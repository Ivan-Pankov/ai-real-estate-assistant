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



st.set_page_config(
    page_title="AI Real Estate Assistant | USA",
    page_icon="🏡",
    layout="wide"
)

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

[data-testid="stCaptionContainer"] {
    font-size: 15px !important;
}

.stApp h1 { font-size: 28px !important; }
.stApp h2 { font-size: 24px !important; }
.stApp h3 { font-size: 21px !important; }

</style>
""", unsafe_allow_html=True)



def get_emily_response(message, properties):
    """Generate a local demo response based on the property catalogue."""
    query = message.strip()

    pending_query = st.session_state.get("emily_pending_query")
    if pending_query and query:
        query = f"{pending_query} {query}"
        st.session_state.pop("emily_pending_query", None)

    if not query:
        return "Напишите, пожалуйста, что именно вы ищете."

    greeting_words = ("привет", "здравствуй", "добрый день", "hello")
    if any(word in query.lower() for word in greeting_words):
        return (
            "Здравствуйте! Я Emily. Могу помочь найти дом или квартиру "
            "в Майами, Остине или Сан-Франциско. "
            "Например, напишите: «Дом в Майами до 500 тысяч долларов»."
        )

    results, criteria = search_properties(properties, query)
    recognized = describe_criteria(criteria)

    lower_query = query.lower()
    recommendation_words = (
        "посоветуй", "порекомендуй", "рекомендац",
        "лучше выбрать", "лучший вариант", "самый выгодный",
        "что выбрать", "recommend", "best option", "which one",
    )
    is_recommendation = any(
        word in lower_query for word in recommendation_words
    )

    if is_recommendation:
        if criteria["max_price"] is None:
            st.session_state.emily_pending_query = query
            return (
                "С удовольствием помогу выбрать лучший вариант. "
                "Какой максимальный бюджет покупки вы планируете? "
                "Например, $500,000."
            )

        recommendations = recommend_properties(
            results,
            budget=criteria["max_price"],
            min_bedrooms=criteria["bedrooms"],
        )

        if not recommendations:
            return (
                "В демонстрационном каталоге нет подходящих объектов "
                "в рамках указанных условий. Попробуйте изменить параметры."
            )

        return {
            "kind": "property_recommendation",
            "content": (
                "Я сравнила подходящие объекты по площади, "
                "количеству спален и остатку бюджета. "
                "Вот моя рекомендация:"
            ),
            "properties": recommendations,
            "total": len(results),
            "budget": criteria["max_price"],
        }

    # Ask for the city when the user specifies only a property type.
    if criteria["property_type"] and not criteria["city"] and not criteria["state"]:
        st.session_state.emily_pending_query = query
        return (
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
            "Поняла, какой объект и город вы рассматриваете. "
            "Какой бюджет покупки вы планируете? "
            "Например, до 400 тысяч долларов."
        )

    if recognized:
        if not results:
            return (
                "Я поняла ваш запрос: "
                + "; ".join(recognized)
                + ". Но в демонстрационном каталоге нет объектов "
                  "с такими параметрами. Попробуйте изменить бюджет, "
                  "город или количество спален."
            )

        return {
            "kind": "property_results",
            "content": "Я нашла подходящие варианты в демонстрационном каталоге:",
            "properties": results,
            "total": len(results)
        }

    lower_query = query.lower()

    if any(word in lower_query for word in ("сравнить", "сравнение", "разница")):
        return (
            "Конечно! Откройте раздел «Сравнение недвижимости» ниже "
            "в приложении и выберите два разных объекта. "
            "Я автоматически покажу их сравнение и свой анализ."
        )

    if any(word in lower_query for word in ("помощь", "что умеешь", "возможности")):
        return (
            "Я могу искать дома и квартиры в Майами, Остине и "
            "Сан-Франциско, учитывать бюджет и количество спален, "
            "показывать характеристики объектов и помогать сравнивать "
            "два варианта. Попробуйте задать конкретный запрос."
        )

    return (
        "Пока я работаю в демонстрационном режиме и отвечаю "
        "по каталогу недвижимости. Укажите город, тип объекта "
        "и бюджет. Например: «Квартира в Остине до 400 тысяч долларов»."
    )


# EMILY AI ASSISTANT
def set_emily_query(query):
    st.session_state.emily_messages.append(
        {"role": "user", "content": query}
    )

    answer = get_emily_response(query, properties)

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
        st.markdown("## Привет! Я Emily, ваш виртуальный консультант")
        st.write(
            "Помогу разобраться с объектами, сравнить варианты и подобрать "
            "недвижимость в США."
        )
        st.caption("🟢 AI-консультант · Демонстрационный режим")

        button1, button2, button3 = st.columns(3)

        with button1:
            st.button(
                "🏡 Дом в Майами",
                key="emily_miami",
                use_container_width=True,
                on_click=set_emily_query,
                args=("Дом в Майами до 500 тысяч долларов",)
            )

        with button2:
            st.button(
                "🏢 Квартира в Остине",
                key="emily_austin",
                use_container_width=True,
                on_click=set_emily_query,
                args=("Квартира в Остине с 2 спальнями",)
            )

        with button3:
            st.button(
                "🌉 Дом в Сан-Франциско",
                key="emily_sf",
                use_container_width=True,
                on_click=set_emily_query,
                args=("Дом в Сан-Франциско до 900 тысяч долларов",)
            )



# EMILY CHAT
st.divider()
st.subheader("💬 Чат с Emily")


if "emily_messages" not in st.session_state:
    st.session_state.emily_messages = [
        {
            "role": "assistant",
            "content": "Чем могу помочь с подбором недвижимости?"
        }
    ]

with st.container(border=True):
    for message in st.session_state.emily_messages:
        with st.chat_message(message["role"]):
            if message.get("kind") in ("property_results", "property_recommendation"):
                is_recommendation = message["kind"] == "property_recommendation"

                if is_recommendation:
                    st.markdown("### 🏆 Рекомендации Emily")

                st.markdown(message["content"])

                for index, prop in enumerate(message["properties"], start=1):
                    with st.container(border=True):
                        if is_recommendation and index == 1:
                            st.markdown("**🥇 Первый выбор Emily**")
                        elif is_recommendation:
                            st.markdown(f"**🥈 Альтернатива {index - 1}**")

                        st.markdown(f"**🏡 {prop['id']}**")
                        st.caption(f"📍 {prop['district']}, {prop['city']}")
                        st.markdown(
                            f"<div style='font-size:25px; font-weight:700; "
                            f"color:#176b50;'>${prop['price']:,}</div>",
                            unsafe_allow_html=True
                        )

                        if is_recommendation:
                            remaining = message["budget"] - prop["price"]
                            st.caption(f"💰 Остаток бюджета: ${remaining:,}")

                        info1, info2, info3 = st.columns(3)
                        info1.metric("Спальни", prop["bedrooms"])
                        info2.metric("Площадь", f"{prop['area_m2']} м²")
                        info3.metric("Ванные", prop["bathrooms"])

                if is_recommendation:
                    st.caption(
                        f"Подходящих объектов: {message['total']}. "
                        f"Показано рекомендаций: {len(message['properties'])}."
                    )
                else:
                    st.caption(f"Найдено объектов: {message['total']}")
            else:
                st.markdown(message["content"])

    user_message = st.chat_input(
        "Напишите сообщение Emily...",
        key="emily_chat_input"
    )

    if user_message:
        st.session_state.emily_messages.append(
            {"role": "user", "content": user_message}
        )

        answer = get_emily_response(user_message, properties)

        if isinstance(answer, dict):
            st.session_state.emily_messages.append(
                {"role": "assistant", **answer}
            )
        else:
            st.session_state.emily_messages.append(
                {"role": "assistant", "content": answer}
            )

        st.rerun()

if st.button("🗑️ Очистить переписку", key="clear_emily_chat"):
    st.session_state.emily_messages = [
        {
            "role": "assistant",
            "content": "Чем могу помочь с подбором недвижимости?"
        }
    ]
    st.rerun()


# HEADER
st.title("🏡 AI-помощник по недвижимости США")
st.caption("Подбор домов и квартир в США")

st.info(
    "Демонстрационная версия. Объекты, цены и фотографии условные. "
    "Это не актуальные объявления о продаже."
)


# NATURAL LANGUAGE SEARCH
st.subheader("🔎 Поиск на естественном языке")

natural_query = st.text_input(
    "Опишите, какую недвижимость вы ищете",
    placeholder="Например: Дом в Майами до 500 тысяч долларов с 3 спальнями",
    key="natural_query"
)

if natural_query.strip():
    filtered, criteria = search_properties(properties, natural_query)
    recognized = describe_criteria(criteria)

    with st.expander("Что понял поисковый помощник", expanded=True):
        if recognized:
            for item in recognized:
                st.write(f"• {item}")
        else:
            st.write("Параметры поиска не распознаны. Поиск по тексту.")

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


st.sidebar.header("Дополнительные фильтры")

states = sorted({p["state"] for p in properties})

min_price = min(p["price"] for p in properties)
max_price = max(p["price"] for p in properties)

selected_state = st.sidebar.selectbox(
    "Штат",
    ["Все штаты"] + states,
    key="filter_state"
)

cities = sorted({
    p["city"] for p in properties
    if selected_state == "Все штаты" or p["state"] == selected_state
})

selected_city = st.sidebar.selectbox(
    "Город",
    ["Все города"] + cities,
    key="filter_city"
)

type_options = {
    "Дом": "house",
    "Квартира / Condo": "apartment"
}

selected_type = st.sidebar.selectbox(
    "Тип недвижимости",
    ["Любой тип"] + list(type_options.keys()),
    key="filter_type"
)

price_range = st.sidebar.slider(
    "Бюджет (USD)",
    min_value=min_price,
    max_value=max_price,
    value=(min_price, max_price),
    step=10000,
    format="$%d",
    key="filter_price_range"
)

bedroom_options = sorted({p["bedrooms"] for p in properties})

selected_bedrooms = st.sidebar.selectbox(
    "Спальни",
    ["Любое количество"] + bedroom_options,
    key="filter_bedrooms"
)

st.sidebar.divider()

favorites_only = st.sidebar.checkbox(
    "❤️ Только избранное",
    key="filter_favorites_only"
)

st.sidebar.button(
    "Сбросить фильтры",
    use_container_width=True,
    on_click=reset_filters
)

def clear_favorites():
    st.session_state.favorites.clear()

st.sidebar.button(
    "Очистить избранное",
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
    ["Сначала дешевле", "Сначала дороже", "Больше площадь"]
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

col1.metric("Найдено объектов", len(filtered))
col2.metric("В избранном", len(st.session_state.favorites))

if filtered:
    average_price = sum(p["price"] for p in filtered) // len(filtered)
    average_area = sum(p["area_m2"] for p in filtered) // len(filtered)

    col3.metric("Средняя цена", f"${average_price:,}")
    col4.metric("Средняя площадь", f"{average_area} м²")
else:
    col3.metric("Средняя цена", "—")
    col4.metric("Средняя площадь", "—")


# PROPERTY CARDS
st.divider()
st.subheader("🏘️ Результаты поиска")

if not filtered:
    st.warning("По заданным параметрам ничего не найдено.")

for p in filtered:
    property_id = p["id"]
    is_favorite = property_id in st.session_state.favorites

    property_type = (
        "Дом" if p["type"] == "house"
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

            metric1.metric("Спальни", p["bedrooms"])
            metric2.metric("Ванные", p["bathrooms"])
            metric3.metric("Комнаты", p["rooms"])
            metric4.metric("Площадь", f'{p["area_m2"]} м²')

            st.write(p["description"])

            button_col, emily_col, details_col = st.columns(3)

            with button_col:
                favorite_label = (
                    "❤️ Убрать из избранного"
                    if is_favorite
                    else "🤍 В избранное"
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
                    st.markdown("### Emily о выбранном объекте")
                    st.write(
                        f"Это {property_type.lower()} в городе "
                        f"{p['city']}, район {p['district']}."
                    )
                    st.write(
                        f"Цена объекта составляет ${p['price']:,}. "
                        f"Площадь — {p['area_m2']} м²."
                    )
                    st.write(
                        f"Количество спален: {p['bedrooms']}. "
                        f"Количество ванных комнат: {p['bathrooms']}. "
                        f"Всего комнат: {p['rooms']}."
                    )
                    st.write("**Что важно знать:**")
                    st.write(p["description"])
                    st.caption(
                        "Ответ сформирован по демонстрационным данным каталога."
                    )

            with details_col:
                with st.popover(
                    "Подробнее",
                    use_container_width=True
                ):
                    st.subheader(f"Объект {property_id}")
                    st.write(f"**Тип:** {property_type}")
                    st.write(f'**Город:** {p["city"]}, {p["state"]}')
                    st.write(f'**Район:** {p["district"]}')
                    st.write(f'**Цена:** ${p["price"]:,}')
                    st.write(f'**Площадь:** {p["area_m2"]} м²')
                    st.write(f'**Спальни:** {p["bedrooms"]}')
                    st.write(f'**Ванные комнаты:** {p["bathrooms"]}')
                    st.write(f'**Комнаты:** {p["rooms"]}')
                    st.write(p["description"])



# PROPERTY COMPARISON
st.divider()
st.subheader("⚖️ Сравнение недвижимости")
st.write(
    "Выберите два объекта, чтобы Emily сравнила их характеристики "
    "и помогла оценить различия."
)

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
        st.warning("Выберите два разных объекта для сравнения.")
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

        st.markdown("### Характеристики объектов")

        comparison_rows = [
            (
                "Тип недвижимости",
                "Дом" if first["type"] == "house" else "Квартира / Condo",
                "Дом" if second["type"] == "house" else "Квартира / Condo"
            ),
            ("Район", first["district"], second["district"]),
            ("Цена", f"${first['price']:,}", f"${second['price']:,}"),
            ("Площадь", f"{first['area_m2']} м²", f"{second['area_m2']} м²"),
            ("Спальни", str(first["bedrooms"]), str(second["bedrooms"])),
            (
                "Ванные комнаты",
                str(first["bathrooms"]),
                str(second["bathrooms"])
            ),
            ("Всего комнат", str(first["rooms"]), str(second["rooms"])),
        ]

        comparison_display = [
            {
                "Параметр": row[0],
                first["id"]: row[1],
                second["id"]: row[2],
            }
            for row in comparison_rows
        ]

        st.table(comparison_display)

        # Replace the old price/size commentary with real mapped neighborhood context.
        st.markdown("### 📍 Инфраструктура и окружение")
        st.caption(
            "Emily показывает объекты, отмеченные в OpenStreetMap в радиусе 3 км "
            "от географического центра района. Это ориентир района, а не точка "
            "конкретного дома: демонстрационный каталог не содержит адресов и координат."
        )

        environment_col1, environment_col2 = st.columns(2)
        for environment_col, prop in zip(
            (environment_col1, environment_col2), (first, second)
        ):
            with environment_col:
                st.markdown(f"#### {prop['id']} · {prop['district']}")
                try:
                    with st.spinner("Emily изучает инфраструктуру района..."):
                        environment = get_neighborhood_info(
                            prop["city"], prop["district"], prop["state"]
                        )
                except requests.RequestException as error:
                    st.warning(
                        "Не удалось получить данные OpenStreetMap. "
                        "Попробуйте обновить страницу позже."
                    )
                    st.caption(f"Техническая причина: {error}")
                    continue
                except (ValueError, KeyError, TypeError) as error:
                    st.warning("Не удалось обработать географические данные района.")
                    st.caption(f"Техническая причина: {error}")
                    continue

                if environment.get("error"):
                    st.info(environment["error"])
                    continue

                if environment["center_distance"] is not None:
                    st.write(
                        f"**До центра города по прямой:** "
                        f"около {environment['center_distance']:.1f} км."
                    )
                else:
                    st.write("Расстояние до центра города пока недоступно.")

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
                        "В OpenStreetMap пока не найдены отмеченные объекты "
                        "инфраструктуры в радиусе 3 км."
                    )

                st.caption(
                    "Источник: OpenStreetMap. Расстояния рассчитаны по прямой "
                    "от центра района; фактический маршрут может быть длиннее."
                )

else:
    st.info("Для сравнения необходимо минимум два объекта.")

# FOOTER
st.divider()
st.caption(
    "AI Real Estate Assistant | USA | Portfolio Demo | Illustrative Data"
)
