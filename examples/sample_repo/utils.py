def process_data(items: list):
    """Clean and transform items."""
    result = []
    for item in items:
        result.append(item.upper())
    return result

def validate(item):
    return True
