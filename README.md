# Glamping Market Research AI

An AI-powered market research platform for campground and glamping investments.

**[→ Try the live app](https://terrainintelligence.streamlit.app/)** Analyzes property addresses, scrapes comparable listings, estimates pricing and occupancy, and generates full investment reports—all running locally with free tools.

## Features

- **Property Analysis**: Analyze any address for glamping/campground investment potential
- **Multi-Source Scraping**: Airbnb, Hipcamp, GlampingHub, Google Maps, Zillow, Redfin
- **Pricing & Occupancy Models**: AI-estimated nightly rates and occupancy
- **Financial Projections**: ROI, NPV, IRR, 10-year revenue forecast
- **RAG Document Context**: Upload zoning docs, reports—agents use them as context
- **Land Investment Finder**: Scout properties by county/state, ranked by ROI potential
- **Export**: Markdown and PDF reports

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
4. View comparables map, pricing distribution, expense breakdown, ROI timeline
5. Download report as Markdown or PDF

### Land Investment Finder Tab

1. Enter county, state, budget range, minimum acreage
2. Click **Find Properties**
3. Results are ranked by estimated ROI
4. View table and map

## Workflow: Agents, LLMs & Browserbase

### Agent Pipeline (LangGraph)

The **Market Analysis** flow runs a linear LangGraph pipeline with 6 agents:

```
┌─────────────┐    ┌───────────┐    ┌────────────┐    ┌──────────┐    ┌───────────┐    ┌────────┐
│  Research   │───▶│  Pricing  │───▶│ Occupancy  │───▶│ Expense  │───▶│ Financial │───▶│ Report │
│   Agent     │    │   Agent   │    │   Agent    │    │  Agent   │    │   Agent   │    │ Agent  │
└─────────────┘    └───────────┘    └────────────┘    └──────────┘    └───────────┘    └────────┘
       │                  │                │                │                │               │
       ▼                  ▼                ▼                ▼                ▼               ▼
  Scrapes           Computes          Estimates         Estimates        ROI, NPV,      LLM writes
  comparables       nightly rate      occupancy %       expenses         IRR, 10yr      recommendation
```

| Agent | Role | Uses LLM? |
|-------|------|------------|
| **Research** | Scrapes comparable listings from Airbnb, Hipcamp, GlampingHub, Google Maps, Zillow, Redfin | No |
| **Pricing** | Computes recommended nightly rate from comparables | No |
| **Occupancy** | Estimates occupancy % from market signals | No |
| **Expense** | Estimates operating expenses (cleaning, taxes, insurance, etc.) | No |
| **Financial** | Computes ROI, NPV, IRR, payback period, 10-year projection | No |
| **Report** | Assembles full Markdown report and generates investment recommendation | **Yes** (Ollama) |

The **Land Investment Finder** uses a separate agent:

| Agent | Role | Uses LLM? |
|-------|------|------------|
| **Property Scout** | Scrapes LandWatch, Zillow, Redfin for land listings; ranks by estimated ROI | No |

### LLMs

| Model | Purpose |
|-------|---------|
| **Ollama `llama3.2`** (configurable via `OLLAMA_MODEL`) | Report agent: writes 2–3 sentence investment recommendations based on ROI, payback, NPV |
| **Ollama `nomic-embed-text`** (configurable via `OLLAMA_EMBEDDING_MODEL`) | RAG: embeds uploaded documents for ChromaDB; retrieved context is passed to the pipeline and included in reports |

### Browserbase vs Local Playwright

Both the **Research** and **Property Scout** agents need a browser to scrape sites. The app chooses the browser backend at runtime:

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
2. **RAG** (if docs uploaded): `nomic-embed-text` embeds files → ChromaDB stores vectors → retriever fetches relevant chunks → `doc_context` passed into pipeline.
3. **Research agent** gets a page from `get_browser_manager()` → runs 6 scrapers (Airbnb, Hipcamp, etc.) → outputs `comparables`.
4. **Pricing → Occupancy → Expense → Financial** agents run deterministic models on the state.
5. **Report agent** builds Markdown report and calls Ollama (`llama3.2`) for the investment recommendation.
6. **User** sees report, map, charts; can export Markdown/PDF.

## Project Structure

```
TerrainIntelligence/
├── backend/
│   ├── agents/          # LangGraph agents
│   ├── scrapers/        # Playwright + BeautifulSoup scrapers
│   ├── analysis/        # Pricing, occupancy, financial models
│   ├── rag/             # Document loader, ChromaDB, retriever
│   └── browser/         # Browserbase / local Playwright manager
├── frontend/
│   └── app.py           # Streamlit UI
├── data/
│   ├── cache/           # Cached scrape results
│   ├── comparables/
│   ├── reports/
│   └── chroma_db/       # Vector store
├── config.py
├── requirements.txt
└── run.py
```

## Performance Notes

- **Caching**: Scraped results are cached in `data/cache/` to avoid repeated requests
- **Mock Data**: If a scraper fails (rate limits, structure changes), mock/sample data is returned so the pipeline continues
- **Browserbase**: Use Browserbase for more reliable scraping; local Playwright works but may hit anti-bot measures

## Limitations

- Scrapers depend on website structure; sites change and may break
- Geocoding for maps uses placeholders; add geopy for real coordinates
- Financial estimates use industry heuristics; validate with professionals

## License

MIT
