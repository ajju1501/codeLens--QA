from typing import Dict, Any, List
from .utils import load_json, logger
from .graph_builder import GraphBuilder
from .retriever import Retriever
from .llm import LLMClient

class QueryPipeline:
    def __init__(self, index_data: List[Dict[str, Any]]):
        self.units = index_data
        self.unit_map = {u['id']: u for u in self.units}
        
        # Initialize components
        self.graph_builder = GraphBuilder(self.units)
        self.graph = self.graph_builder.build()
        
        self.retriever = Retriever()
        self.retriever.index_units(self.units)
        
        self.llm = LLMClient()

    def run(self, question: str, k: int = 5) -> Dict[str, Any]:
        logger.info(f"Processing query: {question}")
        
        # 1. Retrieve relevant units
        top_hits = self.retriever.query_top_k(question, k=k)
        top_unit_ids = [h[0] for h in top_hits]
        top_units = [self.unit_map[uid] for uid in top_unit_ids]
        
        logger.info(f"Retrieved {len(top_units)} relevant units")
        
        # 2. Get Graph Context (neighbors of top units)
        # We want to see what these units call or are called by
        context_units = self.graph_builder.get_context_neighbors(top_unit_ids)
        # Merge with top units
        all_context_ids = set(top_unit_ids) | {u['id'] for u in context_units}
        final_context_units = [self.unit_map[uid] for uid in all_context_ids]
        
        # 3. Build Graph Context String (edges)
        graph_edges = []
        subgraph = self.graph.subgraph(all_context_ids)
        for u, v, data in subgraph.edges(data=True):
            graph_edges.append(f"{u} -> {v} ({data.get('type', 'rel')})")
            
        # 4. Generate Answer
        answer = self.llm.generate_answer(question, final_context_units, graph_edges)
        
        # 5. Attach sources
        answer['sources'] = top_unit_ids
        
        return answer
