class DataLoader:
    """Handles loading data from files."""
    def __init__(self, source: str):
        self.source = source

    def load(self):
        """Simulate loading data."""
        print(f"Loading from {self.source}")
        return ["item1", "item2", "item3"]
