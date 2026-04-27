import pytest
from src.tax_classifier import TaxClassifier


def test_loads_categories():
    classifier = TaxClassifier("tax_rate_by_category.csv")
    assert len(classifier.categories) > 0


def test_get_rate_returns_float():
    classifier = TaxClassifier("tax_rate_by_category.csv")
    category = next(iter(classifier.categories))
    rate = classifier.get_rate(category)
    assert isinstance(rate, float)
    assert rate >= 0


def test_get_rate_unknown_raises():
    classifier = TaxClassifier("tax_rate_by_category.csv")
    with pytest.raises(ValueError):
        classifier.get_rate("Nonexistent Category XYZ")


def test_get_categories_text():
    classifier = TaxClassifier("tax_rate_by_category.csv")
    text = classifier.get_categories()
    assert isinstance(text, str)
    assert len(text) > 0


def test_all_rates_non_negative():
    classifier = TaxClassifier("tax_rate_by_category.csv")
    for category, rate in classifier.categories.items():
        assert rate >= 0, f"{category} has negative rate: {rate}"
