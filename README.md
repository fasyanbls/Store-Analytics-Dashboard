# Store Analytics Dashboard

## Project Overview

The **Store Analytics Dashboard** is an operational analytics dashboard designed for business owners and store managers who need clear, data-backed answers without needing to understand SQL or data science. The dashboard connects directly to a **PostgreSQL database** (Sakila schema), runs dynamic queries based on user-selected filters, and presents insights across five analytical dimensions: store performance, inventory efficiency, customer behavior, rental patterns, and revenue forecasting. Built as a **data analytics project**, this not just to visualize data, but to think like a business analyst: understand what questions a business owner actually needs answered, figure out which data tells that story, and build something that communicates insights clearly to a non-technical audience. This dashboard bridges the gap between raw database records and strategic business decisions.

---

## Dashboard Preview

### Tab 1 — Overview
<img width="1918" height="996" alt="image" src="https://github.com/user-attachments/assets/36590c8f-8305-4933-9dbe-9c3c674cb2b1" />

---

### Tab 2 — Inventory & Categories
<img width="1919" height="997" alt="image" src="https://github.com/user-attachments/assets/a6bb21f3-20f2-4453-8a76-5bc459835e58" />

---

### Tab 3 — Customers & Geography
<img width="1918" height="1000" alt="image" src="https://github.com/user-attachments/assets/6e2fc390-2d7b-498c-a4fe-4d330bb8a5ee" />

---

### Tab 4 — Rental Patterns
<img width="1919" height="1010" alt="image" src="https://github.com/user-attachments/assets/601466bb-76da-4d2b-867f-d6549fdd0281" />

---

### Tab 5 — ML Predictions
<img width="1919" height="927" alt="image" src="https://github.com/user-attachments/assets/ccddc1d9-d8ba-4e5c-badd-cd0241ca34a2" />

---

## Dataset

- **Source:** [Sakila DVD Rental Database](https://dev.mysql.com/doc/sakila/en/) — a standard sample database widely used for SQL learning and analytics projects
- **Database:** PostgreSQL

---

## Tech Stack

| Layer | Tools |
|---|---|
| **Frontend** | Streamlit |
| **Visualization** | Plotly Express, Plotly Graph Objects |
| **Database** | PostgreSQL + psycopg2 |
| **Machine Learning** | scikit-learn (Linear Regression) |
| **Data Processing** | Pandas, NumPy |
| **Styling** | Custom CSS (Inter font, Navy + Pink theme, Dark/Light mode) |

---

## Features

### Tab 1 — Overview
- **6 KPI Cards:** Total Revenue, Active Customers, Total Rentals, Inventory, Film Titles, Avg Transaction Value
- **Store Revenue & Rentals Bar Charts** — side-by-side store comparison
- **Monthly/Daily Revenue Trend** — line chart with Store 1 vs Store 2 breakdown
- **Customer Distribution Donut Chart** — segmented by rental frequency (Elite, Frequent, Regular, Casual)
- **Monthly Rentals Trend** — stacked area chart showing volume over time
- **Top Categories by Revenue** — horizontal bar chart

### Tab 2 — Inventory & Categories
- **Revenue per Inventory Unit** — all 16 categories ranked by revenue efficiency per copy
- **Category Rental Share** — pie chart showing rental volume distribution
- **Top Films by Revenue** — best performing individual titles

### Tab 3 — Customers & Geography
- **Top 15 Customers Table** — ranked by total revenue with rental count and last rental date
- **Customer Segmentation** — Elite (40+ rentals), Frequent (30–40), Regular (20–29), Casual (<20)
- **Geographic Revenue Map** — world map showing revenue by country
- **Churn Risk Indicator** — customers flagged as at-risk based on inactivity threshold

### Tab 4 — Rental Patterns
- **Revenue by Day of Week** — bar chart showing which days generate the most revenue
- **Hourly Heatmap** — rental activity by hour and day of week
- **Late Return Analysis** — return behavior patterns

### Tab 5 — ML Predictions
- **3-Month Revenue Forecast** — Linear Regression model trained on historical monthly revenue and transaction volume
- **Forecast Cards** — projected revenue with likely range (±MAE) for Mar, Apr, May 2006
- **Business Decision Simulator (What-If Tool)** — simulate the revenue impact of:
  - Rental price adjustments (±%)
  - Promotional discounts (%)
  - New customer acquisition targets

---

## Key Business Insights

### Store Performance
- Store 1 generated **$30,628** and Store 2 generated **$30,683** — a difference of only **$55** across 10 months
- Both stores move in sync, peaking together in **July 2005 ($14k+)** and dropping together in **February 2006 (~$250)**
- Store 2 has **198 more rentals** but nearly identical revenue → Store 2 customers rent more frequently at lower value per visit; Store 1 customers visit less but spend more per transaction

### Inventory Efficiency
- **Comedy ($14.90/copy)** and **New titles ($14.40/copy)** lead in revenue per inventory unit
- **Children ($12.30/copy)** and **Family ($12.40/copy)** are the least efficient categories
- Gap between top and bottom performers: ~**$2.60 per copy** — significant at scale

### Customer Behavior
- Top customer **Eleanor Hunt** generated **$211.55** from 46 rentals
- **Marion Snyder** (39 rentals, $194.61) outranks **Clara Shaw** (42 rentals, $189.60), demonstrating that revenue is driven by spending value, not just frequency
- Most top customers' last rental was **August 2005** — coinciding with peak revenue. Their inactivity directly correlates with the revenue drop

### Revenue Patterns
- **Tuesday** is the strongest revenue day overall across both stores
- During peak months (July–August), weekends outperform weekdays
- **February 2006** shows revenue only on Tuesday, both stores confirming this was not a normal operating month

---

## Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL with Sakila database loaded
- pip

### 1. Clone the Repository
```bash
git clone https://github.com/fasyanbls/Store-Analytics-Dashboard.git
cd Store-Analytics-Dashboard
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up the Database
Load the Sakila database into PostgreSQL:
```bash
psql -U postgres -c "CREATE DATABASE dvdrental;"
psql -U postgres -d dvdrental -f sakila-schema.sql
psql -U postgres -d dvdrental -f sakila-data.sql
```

### 4. Configure Database Connection
Update the connection settings in `app.py`:
```python
conn = psycopg2.connect(
    host="localhost",
    database="dvdrental",
    user="your_username",
    password="your_password",
    port=5432
)
```

### 5. Run the Dashboard
```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

---

## Requirements

```
streamlit
pandas
numpy
plotly
psycopg2-binary
scikit-learn
```

---

## Strategic Recommendations (From Analysis)

1. **Prioritize Comedy, New, Sports, and Games** for restocking, highest revenue per copy consistently
2. **Differentiate store strategies**, Store 2 needs frequency-based loyalty programs; Store 1 needs premium value offerings
3. **Reactivate top customers** who last rented in August 2005, personalized outreach with exclusive offers
4. **Run Tuesday promotions** for regular months; shift to weekends during peak season (July–August)
5. **Use the ML Simulator** before making any pricing or discount decision, test the impact first

---

## Author

**Fasya Nabila Salim**

- GitHub: [@fasyanbls](https://github.com/fasyanbls)
- LinkedIn: [linkedin.com/in/username](https://linkedin.com/in/fasyanbls)

---


