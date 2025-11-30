import networkx as nx
from typing import List, Dict, Any, Set
from .utils import logger

class GraphBuilder:
    def __init__(self, units: List[Dict[str, Any]]):
        self.units = units
        self.graph = nx.DiGraph()
        self.unit_map = {u['id']: u for u in units}

    def build(self):
        logger.info("Building dependency graph...")
        
        # Add nodes
        for unit in self.units:
            self.graph.add_node(unit['id'], **unit)
            
        # Add edges based on calls
        # Heuristic: if unit A calls 'foo', and unit B is named 'foo' or ends with '.foo', add edge
        # This is naive but works for the demo
        
        name_to_ids = {}
        for u in self.units:
            name = u['name'].split('.')[-1] # Simple name
            if name not in name_to_ids:
                name_to_ids[name] = []
            name_to_ids[name].append(u['id'])
            
        for unit in self.units:
            for call in unit.get('calls', []):
                # Try to find target
                targets = name_to_ids.get(call, [])
                for target_id in targets:
                    # Avoid self-loops if desired, or keep them
                    if target_id != unit['id']:
                        self.graph.add_edge(unit['id'], target_id, type='call')
                        
        logger.info(f"Graph built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        return self.graph

    def find_call_path(self, start_id: str, end_id: str) -> List[str]:
        try:
            return nx.shortest_path(self.graph, start_id, end_id)
        except nx.NetworkXNoPath:
            return []
        except nx.NodeNotFound:
            return []

    def get_context_neighbors(self, unit_ids: List[str], depth: int = 1) -> List[Dict[str, Any]]:
        """Get neighbors of the given units to provide context."""
        relevant_ids = set(unit_ids)
        for uid in unit_ids:
            if uid in self.graph:
                # Add successors (callees) and predecessors (callers)
                relevant_ids.update(self.graph.successors(uid))
                relevant_ids.update(self.graph.predecessors(uid))
        
        return [self.unit_map[uid] for uid in relevant_ids if uid in self.unit_map]
