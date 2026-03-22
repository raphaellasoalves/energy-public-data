# ANP Public Data Crawlers

Automated data collection from the **ANP (Agência Nacional do Petróleo, Gás Natural e Biocombustíveis)** public Power BI dashboards.

These crawlers extract structured tabular data from ANP's interactive panels and export them as `.xlsx` files for further analysis.

---

## Crawlers

| Script | Panel | Output |
|--------|-------|--------|
| `exploratory_phase.py` | Painel Fase de Exploração — Blocos sob Contrato | `anp_blocks_under_contract.xlsx` |
| `well_interventions.py` | Painel Intervenção em Poços (filter: Perfuração) | `anp_well_interventions.xlsx` |
| `development_fields.py` | BI ANP — Campos em Desenvolvimento | `anp_development_fields.xlsx` |

---

## How it works

The ANP dashboards are hosted on Power BI embedded (public access). Since the data is rendered inside a virtualized grid — meaning only visible rows and columns are loaded in the DOM at any given time — a standard HTML scraper cannot capture the full dataset.

These crawlers use **Selenium** to simulate user interaction: scrolling vertically and horizontally across the table, collecting visible cells at each step, and assembling the complete dataset from the accumulated snapshots.

---

## Requirements

- Python 3.9+
- Google Chrome installed
- ChromeDriver is managed automatically via `webdriver-manager`

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage

Run any crawler directly from the project root:

```bash
python crawlers/exploratory_phase.py
python crawlers/well_interventions.py
python crawlers/development_fields.py
```

Output files are saved to the `output/` folder (created automatically if it doesn't exist).

---

## Data sources

All data is publicly available via ANP's official Power BI portal:

- [ANP — Painel Fase de Exploração](https://www.gov.br/anp/pt-br)
- [ANP — Intervenção em Poços](https://www.gov.br/anp/pt-br)
- [ANP — Campos em Desenvolvimento](https://www.gov.br/anp/pt-br)

---

## Author

**Raphaella Alves**  
Data Analyst & Data Engineer  
[LinkedIn](https://linkedin.com/in/raphaella-alves-a44ab047)
