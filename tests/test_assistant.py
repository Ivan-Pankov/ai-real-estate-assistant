import json
from pathlib import Path

from assistant import recommend_properties, search_properties


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "properties.json"


def load_properties():
    with DATA_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def test_search_by_city():
    properties = load_properties()

    results, criteria = search_properties(
        properties,
        "Дом в Майами"
    )

    assert criteria["city"] == "miami"
    assert results
    assert all(item["city"] == "Miami" for item in results)


def test_search_by_property_type():
    properties = load_properties()

    results, criteria = search_properties(
        properties,
        "Дом в Майами до $500,000"
    )

    assert criteria["property_type"] == "house"
    assert all(item["type"] == "house" for item in results)


def test_search_respects_budget():
    properties = load_properties()

    results, criteria = search_properties(
        properties,
        "Недвижимость до $400,000"
    )

    assert criteria["max_price"] == 400000
    assert all(item["price"] <= 400000 for item in results)


def test_search_respects_minimum_bedrooms():
    properties = load_properties()

    results, criteria = search_properties(
        properties,
        "Дом с 3 спальнями"
    )

    assert criteria["bedrooms"] == 3
    assert all(item["bedrooms"] >= 3 for item in results)


def test_recommendations_respect_budget_and_bedrooms():
    properties = load_properties()

    results = recommend_properties(
        properties,
        budget=500000,
        min_bedrooms=3,
    )

    assert results
    assert len(results) <= 3
    assert all(item["price"] <= 500000 for item in results)
    assert all(item["bedrooms"] >= 3 for item in results)


def test_recommendations_return_empty_when_no_match():
    properties = load_properties()

    results = recommend_properties(
        properties,
        budget=100000,
        min_bedrooms=5,
    )

    assert results == []
