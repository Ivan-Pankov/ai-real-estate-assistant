import json
from typing import Any

from assistant import search_properties, recommend_properties


MAX_RESULTS = 5

# Tools available to the OpenAI model.
TOOLS = [
    {
        "type": "function",
        "name": "search_properties",
        "description": (
            "Search the local demonstration property catalogue "
            "by location, property type, budget, and bedrooms. "
            "Use this tool when the user asks to find properties."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The user's property search request, "
                        "including location and preferences."
                    ),
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "recommend_properties",
        "description": (
            "Rank properties from the local catalogue. "
            "Use this tool when the user asks for recommendations "
            "or wants to compare suitable options."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "budget": {
                    "type": ["integer", "null"],
                    "description": "Maximum budget in USD, or null if unknown.",
                },
                "min_bedrooms": {
                    "type": ["integer", "null"],
                    "description": "Minimum number of bedrooms, or null if unknown.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of recommendations, from 1 to 3.",
                },
            },
            "required": ["budget", "min_bedrooms", "limit"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


def _format_property(item: dict[str, Any]) -> dict[str, Any]:
    """Return only fields needed by the AI assistant."""

    allowed_fields = (
        "id",
        "type",
        "country",
        "state",
        "city",
        "district",
        "price",
        "currency",
        "rooms",
        "area_m2",
        "bedrooms",
        "bathrooms",
        "description",
    )

    return {
        key: item[key]
        for key in allowed_fields
        if key in item
    }


def execute_tool(
    name: str,
    arguments: dict[str, Any],
    properties: list[dict[str, Any]],
) -> str:
    """Execute an allowlisted tool and return JSON output."""

    try:
        if name == "search_properties":
            query = arguments.get("query")

            if not isinstance(query, str) or not query.strip():
                raise ValueError("A non-empty search query is required.")

            if len(query) > 500:
                raise ValueError("The search query is too long.")

            results, criteria = search_properties(
                properties,
                query.strip(),
            )

            output = {
                "criteria": criteria,
                "count": len(results),
                "results": [
                    _format_property(item)
                    for item in results[:MAX_RESULTS]
                ],
            }

        elif name == "recommend_properties":
            budget = arguments.get("budget")
            min_bedrooms = arguments.get("min_bedrooms")
            limit = arguments.get("limit")

            if budget is not None and (
                not isinstance(budget, int)
                or isinstance(budget, bool)
                or budget <= 0
            ):
                raise ValueError("Budget must be a positive integer or null.")

            if min_bedrooms is not None and (
                not isinstance(min_bedrooms, int)
                or isinstance(min_bedrooms, bool)
                or min_bedrooms < 0
            ):
                raise ValueError("Minimum bedrooms must be a non-negative integer or null.")

            if (
                not isinstance(limit, int)
                or isinstance(limit, bool)
                or not 1 <= limit <= 3
            ):
                raise ValueError("Limit must be an integer between 1 and 3.")

            results = recommend_properties(
                properties,
                budget=budget,
                min_bedrooms=min_bedrooms,
                limit=limit,
            )

            output = {
                "count": len(results),
                "results": [
                    _format_property(item)
                    for item in results
                ],
            }

        else:
            raise ValueError(f"Unknown tool: {name}")

        return json.dumps(output, ensure_ascii=False)

    except (ValueError, TypeError) as error:
        return json.dumps(
            {"error": str(error)},
            ensure_ascii=False,
        )
