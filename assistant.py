import re
from typing import Any


CITY_ALIASES = {
    "miami": ["miami", "майами"],
    "austin": ["austin", "остин"],
    "san francisco": ["san francisco", "сан франциско", "сан-франциско"],
}

STATE_ALIASES = {
    "Florida": ["florida", "флорида", "fl"],
    "Texas": ["texas", "техас", "tx"],
    "California": ["california", "калифорния", "ca"],
}

TYPE_ALIASES = {
    "house": ["house", "дом", "дома"],
    "apartment": ["apartment", "квартира", "квартиры", "квартиру", "квартирой", "condo", "condos"],
}


def normalize_text(text: str) -> str:
    """Normalize text for matching."""
    return re.sub(r"\s+", " ", text.lower().strip())


def extract_budget(query: str) -> tuple[int | None, int | None]:
    """Extract price limits without mistaking bedroom counts for prices."""
    text = normalize_text(query)

    pattern = (
        r"(\d[\d\s,]*(?:\.\d+)?)\s*"
        r"(k|m|тыс\.?|тысяч(?:а|и)?|млн\.?|миллион(?:а)?)?"
    )

    matches = list(re.finditer(pattern, text))
    tokens = []

    for match in matches:
        value = match.group(1).replace(",", "").replace(" ", "")
        suffix = (match.group(2) or "").lower()

        # Ignore numbers describing bedrooms.
        following = text[match.end():match.end() + 20]
        if re.match(r"\s*(?:bedrooms?|beds?|спальн)", following):
            continue

        try:
            number = float(value)
        except ValueError:
            continue

        multiplier = 1
        if suffix in ("k", "тыс", "тыс.", "тысяч", "тысяча", "тысячи"):
            multiplier = 1_000
        elif suffix in ("m", "млн", "млн.", "миллион", "миллиона"):
            multiplier = 1_000_000

        before = text[max(0, match.start() - 8):match.start()]
        has_currency = "$" in before or "usd" in before

        tokens.append({
            "value": int(number * multiplier),
            "explicit": bool(suffix) or has_currency,
            "suffix": bool(suffix),
            "start": match.start(),
            "end": match.end(),
        })

    if not tokens:
        return None, None

    # Support ranges such as: от 300 до 450 тысяч.
    if len(tokens) >= 2:
        first, last = tokens[0], tokens[-1]
        between = text[first["end"]:last["start"]]
        prefix = text[:first["start"]]

        if (
            last["suffix"]
            and re.search(r"\b(?:от|from)\b", prefix)
            and re.search(r"\b(?:до|to)\b", between)
        ):
            multiplier = last["value"] // int(
                float(re.sub(r"[^\d.]", "", text[last["start"]:last["end"]].split()[0]))
                or 1
            ) if False else 1

            raw_suffix = re.search(pattern, text[last["start"]:last["end"]])
            suffix = raw_suffix.group(2).lower() if raw_suffix and raw_suffix.group(2) else ""

            if suffix in ("k", "тыс", "тыс.", "тысяч", "тысяча", "тысячи"):
                first_value = int(float(re.sub(r"[^\d.]", "", text[first["start"]:first["end"]])) * 1000)
            elif suffix in ("m", "млн", "млн.", "миллион", "миллиона"):
                first_value = int(float(re.sub(r"[^\d.]", "", text[first["start"]:first["end"]])) * 1_000_000)
            else:
                first_value = first["value"]

            return first_value, last["value"]

    explicit_tokens = [token for token in tokens if token["explicit"]]

    if not explicit_tokens:
        return None, None

    if len(explicit_tokens) >= 2:
        return explicit_tokens[0]["value"], explicit_tokens[-1]["value"]

    amount = explicit_tokens[0]["value"]
    before = text[:explicit_tokens[0]["start"]]

    if any(word in before for word in ("от ", "from ", "выше ")):
        return amount, None

    return None, amount

def parse_search_request(query: str) -> dict[str, Any]:
    """Extract property search criteria from Russian or English text."""
    text = normalize_text(query)

    criteria: dict[str, Any] = {
        "city": None,
        "state": None,
        "property_type": None,
        "min_price": None,
        "max_price": None,
        "bedrooms": None,
    }

    for city, aliases in CITY_ALIASES.items():
        if any(alias in text for alias in aliases):
            criteria["city"] = city
            break

    for state, aliases in STATE_ALIASES.items():
        if any(alias in text for alias in aliases):
            criteria["state"] = state
            break

    for property_type, aliases in TYPE_ALIASES.items():
        if any(alias in text for alias in aliases):
            criteria["property_type"] = property_type
            break

    min_price, max_price = extract_budget(text)
    criteria["min_price"] = min_price
    criteria["max_price"] = max_price

    bedroom_match = re.search(
        r"(\d+)\s*(?:bedrooms?|beds?|спальн\w*)",
        text
    )
    if bedroom_match:
        criteria["bedrooms"] = int(bedroom_match.group(1))

    return criteria


def search_properties(
    properties: list[dict[str, Any]],
    query: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Filter properties using parsed natural-language criteria."""
    criteria = parse_search_request(query)
    results = []

    for property_item in properties:
        if criteria["city"] and property_item.get("city", "").lower() != criteria["city"]:
            continue

        if criteria["state"] and property_item.get("state", "").lower() != criteria["state"].lower():
            continue

        if criteria["property_type"] and property_item.get("type") != criteria["property_type"]:
            continue

        price = property_item.get("price", 0)

        if criteria["min_price"] is not None and price < criteria["min_price"]:
            continue

        if criteria["max_price"] is not None and price > criteria["max_price"]:
            continue

        if criteria["bedrooms"] is not None:
            if property_item.get("bedrooms", 0) < criteria["bedrooms"]:
                continue

        results.append(property_item)

    return results, criteria


def describe_criteria(criteria: dict[str, Any]) -> list[str]:
    """Return human-readable descriptions of recognized criteria."""
    labels = []

    if criteria["city"]:
        labels.append(f"Город: {criteria['city']}")

    if criteria["state"]:
        labels.append(f"Штат: {criteria['state']}")

    if criteria["property_type"]:
        labels.append(
            "Тип: " + (
                "дом" if criteria["property_type"] == "house" else "квартира"
            )
        )

    if criteria["min_price"] is not None:
        labels.append(f"Цена от: ${criteria['min_price']:,}")

    if criteria["max_price"] is not None:
        labels.append(f"Цена до: ${criteria['max_price']:,}")

    if criteria["bedrooms"] is not None:
        labels.append(f"Спален: от {criteria['bedrooms']}")

    return labels

def recommend_properties(
    properties: list[dict[str, Any]],
    budget: int | None = None,
    min_bedrooms: int | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Rank properties using budget, area, bedrooms and remaining budget."""

    candidates = [
        item for item in properties
        if (budget is None or item.get("price", 0) <= budget)
        and (
            min_bedrooms is None
            or item.get("bedrooms", 0) >= min_bedrooms
        )
    ]

    if not candidates:
        return []

    max_area = max(item.get("area_m2", 0) for item in candidates) or 1
    max_bedrooms = max(item.get("bedrooms", 0) for item in candidates) or 1

    ranked = []

    for item in candidates:
        area_score = item.get("area_m2", 0) / max_area
        bedroom_score = item.get("bedrooms", 0) / max_bedrooms

        if budget:
            savings_score = (budget - item["price"]) / budget
        else:
            savings_score = 0

        score = (
            area_score * 0.40
            + bedroom_score * 0.35
            + savings_score * 0.25
        )

        ranked.append((score, item))

    ranked.sort(key=lambda pair: pair[0], reverse=True)

    return [item for score, item in ranked[:limit]]


