# Glamping Market Research AI

An **autonomous AI research platform** for campground and glamping investments—similar to OpenAI Deep Research. Performs multi-step research, plans its own browsing actions, gathers and verifies sources, and iteratively improves results.

**[→ Try the live app](https://terrainintelligence.streamlit.app/)** Analyzes property addresses, scrapes comparable listings, estimates pricing and occupancy, and generates full investment reports—all running locally with free tools.

## Demo

A **Browserbase session recording** shows the Research agent scraping Airbnb, Hipcamp, and other sites during a market analysis run.

**View locally:**

```bash
# 1. Export the recording (requires BROWSERBASE_API_KEY in .env)
python scripts/fetch_session_recording.py

# 2. Serve the demo folder and open in a browser
cd demo && python -m http.server 8080
# Open http://localhost:8080/replay.html
```

**Or** view directly in the [Browserbase Dashboard](https://browserbase.com/sessions/81f0c1ba-c7fa-4c36-be58-d8efc37cbfc8) (requires a Browserbase account).

## Features

- **Autonomous Research Loop**: Planner → Browser → Verifier agents iterate until sufficient data or limit reached
- **Property Analysis**: Analyze any address for glamping/campground investment potential
- **Multi-Source Scraping**: Airbnb, Hipcamp, GlampingHub, Google Maps, Zillow, Redfin
- **Comparable Filtering**: Weighted similarity scoring (distance, unit type, amenities, rating, price); top 20 most similar
- **Tourism Demand Signals**: Review counts, attractions nearby, search popularity—adjusts occupancy estimates
- **Capacity Estimation**: Acreage-based unit limits (cabins 2–5/acre, glamping 4–8/acre, RV 6–10/acre, tent 8–15/acre); zoning from docs
- **Financial Scenarios**: Base, optimistic, and conservative cases with IRR, NPV, 10-year cash flow
- **Investment Score**: ROI + demand + competition + tourism weighted ranking
- **RAG Document Context**: Upload zoning docs—influences capacity, permitting risk, feasibility
- **Land Investment Finder**: Scout properties; runs full capacity + financial model; ranks by investment score
- **Export**: Markdown and PDF reports with automated source citations

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python |
| LLM | Ollama (local) or OpenAI (cloud) |
| Agent Framework | LangGraph |
| Browser | Playwright + Browserbase (optional) |
| Vector DB | ChromaDB |
| Embeddings | Ollama or OpenAI |
| UI | Streamlit |
| Charts | Plotly |

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai) installed and running

## Setup Instructions

### 1. Install Ollama

**macOS:**
```bash
brew install ollama
ollama serve  # or run from Applications
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
```

**Windows:** Download from [ollama.ai](https://ollama.ai)

### 2. Pull Ollama Models

```bash
# Main LLM for analysis and recommendations
ollama pull llama3.2

# Embeddings for RAG (document search)
ollama pull nomic-embed-text
```

### 3. Clone and Install Dependencies

```bash
cd TerrainIntelligence
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Install Playwright Browsers (for local scraping)

```bash
playwright install chromium
```

### 5. Configure Environment (Optional)

Copy `.env.example` to `.env` and set:

- **Browserbase** (optional): If `BROWSERBASE_API_KEY` and `BROWSERBASE_PROJECT_ID` are set, the app uses Browserbase remote browsers. Otherwise it falls back to local Playwright.

```env
BROWSERBASE_API_KEY=your_key
BROWSERBASE_PROJECT_ID=your_project_id
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### 6. Run the App

```bash
streamlit run frontend/app.py
```

Or:

```bash
python run.py
```

Open http://localhost:8501 in your browser.

**Quick test without browser:** Set `MOCK_SCRAPING=1` to use sample data instead of live scraping (useful when Playwright isn't installed or for testing).

## Deploy to Streamlit Community Cloud

**Live app:** [terrainintelligence.streamlit.app](https://terrainintelligence.streamlit.app/)

1. Push your repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app** → select your repo, branch `main`, and set **Main file path** to `frontend/app.py`.
4. Click **Deploy**. The app will build and launch.
5. **API keys**: Use the sidebar **Configure API Keys** to enter:
   - **OpenAI API Key** (required for AI recommendations on cloud) – get one at [platform.openai.com](https://platform.openai.com)
   - **Browserbase** (optional) – for live scraping instead of mock data
   - **Mock scraping** – check this when no Browserbase; uses sample data

On Streamlit Cloud, Ollama is not available. Use your OpenAI key for AI recommendations and document embeddings.

## Usage

### Market Analysis Tab

1. Enter property address, acreage, and unit counts (cabins, glamping, RV, tent sites)
2. Optionally upload PDF/DOCX/XLSX files (zoning, reports)
3. Click **Run Market Analysis**
4. View comparables map, price distribution, occupancy curve, financial scenarios, ROI timeline
5. Download report as Markdown or PDF

### Land Investment Finder Tab

1. Enter county, state, budget range, minimum acreage
2. Click **Find Properties**
3. Results are ranked by **investment score** (ROI + demand + capacity + risk)
4. View table and map

### Other Tabs

- **Comparables**: Top similar listings, map, price distribution histogram
- **Financial Model**: Base/optimistic/conservative scenarios, 10-year chart, ROI timeline, capacity estimate
- **Sources**: Research log, scraped sources, automated citations
- **Export & Cache**: CSV export of comparables

## Workflow: Agents, LLMs & Browserbase

### Autonomous Research Loop (LangGraph)

The **Market Analysis** flow uses an autonomous research loop that iterates until sufficient listings or max iterations:

```
  RESEARCH LOOP (Planner → Browser → Verifier, repeat until ≥15 listings or 3 iterations)
  ┌──────────┐     ┌───────────┐     ┌──────────┐
  │ Planner  │────▶│  Browser  │────▶│ Verifier │────┐
  └──────────┘     └───────────┘     └──────────┘    │
        ▲                 │                 │         │  done? ──▶ continue
        └─────────────────┴─────────────────┘         │
                                                      ▼
  DOWNSTREAM PIPELINE
  ┌───────────┐   ┌──────────┐   ┌────────┐   ┌───────────┐   ┌────────┐
  │  Pricing  │──▶│ Occupancy │──▶│ Expense │──▶│ Financial │──▶│ Report │
  └───────────┘   └──────────┘   └────────┘   └───────────┘   └────────┘
        │                │             │              │              │
        ▼                ▼             ▼              ▼              ▼
  Top 20 similar   Tourism + occ %  Operating    ROI, NPV, IRR   LLM writes
  comparables      seasonal curve  expenses    Scenarios       recommendation
```

| Agent | Role | Uses LLM? |
|-------|------|------------|
| **Planner** | Breaks research into tasks; decides which scrapers; creates research plan | No |
| **Browser** | Controls Playwright/Browserbase; runs scrapers; multi-step browsing | No |
| **Verifier** | Removes duplicates; cross-checks pricing; computes confidence_score, source_count | No |
| **Pricing** | Selects top 20 similar comparables; recommends nightly rate | No |
| **Occupancy** | Estimates occupancy %; gathers tourism demand signals; seasonal curve | No |
| **Expense** | Estimates operating expenses | No |
| **Financial** | ROI, NPV, IRR; base/optimistic/conservative scenarios; capacity estimate; investment score | No |
| **Report** | Full report with Tourism Demand, Capacity, Scenarios, Risk; source citations | **Yes** (Ollama) |

The **Land Investment Finder** uses a separate agent:

| Agent | Role | Uses LLM? |
|-------|------|------------|
| **Property Scout** | Scrapes LandWatch, Zillow, Redfin; runs capacity + financial model; ranks by investment score | No |

### Legacy Mode

To use the original single-step research agent: `run_analysis(prop_input, doc_context, use_autonomous_research=False)`

### LLMs

| Model | Purpose |
|-------|---------|
| **Ollama `llama3.2`** (configurable via `OLLAMA_MODEL`) | Report agent: writes 2–3 sentence investment recommendations based on ROI, payback, NPV |
| **Ollama `nomic-embed-text`** (configurable via `OLLAMA_EMBEDDING_MODEL`) | RAG: embeds uploaded documents for ChromaDB; retrieved context is passed to the pipeline and included in reports |

### Browserbase vs Local Playwright

The **Browser** agent (and **Property Scout**) need a browser to scrape sites. The app chooses the browser backend at runtime:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  get_browser_manager()                                                       │
│                                                                             │
│  BROWSERBASE_API_KEY + BROWSERBASE_PROJECT_ID set?                           │
│       │                                                                     │
│       ├── Yes ──▶ BrowserbaseManager                                        │
│       │              • Creates remote browser session via Browserbase API   │
│       │              • Playwright connects over CDP (session.connect_url)   │
│       │              • Scrapers run in cloud browser (better anti-bot)      │
│       │                                                                     │
│       └── No  ──▶ LocalPlaywrightManager                                    │
│                      • Launches local Chromium (headless)                   │
│                      • Scrapers run on your machine                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

- **Browserbase**: Remote, managed browsers. More reliable for scraping sites with anti-bot measures. Requires API key and project ID.
- **Local Playwright**: Runs Chromium locally. Free, but may hit rate limits or blocks on some sites.
- **Mock mode** (`MOCK_SCRAPING=1`): Skips real scraping; uses sample data so you can test without a browser.

### End-to-End Flow

1. **User** enters property address, unit counts, optionally uploads docs → Streamlit frontend.
2. **RAG** (if docs uploaded): `nomic-embed-text` embeds files → ChromaDB stores vectors → retriever fetches relevant chunks → `doc_context` passed into pipeline (influences capacity, permitting risk).
3. **Planner agent** creates research plan (Airbnb, Hipcamp, GlampingHub, Google Maps, Zillow, Redfin, tourism).
4. **Browser agent** runs scrapers; **Verifier agent** deduplicates, cross-checks, computes confidence. Loop until ≥15 listings or 3 iterations.
5. **Pricing** selects top 20 similar comparables; **Occupancy** uses tourism signals; **Expense** and **Financial** run models.
6. **Report agent** builds Markdown report and calls Ollama (`llama3.2`) for the investment recommendation.
7. **User** sees report, map, charts, financial scenarios; can export Markdown/PDF.

## Project Structure

```
TerrainIntelligence/
├── demo/               # Session recording replay (replay.html + session_recording.json)
├── scripts/            # Utilities (e.g. fetch_session_recording.py)
├── backend/
│   ├── agents/         # LangGraph agents (planner, browser, verifier, pricing, occupancy, etc.)
│   ├── scrapers/       # Playwright + BeautifulSoup scrapers
│   ├── analysis/       # Pricing, occupancy, financial models, comparable_filter, capacity_estimation, tourism_demand
│   ├── rag/            # Document loader, ChromaDB, retriever
│   ├── browser/        # Browserbase / local Playwright manager
│   └── logging_config.py  # Agent/research logging to data/research.log
├── frontend/
│   └── app.py          # Streamlit UI (6 tabs)
├── data/
│   ├── cache/          # Cached scrape results
│   ├── comparables/
│   ├── reports/
│   ├── chroma_db/      # Vector store
│   └── research.log    # Agent decisions and research steps
├── config.py
├── requirements.txt
└── run.py
```

## Performance Notes

- **Caching**: Scraped results are cached in `data/cache/` to avoid repeated requests
- **Mock Data**: If a scraper fails (rate limits, structure changes), mock/sample data is returned so the pipeline continues
- **Browserbase**: Use Browserbase for more reliable scraping; local Playwright works but may hit anti-bot measures
- **Logging**: Agent decisions and research steps are logged to `data/research.log` for debugging

## Limitations

- Scrapers depend on website structure; sites change and may break
- Geocoding for maps uses placeholders; add geopy for real coordinates
- Financial estimates use industry heuristics; validate with professionals

## License

MIT
