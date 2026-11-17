# AI Real Estate Assistant

An interactive AI-assisted real estate search demo built with Python and Streamlit. The application helps users explore a fictional catalog of residential properties in selected U.S. cities through filters and natural-language queries.

## Project Overview

AI Real Estate Assistant is a portfolio project demonstrating how a conversational interface can make property search more accessible.

Users can interact with Emily, a demo real estate assistant, to search for properties, receive recommendations, save favorites, and compare selected listings.

**Important:** This project currently uses fictional demonstration data. It does not display live real estate listings or verified market prices.

## Features

- **Property Search:** Search residential properties by city, state, property type, budget, and number of bedrooms.
- **Natural-Language Queries:** Describe search criteria in everyday language.
- **Emily Assistant:** Interact with a local rule-based conversational assistant.
- **Property Recommendations:** Receive ranked suggestions based on budget, bedrooms, property area, and remaining budget.
- **Favorites:** Save and clear favorite properties during a session.
- **Property Comparison:** Compare two properties and view a generated analysis.
- **Russian User Interface:** The application interface is in Russian.

## Demo Data Disclaimer

The property catalog contains fictional demonstration entries for Miami, Austin, and San Francisco.

Property details, prices, and images are provided for interface and functionality testing only. They are not actual offers for sale and should not be used for real estate, financial, or investment decisions.

## Technology Stack

- Python
- Streamlit
- JSON
- pytest

## Project Structure

```text
ai-real-estate-assistant/
├── app.py
├── assistant.py
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── config.toml
├── assets/
│   └── emily.png
├── data/
│   └── properties.json
└── tests/
    └── test_assistant.py
```

## Installation

Clone the repository:

```bash
git clone https://github.com/Ivan-Pankov/ai-real-estate-assistant.git
cd ai-real-estate-assistant
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Running the Application

Start the Streamlit application:

```bash
streamlit run app.py
```

Open the local URL shown in the terminal, usually:

```text
http://localhost:8501
```

## Running Tests

Run the automated tests:

```bash
pytest -v
```

The test suite covers property search criteria, budget constraints, bedroom requirements, and recommendation filtering.

## Architecture and Current Limitations

The application separates the user interface (`app.py`) from search and recommendation logic (`assistant.py`).

Emily currently operates as a deterministic, rule-based demo assistant. The project does not yet include a live large language model, OpenAI API integration, external real estate data providers, user authentication, or a production database.

Recommendations are generated using transparent scoring rules. They should be treated as demonstration results rather than professional real estate advice.

## Future Improvements

Potential next development steps include:

- Integration with a language model for more flexible conversations.
- Connection to verified real estate data sources and APIs.
- More advanced property ranking and recommendation methods.
- Persistent user accounts and saved favorites.
- Improved property details, maps, and location-based search.
- Deployment as a publicly accessible web application.

## Project Status

This is an actively developed portfolio project. Features and architecture may evolve as development continues.

