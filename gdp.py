"""HW5 GDP plot. AI assistance: ChatGPT generated and revised portions of this code.
Requires pandas, requests, lxml, and plotly. Run: python gdp.py
Writes stacked_bar.html to the current working directory.
"""

# [wAAI ChatGPT] Read the assignment's Wikipedia page and identify the IMF table.
import requests
from io import StringIO
import pandas as pd
import plotly.express as px

url = (
    "https://en.wikipedia.org/w/index.php?"
    "title=List_of_countries_by_GDP_(nominal)&oldid=1187446467"
)

response = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30
)
response.raise_for_status()

# Read all HTML tables on the page
page_tables = pd.read_html(StringIO(response.text))

# Identify the GDP table by its column headings
gdp_raw = None

for table in page_tables:
    headings = " ".join(str(col) for col in table.columns).lower()

    if "country" in headings and (
        "imf" in headings or "international monetary fund" in headings
    ):
        gdp_raw = table
        break

if gdp_raw is None:
    for number, table in enumerate(page_tables):
        print(f"Table {number}: {table.columns.tolist()}")
    raise ValueError("Could not identify the IMF table from its headings.")

print(gdp_raw.head())
print("Column names:")
print(gdp_raw.columns)

# [wAAI ChatGPT] Select and clean IMF forecasts and UN regions.

# The table has two-row column headings.
imf_column = next(
    col for col in gdp_raw.columns
    if col[0].startswith("IMF") and col[1] == "Forecast"
)

gdp = gdp_raw[
    [
        ("Country/Territory", "Country/Territory"),
        ("UN region", "UN region"),
        imf_column
    ]
].copy()

gdp.columns = ["country", "region", "gdp_millions"]

# Remove footnote markers and surrounding spaces.
for column in ["country", "region"]:
    gdp[column] = (
        gdp[column]
        .astype("string")
        .str.replace(r"\[.*?\]", "", regex=True)
        .str.strip()
    )

# Convert IMF forecasts to numbers.
gdp["gdp_millions"] = pd.to_numeric(
    gdp["gdp_millions"]
    .astype(str)
    .str.replace(r"\[.*?\]", "", regex=True)
    .str.replace(",", "", regex=False)
    .str.strip(),
    errors="coerce"
)

# Exclude the World total and rows without IMF forecasts.
gdp = gdp.loc[gdp["country"] != "World"].dropna(
    subset=["gdp_millions"]
).copy()

# Convert millions to trillions of US dollars.
gdp["gdp_trillions"] = gdp["gdp_millions"] / 1_000_000

print(gdp.head())
print(f"Countries/territories with IMF forecasts: {len(gdp)}")

print(
    gdp.groupby("region", as_index=False)
    .agg(
        countries=("country", "count"),
        gdp_trillions=("gdp_trillions", "sum")
    )
    .sort_values("gdp_trillions", ascending=False)
)

# [wAAI ChatGPT] Plot countries within UN regions and export interactive HTML.
# Order regions by total GDP
region_order = (
    gdp.groupby("region")["gdp_trillions"]
    .sum()
    .sort_values(ascending=False)
    .index.tolist()
)

# Each country is a segment within its region's bar
fig_gdp = px.bar(
    gdp.sort_values("gdp_trillions", ascending=False),
    x="region",
    y="gdp_trillions",
    color="country",
    category_orders={"region": region_order},
    title="GDP by Country and UN Region — IMF Forecasts",
    labels={
        "region": "UN region",
        "gdp_trillions": "GDP (trillions of US dollars)",
        "country": "Country/Territory"
    },
    hover_name="country",
    height=650
)

fig_gdp.update_layout(
    barmode="stack",
    template="plotly_white",
    showlegend=False
)

fig_gdp.update_traces(
    hovertemplate=(
        "<b>%{hovertext}</b><br>"
        "Region: %{x}<br>"
        "GDP: US$%{y:.3f} trillion"
        "<extra></extra>"
    )
)



# Save a standalone interactive webpage
fig_gdp.write_html("stacked_bar.html", include_plotlyjs=True)

print("Saved stacked_bar.html")