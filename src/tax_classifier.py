import csv
from pathlib import Path


class TaxClassifier:
    def __init__(self, csv_path: str= "tax_rates.csv"):
        self.categories = {}
        self._load_from_csv(csv_path)
    
    # The _load_from_csv method reads tax categories and their corresponding tax rates from a CSV file.
    # ref: https://docs.python.org/3/library/csv.html 
    def _load_from_csv(self, csv_path: str) -> None:
        path = Path(csv_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Tax rates CSV not found: {csv_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('Category') or not row.get('Tax Rate (%)'):
                    continue

                category_name = row['Category'].strip()
                try:
                    tax_rate = float(row['Tax Rate (%)']) / 100
                    self.categories[category_name] = tax_rate
                except ValueError:
                    pass
    
    # The get_rate method retrieves the tax rate for a given category. If the category is not found, it returns a default tax rate of categpory not found, needs manual attention.
    # Will be used for llm tool call to get the tax rate for a line item based on its classified category.
    def get_rate(self, category: str) -> float:
        if category not in self.categories:
            raise ValueError(f"Category '{category}' not found. Manual review needed.")
        return self.categories[category]
    
    # The get_categories method generates a string listing all tax categories and their rates.
    # Will be used by llm tool call to provide context on available tax categories and rates when classifying line items.
    def get_categories(self) -> str:
        lines = []
        for i, (category, rate) in enumerate(self.categories.items()):
            percentage = rate * 100
            lines.append(f"{i}. {category}: {percentage}%")
        return "\n".join(lines)