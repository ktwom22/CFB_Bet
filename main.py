import os
import time
import io
import pandas as pd
import requests
from flask import Flask, render_template_string

app = Flask(__name__)

# Google Sheet CSV URL (published)
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR-2usKJIhDgXcx0EiAO9zFitGNdhquuYheq85oh97KtR8P_X9LUinJhr9ryzsa1iPNjR8WwzLA1glo/pub?gid=596426925&single=true&output=csv"

# Cache
cache_data = None
cache_time = 0
CACHE_TTL = 300  # 5 minutes


def fetch_sheet_data():
    """Fetch CSV from Google Sheets and normalize columns."""
    global cache_data, cache_time
    now = time.time()

    if cache_data is not None and now - cache_time < CACHE_TTL:
        return cache_data

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(CSV_URL, headers=headers, timeout=30)
        response.raise_for_status()

        df = pd.read_csv(io.StringIO(response.text))

        # Normalize headers
        df.columns = df.columns.str.strip().str.title()

        # Fill missing logos with placeholder
        df['Away Logo'] = df['Away Logo'].fillna("https://via.placeholder.com/60x60.png?text=No+Logo")
        df['Home Logo'] = df['Home Logo'].fillna("https://via.placeholder.com/60x60.png?text=No+Logo")

        cache_data = df
        cache_time = now
        return df

    except Exception as e:
        print(f"Error fetching Google Sheet: {e}")
        return pd.DataFrame()


@app.route("/")
def index():
    df = fetch_sheet_data()
    if df.empty:
        return "<h2>Unable to fetch matchup data at this time.</h2>"

    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CFB Predicted Matchups</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                padding: 20px;
                background-color: #f0f2f5;
            }
            h2 {
                text-align: center;
                margin-bottom: 30px;
            }
            .matchup-card {
                background-color: #fff;
                border-radius: 12px;
                padding: 15px 20px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            .team {
                display: flex;
                flex-direction: column;
                align-items: center;
                width: 45%;
            }
            .team img {
                height: 60px;
                width: 60px;
                object-fit: contain;
                margin-bottom: 5px;
            }
            .spread {
                font-size: 14px;
                color: #555;
            }
            .outcome {
                font-weight: bold;
                font-size: 16px;
                color: #333;
            }
            @media (max-width: 600px) {
                .matchup-card {
                    flex-direction: column;
                    text-align: center;
                }
                .team {
                    width: 100%;
                    margin-bottom: 10px;
                }
            }
        </style>
    </head>
    <body>
        <h2>CFB Predicted Matchups</h2>
        {% for _, row in matchups.iterrows() %}
            <div class="matchup-card">
                <div class="team">
                    <img src="{{ row['Away Logo'] }}" alt="{{ row['Away Team'] }}">
                    {{ row['Away Team'] }}
                    {% if row['Away Spread'] %} <div class="spread">({{ row['Away Spread'] }})</div> {% endif %}
                </div>
                <div class="outcome">→ {{ row['Predicted Outcome'] }}</div>
                <div class="team">
                    <img src="{{ row['Home Logo'] }}" alt="{{ row['Home Team'] }}">
                    {{ row['Home Team'] }}
                    {% if row['Home Spread'] %} <div class="spread">({{ row['Home Spread'] }})</div> {% endif %}
                </div>
            </div>
        {% endfor %}
    </body>
    </html>
    """
    return render_template_string(template, matchups=df)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
