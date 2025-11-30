ANSWER_TEMPLATE = """
You are a helpful developer assistant. Answer the question based on the provided code context.

Question: {question}

Context Snippets:
{context_str}

Graph Context (Call Flow):
{graph_context}

Instructions:
1. Summarize the relevant components.
2. Explain the call flow if applicable.
3. Identify potential hotspots or important logic.
4. Be concise.

Answer in JSON format with keys: component_summary, call_flow, hotspots.
"""

FALLBACK_TEMPLATE = """
**Component Summary**:
Based on the retrieved code, the relevant components are:
{summaries}

**Call Flow**:
Potential interactions based on function names:
{connections}

**Hotspots**:
Key logic appears to be in:
{hotspots}
"""
