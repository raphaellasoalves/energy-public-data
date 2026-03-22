# ANP Data Crawlers

Python crawlers for extracting data from public ANP (Agência Nacional do Petróleo, Gás Natural e Biocombustíveis) Power BI dashboards.

The ANP publishes operational and regulatory data from Brazil's oil & gas sector through interactive Power BI panels. This repository automates the extraction of tabular data from those panels into structured Excel files.

---

## Crawlers

| Script | Panel | Output |
|---|---|---|
| `exploratory_phase.py` | Blocos sob Contrato — Fase Exploratória | `anp_exploratory_phase.xlsx` |
| `well_interventions.py` | Intervenção em Poços (filter: Perfuração) | `anp_well_interventions.xlsx` |
| `development_fields.py` | Campos em Desenvolvimento | `anp_development_fields.xlsx` |

### Data collected

**Exploratory Phase** — contract blocks under exploration: operator, basin, area, contractual deadlines, drilled wells, committed work units.

**Well Interventions** — drilling interventions: well names (ANP and operator), field, basin, probe, objective, start/end dates, days in intervention.

**Development Fields** — fields in production development: field, basin, operator, environment, contract details, water depth, status, production dates, field classification.

---

## Requirements

- Python 3.8+
- Google Chrome (latest)
- ChromeDriver is managed automatically via `webdriver-manager`

---

## Setup

```bash
# Clone the repository
git clone https://github.com/raphaellasoalves/anp-data-crawlers.git
cd anp-data-crawlers

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

Run each crawler individually:

```bash
python crawlers/exploratory_phase.py
python crawlers/well_interventions.py
python crawlers/development_fields.py
```

Output files are saved to the `output/` folder (created automatically on first run).

> **Note:** The crawlers open a Chrome browser window and interact with the Power BI interface. Execution time varies depending on table size and network speed.

---

## Why crawlers?

The ANP Power BI panels do not offer a native data export or download option. The data is only accessible through the interactive interface, with no API or downloadable file available. These crawlers were built to fill that gap, enabling the extraction of structured data for analysis and integration into data pipelines.

---

## How it works

The ANP panels are hosted on Power BI Embedded, which renders data as virtualized DOM tables — meaning only the visible rows and columns exist in the HTML at any given moment. Standard scraping approaches (requests + BeautifulSoup) do not work here.

These crawlers use **Selenium** to:
1. Navigate to the public Power BI URL
2. Locate and enter focus mode on the target table
3. Scroll the table systematically — both vertically and horizontally — collecting all visible cells at each step
4. Deduplicate and pivot the collected cells into a structured DataFrame
5. Export the result to Excel

Horizontal scroll is handled by detecting and dragging the Power BI scrollbar handle, with stale element recovery and end-of-table detection based on container position tracking.

---

## Data source

All data is publicly available through ANP's official BI panels:
[https://www.gov.br/anp/pt-br](https://www.gov.br/anp/pt-br)

---

## Author

**Raphaella Alves** — Data Analyst & Data Engineer  
[LinkedIn](https://linkedin.com/in/raphaella-alves-a44ab047) · [GitHub](https://github.com/raphaellasoalves)
