import json
import re
from pathlib import Path

import requests
import streamlit as st

from assistant import (
    search_properties,
    describe_criteria,
    recommend_properties,
)

from ai_client import generate_ai_response



st.set_page_config(
    page_title="AI Real Estate Assistant | USA",
    page_icon="🏡",
    layout="wide"
)


# LANGUAGE SELECTOR
if "language" not in st.session_state:
    st.session_state.language = "ru"

lang_ru, lang_en, _ = st.columns([1, 1, 8])

if lang_ru.button("RU", type="primary" if st.session_state.language == "ru" else "secondary", key="language_ru"):
    st.session_state.language = "ru"
    st.rerun()

if lang_en.button("EN", type="primary" if st.session_state.language == "en" else "secondary", key="language_en"):
    st.session_state.language = "en"
    st.rerun()

LANG = st.session_state.language


# UI TRANSLATIONS
TRANSLATIONS = {
    "ru": {
        "title": "🏡 AI-помощник по недвижимости США",
        "subtitle": "Подбор домов и квартир в США",
        "demo_notice": "Демонстрационная версия. Объекты, цены и фотографии условные. Это не актуальные объявления о продаже.",
        "natural_search": "🔎 Поиск на естественном языке",
        "search_label": "Опишите, какую недвижимость вы ищете",
        "search_placeholder": "Например: Дом в Майами до 500 тысяч долларов с 3 спальнями",
        "filters": "Дополнительные фильтры",
        "state": "Штат",
        "all_states": "Все штаты",
        "city": "Город",
        "all_cities": "Все города",
        "property_type": "Тип недвижимости",
        "any_type": "Любой тип",
        "house": "Дом",
        "apartment": "Квартира",
        "budget": "Бюджет (USD)",
        "bedrooms": "Спальни",
        "any_bedrooms": "Любое количество",
        "favorites_only": "❤️ Только избранное",
        "reset_filters": "Сбросить фильтры",
        "clear_favorites": "Очистить избранное",
        "sorting": "Сортировка",
        "cheapest": "Сначала дешевле",
        "expensive": "Сначала дороже",
        "largest": "Больше площадь",
        "found": "Найдено объектов",
        "in_favorites": "В избранном",
        "average_price": "Средняя цена",
        "average_area": "Средняя площадь",
        "results": "🏘️ Результаты поиска",
        "no_results": "По заданным параметрам ничего не найдено.",
        "bathrooms": "Ванные",
        "rooms": "Комнаты",
        "area": "Площадь",
        "remove_favorite": "❤️ Убрать из избранного",
        "add_favorite": "🤍 В избранное",
        "ask_emily": "💬 Спросить Emily",
        "details": "Подробнее",
        "comparison": "⚖️ Сравнение недвижимости",
        "comparison_help": "Выберите два объекта, чтобы Emily сравнила их характеристики и помогла оценить различия.",
        "first_property": "Первый объект",
        "second_property": "Второй объект",
        "different_properties": "Выберите два разных объекта для сравнения.",
        "characteristics": "Характеристики объектов",
        "parameter": "Параметр",
        "infrastructure": "📍 Инфраструктура и окружение",
        "infrastructure_note": "Emily показывает объекты, отмеченные в OpenStreetMap в радиусе 3 км от географического центра района. Это ориентир района, а не точка конкретного дома: демонстрационный каталог не содержит адресов и координат.",
        "studying": "Emily изучает инфраструктуру района...",
        "osm_error": "Не удалось получить данные OpenStreetMap. Попробуйте обновить страницу позже.",
        "geo_error": "Не удалось обработать географические данные района.",
        "city_center": "До центра города по прямой",
        "distance_unavailable": "Расстояние до центра города пока недоступно.",
        "no_infrastructure": "В OpenStreetMap пока не найдены отмеченные объекты инфраструктуры в радиусе 3 км.",
        "source": "Источник: OpenStreetMap. Расстояния рассчитаны по прямой от центра района; фактический маршрут может быть длиннее.",
        "need_two": "Для сравнения необходимо минимум два объекта.",
        "greeting": "Привет! Я Emily, ваш виртуальный консультант",
        "intro": "Помогу разобраться с объектами, сравнить варианты и подобрать недвижимость в США.",
        "ai_demo": "🟢 AI-консультант · Демонстрационный режим",
        "chat": "💬 Чат с Emily",
        "chat_placeholder": "Напишите Emily...",
        "clear_chat": "🗑️ Очистить переписку",
        "chat_greeting": "Чем могу помочь с подбором недвижимости?",
        "recommendations": "🏆 Рекомендации Emily",
        "top_choice": "🥇 Первый выбор Emily",
        "alternative": "🥈 Альтернатива",
        "remaining_budget": "💰 Остаток бюджета",
        "suitable_properties": "Подходящих объектов",
        "shown_recommendations": "Показано рекомендаций",
        "found_properties": "Найдено объектов",
        "emily_about": "Emily о выбранном объекте",
        "property": "Объект",
        "type": "Тип",
        "district": "Район",
        "price": "Цена",
        "total_rooms": "Всего комнат",
        "important": "Что важно знать:",
        "demo_answer": "Ответ сформирован по демонстрационным данным каталога.",
        "recognized_search": "Что понял поисковый помощник",
        "unrecognized": "Параметры поиска не распознаны. Поиск по тексту.",
        "footer": "AI Real Estate Assistant | USA | Portfolio Demo | Illustrative Data",
        "education": "Образование",
        "shopping": "Торговля",
        "healthcare": "Медицина",
        "parks": "Парки и отдых",
        "nature": "Природа и водоёмы",
        "transport": "Транспорт",
    },
    "en": {
        "title": "🏡 AI Real Estate Assistant USA",
        "subtitle": "Find houses and apartments across the United States",
        "demo_notice": "Demo version. Properties, prices, and photos are illustrative. These are not active listings for sale.",
        "natural_search": "🔎 Natural Language Search",
        "search_label": "Describe the property you are looking for",
        "search_placeholder": "For example: 3-bedroom house in Miami under $500,000",
        "filters": "Additional Filters",
        "state": "State",
        "all_states": "All states",
        "city": "City",
        "all_cities": "All cities",
        "property_type": "Property Type",
        "any_type": "Any type",
        "house": "House",
        "apartment": "Apartment / Condo",
        "budget": "Budget (USD)",
        "bedrooms": "Bedrooms",
        "any_bedrooms": "Any number",
        "favorites_only": "❤️ Favorites only",
        "reset_filters": "Reset filters",
        "clear_favorites": "Clear favorites",
        "sorting": "Sort by",
        "cheapest": "Price: low to high",
        "expensive": "Price: high to low",
        "largest": "Largest area",
        "found": "Properties found",
        "in_favorites": "Favorites",
        "average_price": "Average price",
        "average_area": "Average area",
        "results": "🏘️ Search Results",
        "no_results": "No properties match your criteria.",
        "bathrooms": "Bathrooms",
        "rooms": "Rooms",
        "area": "Area",
        "remove_favorite": "❤️ Remove from favorites",
        "add_favorite": "🤍 Add to favorites",
        "ask_emily": "💬 Ask Emily",
        "details": "Details",
        "comparison": "⚖️ Property Comparison",
        "comparison_help": "Select two properties and Emily will compare their features and highlight the differences.",
        "first_property": "First property",
        "second_property": "Second property",
        "different_properties": "Please select two different properties to compare.",
        "characteristics": "Property Features",
        "parameter": "Feature",
        "infrastructure": "📍 Neighborhood & Amenities",
        "infrastructure_note": "Emily displays OpenStreetMap places within 3 km of the geographic center of each district. This is a neighborhood reference point, not the location of a specific home: the demo catalog does not contain property addresses or coordinates.",
        "studying": "Emily is exploring the neighborhood...",
        "osm_error": "Could not retrieve OpenStreetMap data. Please try refreshing the page later.",
        "geo_error": "Could not process neighborhood geographic data.",
        "city_center": "Straight-line distance to city center",
        "distance_unavailable": "Distance to the city center is currently unavailable.",
        "no_infrastructure": "No mapped amenities were found in OpenStreetMap within a 3 km radius.",
        "source": "Source: OpenStreetMap. Distances are measured in a straight line from the district center; actual routes may be longer.",
        "need_two": "At least two properties are required for comparison.",
        "greeting": "Hi! I'm Emily, your virtual real estate assistant",
        "intro": "I can help you explore properties, compare options, and find real estate in the United States.",
        "ai_demo": "🟢 AI Assistant · Demo Mode",
        "chat": "💬 Chat with Emily",
        "chat_placeholder": "Message Emily...",
        "clear_chat": "🗑️ Clear conversation",
        "chat_greeting": "How can I help you find a property?",
        "recommendations": "🏆 Emily's Recommendations",
        "top_choice": "🥇 Emily's Top Pick",
        "alternative": "🥈 Alternative",
        "remaining_budget": "💰 Remaining budget",
        "suitable_properties": "Matching properties",
        "shown_recommendations": "Recommendations shown",
        "found_properties": "Properties found",
        "emily_about": "Emily about this property",
        "property": "Property",
        "type": "Type",
        "district": "District",
        "price": "Price",
        "total_rooms": "Total rooms",
        "important": "What you should know:",
        "demo_answer": "This response is based on the illustrative demo catalog.",
        "recognized_search": "What the search assistant understood",
        "unrecognized": "Search criteria were not recognized. Searching by text.",
        "footer": "AI Real Estate Assistant | USA | Portfolio Demo | Illustrative Data",
        "education": "Education",
        "shopping": "Shopping",
        "healthcare": "Healthcare",
        "parks": "Parks & Recreation",
        "nature": "Nature & Water",
        "transport": "Transportation",
    },
}


def t(key):
    """Return a translated UI string."""
    return TRANSLATIONS[LANG].get(key, TRANSLATIONS["ru"].get(key, key))



DATA_PATH = Path(__file__).parent / "data" / "properties.json"


PROPERTY_IMAGES = {
    "MIA-001": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1000",
    "MIA-002": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1000",
    "MIA-003": "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=1000",
    "AUS-001": "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=1000",
    "AUS-002": "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=1000",
    "AUS-003": "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?w=1000",
    "SFO-001": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1000",
    "SFO-002": "https://images.unsplash.com/photo-1600607687644-c7171b42498f?w=1000",
    "SFO-003": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=1000",
}


@st.cache_data(ttl=86400, show_spinner=False)
def geocode_location(query):
    """Resolve a district or city reference point with retry handling."""
    import time

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "jsonv2",
        "limit": 1,
        "countrycodes": "us",
    }
    headers = {"User-Agent": "AIRealEstateAssistantPortfolio/1.0"}
    last_error = None

    # Respect Nominatim's usage policy and retry temporary network failures.
    for attempt in range(3):
        time.sleep(1.1)
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=(10, 25),
            )
            response.raise_for_status()
            results = response.json()
            if not results:
                return None
            return {
                "lat": float(results[0]["lat"]),
                "lon": float(results[0]["lon"]),
            }
        except (requests.RequestException, ValueError, KeyError, TypeError) as error:
            last_error = error
            if attempt < 2:
                time.sleep(2 ** attempt)

    raise requests.RequestException(
        f"Nominatim не ответил после 3 попыток: {last_error}"
    )


def _distance_km(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, asin, sqrt
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    value = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 6371 * 2 * asin(sqrt(value))


@st.cache_data(ttl=86400, show_spinner=False)
def get_neighborhood_info(city, district, state):
    """Fetch nearby mapped amenities around the geocoded district reference point."""
    query = f"{district}, {city}, {state}, USA"
    point = geocode_location(query)
    if not point:
        return {"error": "Не удалось определить координаты района в OpenStreetMap."}

    lat, lon = point["lat"], point["lon"]
    overpass_query = f"""
    [out:json][timeout:25];
    (
      nwr(around:3000,{lat},{lon})["amenity"~"school|kindergarten|college|university|hospital|clinic|doctors|pharmacy|marketplace"];
      nwr(around:3000,{lat},{lon})["shop"~"supermarket|mall|department_store"];
      nwr(around:3000,{lat},{lon})["leisure"~"park|garden"];
      nwr(around:3000,{lat},{lon})["landuse"="forest"];
      nwr(around:3000,{lat},{lon})["natural"~"wood|water"];
      nwr(around:3000,{lat},{lon})["water"="lake"];
      nwr(around:3000,{lat},{lon})["highway"="bus_stop"];
      nwr(around:3000,{lat},{lon})["railway"~"station|tram_stop"];
      nwr(around:3000,{lat},{lon})["public_transport"="platform"];
    );
    out center tags;
    """
    # Public Overpass instances can be busy or temporarily unavailable.
    # Try independent endpoints in sequence instead of relying on one server.
    overpass_endpoints = (
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass-api.de/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
    )
    headers = {
        "User-Agent": "AIRealEstateAssistantPortfolio/1.0",
        "Accept": "application/json",
    }
    elements = None
    endpoint_errors = []

    for endpoint in overpass_endpoints:
        try:
            response = requests.post(
                endpoint,
                data={"data": overpass_query},
                headers=headers,
                timeout=(10, 40),
            )
            response.raise_for_status()
            payload = response.json()
            elements = payload.get("elements", [])
            break
        except (requests.RequestException, ValueError, TypeError) as error:
            endpoint_errors.append(f"{endpoint}: {error}")

    if elements is None:
        details = " | ".join(endpoint_errors)
        raise requests.RequestException(
            "Все резервные серверы Overpass недоступны. " + details
        )

    groups = {
        "Образование": [],
        "Торговля": [],
        "Медицина": [],
        "Парки и отдых": [],
        "Природа и водоёмы": [],
        "Транспорт": [],
    }
    seen = set()
    for item in elements:
        tags = item.get("tags", {})
        name = tags.get("name") or tags.get("name:en") or tags.get("amenity") or tags.get("shop") or tags.get("leisure") or tags.get("natural") or tags.get("highway") or tags.get("railway")
        if not name:
            continue
        coords = item.get("center", item)
        item_lat, item_lon = coords.get("lat"), coords.get("lon")
        if item_lat is None or item_lon is None:
            continue

        amenity, shop = tags.get("amenity"), tags.get("shop")
        leisure, natural = tags.get("leisure"), tags.get("natural")
        if amenity in ("school", "kindergarten", "college", "university"):
            category = "Образование"
        elif shop in ("supermarket", "mall", "department_store") or amenity == "marketplace":
            category = "Торговля"
        elif amenity in ("hospital", "clinic", "doctors", "pharmacy"):
            category = "Медицина"
        elif leisure in ("park", "garden"):
            category = "Парки и отдых"
        elif tags.get("landuse") == "forest" or natural in ("wood", "water") or tags.get("water") == "lake":
            category = "Природа и водоёмы"
        elif tags.get("highway") == "bus_stop" or tags.get("railway") in ("station", "tram_stop") or tags.get("public_transport") == "platform":
            category = "Транспорт"
        else:
            continue

        key = (category, str(name), round(float(item_lat), 5), round(float(item_lon), 5))
        if key in seen:
            continue
        seen.add(key)
        groups[category].append({
            "name": str(name),
            "distance": _distance_km(lat, lon, float(item_lat), float(item_lon)),
        })

    for category in groups:
        groups[category].sort(key=lambda entry: entry["distance"])
        groups[category] = groups[category][:5]

    city_point = geocode_location(f"{city}, {state}, USA")
    center_distance = (
        _distance_km(lat, lon, city_point["lat"], city_point["lon"])
        if city_point else None
    )
    return {
        "groups": groups,
        "center_distance": center_distance,
        "reference": query,
        "radius_km": 3,
    }


@st.cache_data
def load_properties():
    with DATA_PATH.open(encoding="utf-8") as file:
        return json.load(file)


try:
    properties = load_properties()
except Exception as error:
    st.error(f"Ошибка загрузки каталога: {error}")
    st.stop()


if "favorites" not in st.session_state:
    st.session_state.favorites = set()


# CSS
st.markdown("""
<style>
header[data-testid="stHeader"] {
    display: none !important;
}
#MainMenu {
    display: none !important;
}
.stApp {
    background-color: #f5f7fa;
}
.block-container {
    padding-top: 2rem;
    max-width: 1400px;
}
.property-title {
    font-size: 1.25rem;
    font-weight: 700;
    margin-bottom: 0.3rem;
}
.property-price {
    font-size: 1.65rem;
    font-weight: 800;
    color: #176b50;
}
.property-location {
    color: #667085;
    font-size: 0.95rem;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: white;
    border-radius: 14px;
}

/* Unified typography */
html, body, .stApp {
    font-family: Arial, sans-serif !important;
    font-size: 16px !important;
}

.stApp p,
.stApp li,
.stApp label,
.stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stWidgetLabel"],
.stApp [data-testid="stTable"] th,
.stApp [data-testid="stTable"] td,
.stApp input,
.stApp select,
.stApp textarea {
    font-family: Arial, sans-serif !important;
    font-size: 16px !important;
    line-height: 1.45 !important;
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] input {
    font-size: 16px !important;
}

[data-testid="stTable"] th,
[data-testid="stTable"] td {
    font-size: 16px !important;
    padding: 8px 10px !important;
}

.stButton button {
    font-family: Arial, sans-serif !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    min-height: 44px;
}

/* RU / EN language buttons */
div[data-testid="stHorizontalBlock"] button[data-testid="stBaseButton-primary"] {
    color: white !important;
    background-color: #176b50 !important;
    min-height: 44px !important;
    min-width: 64px !important;
}
div[data-testid="stHorizontalBlock"] button[data-testid="stBaseButton-secondary"] {
    color: #176b50 !important;
    background-color: white !important;
    min-height: 44px !important;
    min-width: 64px !important;
}
.stButton button p {
    color: inherit !important;
    font-size: 16px !important;
    line-height: 1.2 !important;
    opacity: 1 !important;
}

[data-testid="stCaptionContainer"] {
    font-size: 15px !important;
}

.stApp h1 { font-size: 28px !important; }
.stApp h2 { font-size: 24px !important; }
.stApp h3 { font-size: 21px !important; }

</style>
""", unsafe_allow_html=True)



def get_emily_response(message, properties, language=None, history=None):
    """Generate a local demo response in the selected language."""
    language = language or LANG
    is_en = language == "en"
    query = message.strip()

    pending_query = st.session_state.get("emily_pending_query")
    if pending_query and query:
        query = f"{pending_query} {query}"
        st.session_state.pop("emily_pending_query", None)

    if not query:
        return (
            "Please describe what kind of property you are looking for."
            if is_en else
            "Напишите, пожалуйста, что именно вы ищете."
        )

    lower_query = query.lower()

    greeting_words = (
        "привет", "здравствуй", "добрый день",
        "hello", "hi", "good morning", "good afternoon"
    )
    if any(word in lower_query for word in greeting_words):
        return (
            "Hello! I'm Emily, your real estate assistant. "
            "I can help you find a house or apartment in Miami, Austin, "
            "or San Francisco. For example: 'A house in Miami under $500,000'."
            if is_en else
            "Здравствуйте! Я Emily. Могу помочь найти дом или квартиру "
            "в Майами, Остине или Сан-Франциско. "
            "Например, напишите: «Дом в Майами до 500 тысяч долларов»."
        )

    # Route general real estate questions to the OpenAI assistant.
    general_question_starters = (
        "как ", "почему ", "что ", "какие ", "какой ", "какая ",
        "объясни ", "расскажи ", "what ", "how ", "why ",
        "which ", "explain ", "tell me ",
    )
    real_estate_topics = (
        "недвижим", "покупк", "первого дома", "ипотек", "страхов",
        "налог", "первоначальн", "первый взнос", "осмотр дома",
        "mortgage", "buying a home", "first home", "real estate",
        "property tax", "closing cost", "down payment",
        "home inspection",
    )
    known_cities = (
        "майами", "остин", "сан-франциско",
        "miami", "austin", "san francisco",
    )
    budget_markers = (
        "$", "€", "доллар", "тысяч", "тыс.", "budget",
        "under ", "below ",
    )

    is_general_question = (
        lower_query.startswith(general_question_starters)
        and any(topic in lower_query for topic in real_estate_topics)
        and not any(city in lower_query for city in known_cities)
        and not any(marker in lower_query for marker in budget_markers)
    )

    if is_general_question:
        return generate_ai_response(
            query,
            history=history,
            language=language,
        )

    results, criteria = search_properties(properties, query)
    recognized = describe_criteria(criteria)

    if is_en:
        translations = {
            "Город:": "City:",
            "Штат:": "State:",
            "Тип:": "Property type:",
            "Цена от:": "Minimum price:",
            "Цена до:": "Maximum price:",
            "Спален:": "Bedrooms:",
        }
        recognized = [
            next(
                (item.replace(old, new, 1)
                 for old, new in translations.items()
                 if item.startswith(old)),
                item
            )
            for item in recognized
        ]

    recommendation_words = (
        "посоветуй", "порекомендуй", "рекомендац",
        "лучше выбрать", "лучший вариант", "самый выгодный",
        "что выбрать", "recommend", "best option", "which one",
        "suggest", "recommendation"
    )
    is_recommendation = any(
        word in lower_query for word in recommendation_words
    )

    if is_recommendation:
        if criteria["max_price"] is None:
            st.session_state.emily_pending_query = query
            return (
                "I'd be happy to help you choose. What is your maximum "
                "purchase budget? For example, $500,000."
                if is_en else
                "С удовольствием помогу выбрать лучший вариант. "
                "Какой максимальный бюджет покупки вы планируете? "
                "Например, $500,000."
            )

        return generate_ai_response(
            query,
            history=history,
            language=language,
            properties=results,
        )

    if criteria["property_type"] and not criteria["city"] and not criteria["state"]:
        st.session_state.emily_pending_query = query
        return (
            "I'd be happy to help! Which city are you interested in: "
            "Miami, Austin, or San Francisco?"
            if is_en else
            "С удовольствием помогу! В каком городе вы ищете "
            "недвижимость: Майами, Остин или Сан-Франциско?"
        )

    if (
        criteria["property_type"]
        and (criteria["city"] or criteria["state"])
        and criteria["min_price"] is None
        and criteria["max_price"] is None
    ):
        st.session_state.emily_pending_query = query
        return (
            "Got it. What is your purchase budget? "
            "For example, under $400,000."
            if is_en else
            "Поняла, какой объект и город вы рассматриваете. "
            "Какой бюджет покупки вы планируете? "
            "Например, до 400 тысяч долларов."
        )

    if recognized:
        return generate_ai_response(
            query,
            history=history,
            language=language,
            properties=results,
        )

    if any(word in lower_query for word in (
        "сравнить", "сравнение", "разница",
        "compare", "comparison", "difference"
    )):
        return (
            "Of course! Open the Property Comparison section below "
            "and select two different properties. The app will show "
            "their comparison and analysis."
            if is_en else
            "Конечно! Откройте раздел «Сравнение недвижимости» ниже "
            "в приложении и выберите два разных объекта. "
            "Я автоматически покажу их сравнение и свой анализ."
        )

    if any(word in lower_query for word in (
        "помощь", "что умеешь", "возможности",
        "help", "what can you do"
    )):
        return (
            "I can search for houses and apartments in Miami, Austin, "
            "and San Francisco, consider your budget and bedroom count, "
            "show property details, and help compare two options. "
            "Try entering a specific request."
            if is_en else
            "Я могу искать дома и квартиры в Майами, Остине и "
            "Сан-Франциско, учитывать бюджет и количество спален, "
            "показывать характеристики объектов и помогать сравнивать "
            "два варианта. Попробуйте задать конкретный запрос."
        )

    return generate_ai_response(
        query,
        history=history,
        language=language,
    )



# EMILY AI ASSISTANT
def set_emily_query(query):
    st.session_state.emily_messages.append(
        {"role": "user", "content": query}
    )

    answer = get_emily_response(
        query, properties, LANG,
        st.session_state.emily_messages[:-1]
    )

    if isinstance(answer, dict):
        st.session_state.emily_messages.append(
            {"role": "assistant", **answer}
        )
    else:
        st.session_state.emily_messages.append(
            {"role": "assistant", "content": answer}
        )


with st.container(border=True):
    emily_photo, emily_text = st.columns(
        [1, 4],
        vertical_alignment="center"
    )

    with emily_photo:
        st.image("assets/emily.png", width=180)

    with emily_text:
        st.markdown(f"## {t('greeting')}")
        st.write(t("intro"))
        st.caption(t("ai_demo"))

        button1, button2, button3 = st.columns(3)

        with button1:
            st.button(
                ("🏡 House in Miami" if LANG == "en" else "🏡 Дом в Майами"),
                key="emily_miami",
                use_container_width=True,
                on_click=set_emily_query,
                args=(("House in Miami under $500,000" if LANG == "en" else "Дом в Майами до 500 тысяч долларов"),)
            )

        with button2:
            st.button(
                ("🏢 Apartment in Austin" if LANG == "en" else "🏢 Квартира в Остине"),
                key="emily_austin",
                use_container_width=True,
                on_click=set_emily_query,
                args=(("Apartment in Austin with 2 bedrooms" if LANG == "en" else "Квартира в Остине с 2 спальнями"),)
            )

        with button3:
            st.button(
                ("🌉 House in San Francisco" if LANG == "en" else "🌉 Дом в Сан-Франциско"),
                key="emily_sf",
                use_container_width=True,
                on_click=set_emily_query,
                args=(("House in San Francisco under $900,000" if LANG == "en" else "Дом в Сан-Франциско до 900 тысяч долларов"),)
            )



# EMILY CHAT
st.divider()
st.subheader(t("chat"))


if "emily_messages" not in st.session_state:
    st.session_state.emily_messages = [
        {
            "role": "assistant",
            "content": t("chat_greeting")
        }
    ]

with st.container(border=True):
    for message in st.session_state.emily_messages:
        with st.chat_message(message["role"]):
            if message.get("kind") in ("property_results", "property_recommendation"):
                is_recommendation = message["kind"] == "property_recommendation"

                if is_recommendation:
                    st.markdown(f"### {t('recommendations')}")

                st.markdown(message["content"])

                tool_name = message.get("tool_name")
                if tool_name:
                    st.caption(f"Function Calling: `{tool_name}`")

                for index, prop in enumerate(message["properties"], start=1):
                    with st.container(border=True):
                        if is_recommendation and index == 1:
                            st.markdown(f"**{t('top_choice')}**")
                        elif is_recommendation:
                            st.markdown(f"**{t('alternative')} {index - 1}**")

                        st.markdown(f"**🏡 {prop['id']}**")
                        st.caption(f"📍 {prop['district']}, {prop['city']}")
                        st.markdown(
                            f"<div style='font-size:25px; font-weight:700; "
                            f"color:#176b50;'>${prop['price']:,}</div>",
                            unsafe_allow_html=True
                        )

                        if is_recommendation:
                            remaining = message["budget"] - prop["price"]
                            st.caption(f"{t('remaining_budget')}: ${remaining:,}")

                        info1, info2, info3 = st.columns(3)
                        info1.metric(t("bedrooms"), prop["bedrooms"])
                        info2.metric(t("area"), f"{prop['area_m2']} m²" if LANG == "en" else f"{prop['area_m2']} м²")
                        info3.metric(t("bathrooms"), prop["bathrooms"])

                if is_recommendation:
                    st.caption(
                        f"{t('suitable_properties')}: {message['total']}. "
                        f"{t('shown_recommendations')}: {len(message['properties'])}."
                    )
                else:
                    st.caption(f"{t('found_properties')}: {message['total']}")
            else:
                st.markdown(message["content"])

    user_message = st.chat_input(
        t("chat_placeholder"),
        key="emily_chat_input"
    )

    if user_message:
        st.session_state.emily_messages.append(
            {"role": "user", "content": user_message}
        )

        answer = get_emily_response(
            user_message, properties, LANG,
            st.session_state.emily_messages[:-1]
        )

        if isinstance(answer, dict):
            st.session_state.emily_messages.append(
                {"role": "assistant", **answer}
            )
        else:
            st.session_state.emily_messages.append(
                {"role": "assistant", "content": answer}
            )

        st.rerun()

if st.button(t("clear_chat"), key="clear_emily_chat"):
    st.session_state.emily_messages = [
        {
            "role": "assistant",
            "content": t("chat_greeting")
        }
    ]
    st.rerun()


# HEADER
st.title(t("title"))
st.caption(t("subtitle"))

st.info(
    t("demo_notice")
)


# NATURAL LANGUAGE SEARCH
st.subheader(t("natural_search"))

natural_query = st.text_input(
    t("search_label"),
    placeholder=t("search_placeholder"),
    key="natural_query"
)

if natural_query.strip():
    filtered, criteria = search_properties(properties, natural_query)
    recognized = describe_criteria(criteria)

    with st.expander(t("recognized_search"), expanded=True):
        if recognized:
            for item in recognized:
                st.write(f"• {item}")
        else:
            st.write(t("unrecognized"))

    if not recognized:
        query = natural_query.lower().strip()
        filtered = [
            p for p in properties
            if query in " ".join(str(v) for v in p.values()).lower()
        ]
else:
    filtered = properties.copy()


# SIDEBAR FILTERS
def reset_filters():
    st.session_state["filter_state"] = "Все штаты"
    st.session_state["filter_city"] = "Все города"
    st.session_state["filter_type"] = "Любой тип"
    st.session_state["filter_price_range"] = (min_price, max_price)
    st.session_state["filter_bedrooms"] = "Любое количество"
    st.session_state["filter_favorites_only"] = False


st.sidebar.header(t("filters"))

states = sorted({p["state"] for p in properties})

min_price = min(p["price"] for p in properties)
max_price = max(p["price"] for p in properties)

selected_state = st.sidebar.selectbox(
    t("state"),
    ["Все штаты"] + states,
    format_func=lambda x: t("all_states") if x == "Все штаты" else str(x),
    key="filter_state"
)

cities = sorted({
    p["city"] for p in properties
    if selected_state == "Все штаты" or p["state"] == selected_state
})

selected_city = st.sidebar.selectbox(
    t("city"),
    ["Все города"] + cities,
    format_func=lambda x: t("all_cities") if x == "Все города" else str(x),
    key="filter_city"
)

type_options = {
    "Дом": "house",
    "Квартира / Condo": "apartment"
}

selected_type = st.sidebar.selectbox(
    t("property_type"),
    ["Любой тип"] + list(type_options.keys()),
    format_func=lambda x: t("any_type") if x == "Любой тип" else t("house") if x == "Дом" else t("apartment"),
    key="filter_type"
)

price_range = st.sidebar.slider(
    t("budget"),
    min_value=min_price,
    max_value=max_price,
    value=(min_price, max_price),
    step=10000,
    format="$%d",
    key="filter_price_range"
)

bedroom_options = sorted({p["bedrooms"] for p in properties})

selected_bedrooms = st.sidebar.selectbox(
    t("bedrooms"),
    ["Любое количество"] + bedroom_options,
    format_func=lambda x: t("any_bedrooms") if x == "Любое количество" else str(x),
    key="filter_bedrooms"
)

st.sidebar.divider()

favorites_only = st.sidebar.checkbox(
    t("favorites_only"),
    key="filter_favorites_only"
)

st.sidebar.button(
    t("reset_filters"),
    use_container_width=True,
    on_click=reset_filters
)

def clear_favorites():
    st.session_state.favorites.clear()

st.sidebar.button(
    t("clear_favorites"),
    use_container_width=True,
    on_click=clear_favorites
)

# APPLY FILTERS
if selected_state != "Все штаты":
    filtered = [p for p in filtered if p["state"] == selected_state]

if selected_city != "Все города":
    filtered = [p for p in filtered if p["city"] == selected_city]

if selected_type != "Любой тип":
    filtered = [
        p for p in filtered
        if p["type"] == type_options[selected_type]
    ]

filtered = [
    p for p in filtered
    if price_range[0] <= p["price"] <= price_range[1]
]

if selected_bedrooms != "Любое количество":
    filtered = [
        p for p in filtered
        if p["bedrooms"] == selected_bedrooms
    ]

if favorites_only:
    filtered = [
        p for p in filtered
        if p["id"] in st.session_state.favorites
    ]


# SORTING
sort_order = st.selectbox(
    "Сортировка",
    ["Сначала дешевле", "Сначала дороже", "Больше площадь"],
    format_func=lambda x: t("cheapest") if x == "Сначала дешевле" else t("expensive") if x == "Сначала дороже" else t("largest")
)

if sort_order == "Сначала дешевле":
    filtered.sort(key=lambda p: p["price"])
elif sort_order == "Сначала дороже":
    filtered.sort(key=lambda p: p["price"], reverse=True)
else:
    filtered.sort(key=lambda p: p["area_m2"], reverse=True)


# SUMMARY
st.divider()

col1, col2, col3, col4 = st.columns(4)

col1.metric(t("found"), len(filtered))
col2.metric(t("in_favorites"), len(st.session_state.favorites))

if filtered:
    average_price = sum(p["price"] for p in filtered) // len(filtered)
    average_area = sum(p["area_m2"] for p in filtered) // len(filtered)

    col3.metric(t("average_price"), f"${average_price:,}")
    col4.metric(t("average_area"), f"{average_area} м²")
else:
    col3.metric(t("average_price"), "—")
    col4.metric(t("average_area"), "—")


# PROPERTY CARDS
st.divider()
st.subheader(t("results"))

if not filtered:
    st.warning(t("no_results"))

for p in filtered:
    property_id = p["id"]
    is_favorite = property_id in st.session_state.favorites

    property_type = (
        t("house") if p["type"] == "house"
        else "Квартира / Condo"
    )

    with st.container(border=True):
        image_col, info_col = st.columns([1.15, 2])

        with image_col:
            image_url = PROPERTY_IMAGES.get(property_id)

            if image_url:
                st.image(image_url, use_container_width=True)
            else:
                st.image(
                    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1000",
                    use_container_width=True
                )

        with info_col:
            st.markdown(
                f'<div class="property-title">{property_type} | {property_id}</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="property-location">📍 {p["city"]}, '
                f'{p["state_code"]} | {p["district"]}</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="property-price">${p["price"]:,}</div>',
                unsafe_allow_html=True
            )

            metric1, metric2, metric3, metric4 = st.columns(4)

            metric1.metric(t("bedrooms"), p["bedrooms"])
            metric2.metric(t("bathrooms"), p["bathrooms"])
            metric3.metric(t("rooms"), p["rooms"])
            metric4.metric(t("area"), f'{p["area_m2"]} м²')

            st.write(p["description"])

            button_col, emily_col, details_col = st.columns(3)

            with button_col:
                favorite_label = (
                    "❤️ Убрать из избранного"
                    if is_favorite
                    else t("add_favorite")
                )

                if st.button(
                    favorite_label,
                    key=f"favorite_{property_id}",
                    use_container_width=True
                ):
                    if is_favorite:
                        st.session_state.favorites.remove(property_id)
                    else:
                        st.session_state.favorites.add(property_id)

                    st.rerun()

            with emily_col:
                with st.popover(
                    "💬 Спросить Emily",
                    use_container_width=True
                ):
                    st.markdown(f"### {t('emily_about')}")
                    st.write(
                        f"{t('type')}: {property_type}. {t('city')}: "
                        f"{p['city']}, {t('district').lower()}: {p['district']}."
                    )
                    st.write(
                        f"{t('price')}: ${p['price']:,}. "
                        f"{t('area')}: {p['area_m2']} {'m²' if LANG == 'en' else 'м²'}."
                    )
                    st.write(
                        f"{t('bedrooms')}: {p['bedrooms']}. "
                        f"{t('bathrooms')}: {p['bathrooms']}. "
                        f"{t('total_rooms')}: {p['rooms']}."
                    )
                    st.write(f"**{t('important')}**")
                    st.write(p["description"])
                    st.caption(t("demo_answer"))

            with details_col:
                with st.popover(
                    "Подробнее",
                    use_container_width=True
                ):
                    st.subheader(f"{t('property')} {property_id}")
                    st.write(f"**{t('type')}:** {property_type}")
                    st.write(f'**{t("city")}:** {p["city"]}, {p["state"]}')
                    st.write(f'**{t("district")}:** {p["district"]}')
                    st.write(f'**{t("price")}:** ${p["price"]:,}')
                    st.write(f'**{t("area")}:** {p["area_m2"]} м²')
                    st.write(f'**{t("bedrooms")}:** {p["bedrooms"]}')
                    st.write(f'**{t("bathrooms")}:** {p["bathrooms"]}')
                    st.write(f'**{t("rooms")}:** {p["rooms"]}')
                    st.write(p["description"])



# PROPERTY COMPARISON
st.divider()
st.subheader(t("comparison"))
st.write(t("comparison_help"))

property_options = {
    f"{p['id']} | {p['city']} | ${p['price']:,}": p
    for p in properties
}

option_labels = list(property_options.keys())

if len(option_labels) >= 2:
    compare_col1, compare_col2 = st.columns(2)

    with compare_col1:
        first_label = st.selectbox(
            "Первый объект",
            option_labels,
            index=0,
            key="comparison_first"
        )

    with compare_col2:
        second_label = st.selectbox(
            "Второй объект",
            option_labels,
            index=1,
            key="comparison_second"
        )

    if first_label == second_label:
        st.warning(t("different_properties"))
    else:
        first = property_options[first_label]
        second = property_options[second_label]
        selected_pair = (first["id"], second["id"])

        image_col1, image_col2 = st.columns(2)

        with image_col1:
            st.markdown(f"### {first['id']}")
            image_url = PROPERTY_IMAGES.get(first["id"])
            if image_url:
                st.image(image_url, use_container_width=True)
            st.markdown(f"**{first['city']}, {first['state_code']}**")
            st.markdown(f"## ${first['price']:,}")

        with image_col2:
            st.markdown(f"### {second['id']}")
            image_url = PROPERTY_IMAGES.get(second["id"])
            if image_url:
                st.image(image_url, use_container_width=True)
            st.markdown(f"**{second['city']}, {second['state_code']}**")
            st.markdown(f"## ${second['price']:,}")

        st.markdown(f"### {t('characteristics')}")

        comparison_rows = [
            (
                "Тип недвижимости",
                t("house") if first["type"] == "house" else t("apartment"),
                t("house") if second["type"] == "house" else t("apartment")
            ),
            (t("district"), first["district"], second["district"]),
            (t("price"), f"${first['price']:,}", f"${second['price']:,}"),
            (t("area"), f"{first['area_m2']} m²" if LANG == "en" else f"{first['area_m2']} м²", f"{second['area_m2']} m²" if LANG == "en" else f"{second['area_m2']} м²"),
            (t("bedrooms"), str(first["bedrooms"]), str(second["bedrooms"])),
            (
                t("bathrooms"),
                str(first["bathrooms"]),
                str(second["bathrooms"])
            ),
            (t("total_rooms"), str(first["rooms"]), str(second["rooms"])),
        ]

        comparison_display = [
            {
                t("parameter"): row[0],
                first["id"]: row[1],
                second["id"]: row[2],
            }
            for row in comparison_rows
        ]

        st.table(comparison_display)

        # Replace the old price/size commentary with real mapped neighborhood context.
        st.markdown(f"### {t('infrastructure')}")
        st.caption(t("infrastructure_note"))

        environment_col1, environment_col2 = st.columns(2)
        for environment_col, prop in zip(
            (environment_col1, environment_col2), (first, second)
        ):
            with environment_col:
                st.markdown(f"#### {prop['id']} · {prop['district']}")
                try:
                    with st.spinner(t("studying")):
                        environment = get_neighborhood_info(
                            prop["city"], prop["district"], prop["state"]
                        )
                except requests.RequestException as error:
                    st.warning(
                        t("osm_error")
                    )
                    st.caption(f"Техническая причина: {error}")
                    continue
                except (ValueError, KeyError, TypeError) as error:
                    st.warning(t("geo_error"))
                    st.caption(f"Техническая причина: {error}")
                    continue

                if environment.get("error"):
                    st.info(environment["error"])
                    continue

                if environment["center_distance"] is not None:
                    st.write(
                        f"**{t('city_center')}:** "
                        f"около {environment['center_distance']:.1f} км."
                    )
                else:
                    st.write(t("distance_unavailable"))

                found_any = False
                for category, places in environment["groups"].items():
                    if not places:
                        continue
                    found_any = True
                    st.markdown(f"**{category}**")
                    for place in places:
                        st.write(
                            f"• {place['name']} · примерно "
                            f"{place['distance']:.1f} км"
                        )

                if not found_any:
                    st.info(
                        t("no_infrastructure")
                    )

                st.caption(
                    t("source")
                )

else:
    st.info(t("need_two"))

# FOOTER
st.divider()
st.caption(
    "AI Real Estate Assistant | USA | Portfolio Demo | Illustrative Data"
)
