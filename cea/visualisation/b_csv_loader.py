import pandas as pd

class CSVLoader:
    """Loads CSV data dynamically."""

    def __init__(self, file_path):
        self.file_path = file_path

    def load_data(self):
        """Reads CSV and returns a Pandas DataFrame."""
        try:
            df = pd.read_csv(self.file_path)
            return df
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return None
