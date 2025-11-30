from .data_loader import DataLoader
from .utils import process_data

def main():
    """Main entry point."""
    loader = DataLoader("data.csv")
    data = loader.load()
    processed = process_data(data)
    print(f"Processed {len(processed)} items")

if __name__ == "__main__":
    main()
