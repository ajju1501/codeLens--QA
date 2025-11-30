"""
llm.py

A simplified, API-focused LLM client for CodeLens QA.
Supports:
1. Hugging Face API (Serverless Inference) - Free & Fast
2. OpenAI API - Paid & Powerful
3. Offline Mode - Free, Private, Deterministic (Fallback)

No heavy local models or huge downloads required.
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from .prompt_templates import ANSWER_TEMPLATE
from .utils import logger

class LLMClient:
    def __init__(self):
        # Determine provider: "huggingface", "openai", or "none"
        self.provider = os.environ.get("LLM_PROVIDER", "none").lower()
        
        # --- Hugging Face Config ---
        self.hf_token = os.environ.get("HUGGINGFACE_API_KEY") or os.environ.get("HF_TOKEN")
        self.hf_model = os.environ.get("HUGGINGFACE_MODEL", "HuggingFaceH4/zephyr-7b-beta")
        self.hf_client = None
        
        # --- OpenAI Config ---
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.openai_model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")

        # Initialize Provider
        if self.provider == "huggingface":
            if not self.hf_token:
                logger.warning("HUGGINGFACE_API_KEY not set. Switching to offline mode.")
                self.provider = "none"
            else:
                self._init_huggingface()
                
        elif self.provider == "openai":
            if not self.openai_api_key:
                logger.warning("OPENAI_API_KEY not set. Switching to offline mode.")
                self.provider = "none"
            else:
                logger.info(f"Using OpenAI API with model: {self.openai_model}")
                
        else:
            logger.info("Using offline analysis mode (fast & private).")
            self.provider = "none"

    def _init_huggingface(self):
        """Initialize Hugging Face client with fallback to raw HTTP."""
        try:
            from huggingface_hub import InferenceClient
            self.hf_client = InferenceClient(token=self.hf_token)
            logger.info(f"Hugging Face API ready. Model: {self.hf_model}")
        except ImportError:
            logger.warning("huggingface_hub not installed. Using raw HTTP requests.")
            self.hf_client = None
        except Exception as e:
            logger.warning(f"Failed to init HF client: {e}. Will use raw HTTP.")
            self.hf_client = None

    def generate_answer(self, question: str, context_units: List[Dict[str, Any]], graph_context: List[str]) -> Dict[str, Any]:
        """Generate an answer using the configured provider."""
        
        # Prepare context
        context_str = ""
        for u in context_units:
            context_str += f"--- {u.get('id', '?')} ---\n{u.get('code', '')[:500]}...\n\n"
        graph_str = "\n".join(graph_context)

        # Route to provider
        if self.provider == "huggingface":
            return self._call_huggingface(question, context_str, graph_str, context_units, graph_context)
        elif self.provider == "openai":
            return self._call_openai(question, context_str, graph_str, context_units, graph_context)
        else:
            return self._fallback_logic(question, context_units, graph_context)

    # -------------------------------------------------------------------------
    # Hugging Face Implementation
    # -------------------------------------------------------------------------
    def _call_huggingface(self, question: str, context_str: str, graph_str: str, 
                          context_units: List[Dict[str, Any]], graph_context: List[str]) -> Dict[str, Any]:
        
        system_prompt = "You are a code analysis assistant. Analyze code and provide clear, structured answers."
        user_prompt = (f"Question: {question}\n\n"
                       f"Code Context:\n{context_str[:1500]}\n\n"
                       f"Call Graph:\n{graph_str[:400]}\n\n"
                       "Provide a structured answer with:\n1. Component Summary\n2. Call Flow\n3. Key Points\n\nBe concise.")

        generated_text = ""

        # 1. Try InferenceClient (if available)
        if self.hf_client:
            try:
                # Try chat completion first
                if hasattr(self.hf_client, "chat_completion"):
                    resp = self.hf_client.chat_completion(
                        messages=[{"role": "system", "content": system_prompt}, 
                                  {"role": "user", "content": user_prompt}],
                        model=self.hf_model, max_tokens=500, temperature=0.3
                    )
                    generated_text = resp.choices[0].message.content
                # Fallback to text generation
                else:
                    resp = self.hf_client.text_generation(
                        f"{system_prompt}\n\n{user_prompt}", 
                        model=self.hf_model, max_new_tokens=500, temperature=0.3
                    )
                    generated_text = resp
            except Exception as e:
                logger.warning(f"HF Client failed: {e}. Trying raw HTTP...")

        # 2. Try Raw HTTP (Router) if client failed or not available
        if not generated_text:
            try:
                api_url = f"https://api-inference.huggingface.co/models/{self.hf_model}/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.hf_token}"}
                payload = {
                    "model": self.hf_model,
                    "messages": [{"role": "system", "content": system_prompt}, 
                                 {"role": "user", "content": user_prompt}],
                    "max_tokens": 500, "temperature": 0.3
                }
                response = requests.post(api_url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    generated_text = response.json()['choices'][0]['message']['content']
                else:
                    logger.error(f"HF API Error: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"HF Raw HTTP failed: {e}")

        if generated_text:
            return self._structure_response(generated_text, context_units, graph_context, f"Hugging Face ({self.hf_model})")
        
        return self._fallback_logic(question, context_units, graph_context)

    # -------------------------------------------------------------------------
    # OpenAI Implementation
    # -------------------------------------------------------------------------
    def _call_openai(self, question: str, context_str: str, graph_str: str,
                     context_units: List[Dict[str, Any]], graph_context: List[str]) -> Dict[str, Any]:
        try:
            import openai
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            prompt = ANSWER_TEMPLATE.format(question=question, context_str=context_str, graph_context=graph_str)
            
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "system", "content": "You are a coding assistant. Output valid JSON."},
                          {"role": "user", "content": prompt}],
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            # Try to parse JSON
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                parsed = json.loads(content)
                parsed["provider"] = "OpenAI"
                return parsed
            except json.JSONDecodeError:
                return self._structure_response(content, context_units, graph_context, "OpenAI")
                
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            return self._fallback_logic(question, context_units, graph_context)

    # -------------------------------------------------------------------------
    # Utilities & Fallback
    # -------------------------------------------------------------------------
    def _structure_response(self, text: str, units: List[Dict[str, Any]], graph: List[str], provider: str) -> Dict[str, Any]:
        """Parse unstructured text into our UI format."""
        return {
            "component_summary": self._extract_section(text, "Component Summary", "Call Flow") or text[:500],
            "call_flow": self._extract_section(text, "Call Flow", "Key Points") or "\n".join(graph[:5]),
            "hotspots": self._extract_section(text, "Key Points", None) or "See analysis above.",
            "sources": [u.get('id', '?') for u in units],
            "ai_analysis": text,
            "provider": provider
        }

    def _extract_section(self, text: str, start: str, end: Optional[str]) -> str:
        try:
            text_lower = text.lower()
            s_idx = text_lower.find(start.lower())
            if s_idx == -1: return ""
            # Move past header
            s_idx += len(start)
            if text[s_idx] == ':': s_idx += 1
            
            if end:
                e_idx = text_lower.find(end.lower(), s_idx)
                if e_idx != -1: return text[s_idx:e_idx].strip()
            return text[s_idx:s_idx+500].strip()
        except: return ""

    def _fallback_logic(self, question: str, units: List[Dict[str, Any]], graph_context: List[str]) -> Dict[str, Any]:
        """Fast, deterministic offline analysis."""
        if not units:
            return {"component_summary": "No code found.", "provider": "Offline Analysis"}
            
        # 1. Summaries
        summaries = []
        for u in units[:5]:
            code_preview = u.get('code', '')[:100].replace('\n', ' ')
            summaries.append(f"• **{u.get('name')}** ({u.get('kind')})\n  └─ Code: `{code_preview}...`")
            
        # 2. Hotspots (simple heuristic)
        hotspots = []
        for u in units:
            if 'main' in u.get('name', '').lower(): hotspots.append(f"• {u.get('name')} (Entry Point)")
            elif len(u.get('calls', [])) > 2: hotspots.append(f"• {u.get('name')} (Hub)")
            
        return {
            "component_summary": "\n\n".join(summaries),
            "call_flow": "**🔄 Call Flow**:\n" + ("\n".join(graph_context[:5]) if graph_context else "No calls detected."),
            "hotspots": "**🎯 Key Components**:\n" + ("\n".join(hotspots[:5]) if hotspots else "None detected."),
            "sources": [u.get('id') for u in units],
            "note": "✨ Offline analysis - fast & private!",
            "provider": "Offline Analysis (Enhanced)"
        }
