<div align="center">

# SentitreX
### Real-Time SOXL Sentiment & Price Intelligence

[![Live App](https://img.shields.io/badge/🟢%20Live%20App-Azure-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white)](https://sentitrex-web-crgsc0d5bve4d8e2.malaysiawest-01.azurewebsites.net)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/Alone1101/SentitreX/main_sentitrex-api.yml?style=for-the-badge&logo=githubactions&logoColor=white&label=CI%2FCD)](https://github.com/Alone1101/SentitreX/actions)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
![Status: Archive Only](https://img.shields.io/badge/Status-Archive%20Only-red)

*A cloud-native Business Intelligence engine that correlates institutional financial news sentiment with SOXL market volatility — automated, serverless, and live on Azure.*

</div>

---

## Tech Stack

<div align="center">

| Layer | Technology | Badge |
|---|---|---|
| **Frontend** | Streamlit on Azure App Service | ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white) ![Azure App Service](https://img.shields.io/badge/App%20Service-F1%20Tier-0078D4?style=flat-square&logo=microsoftazure&logoColor=white) |
| **Backend** | Azure Functions (Python v2) | ![Azure Functions](https://img.shields.io/badge/Azure%20Functions-Consumption%20Plan-0062AD?style=flat-square&logo=azurefunctions&logoColor=white) |
| **Database** | Azure Cosmos DB (NoSQL) | ![CosmosDB](https://img.shields.io/badge/Cosmos%20DB-NoSQL-003087?style=flat-square&logo=microsoftazure&logoColor=white) |
| **Secrets** | Azure Key Vault | ![Key Vault](https://img.shields.io/badge/Key%20Vault-Managed%20Identity-0078D4?style=flat-square&logo=microsoftazure&logoColor=white) |
| **Auth** | JWT + bcrypt | ![JWT](https://img.shields.io/badge/JWT-Auth-000000?style=flat-square&logo=jsonwebtokens&logoColor=white) |
| **Data Sources** | Alpha Vantage + yfinance | ![Alpha Vantage](https://img.shields.io/badge/Alpha%20Vantage-News%20Sentiment-1DB954?style=flat-square) ![yfinance](https://img.shields.io/badge/yfinance-Price%20Data-6001D2?style=flat-square) |
| **Monitoring** | Azure Application Insights | ![App Insights](https://img.shields.io/badge/Application%20Insights-Telemetry-68217A?style=flat-square&logo=microsoftazure&logoColor=white) |
| **CI/CD** | GitHub Actions | ![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-YAML%20Pipeline-2088FF?style=flat-square&logo=githubactions&logoColor=white) |
| **Region** | Azure Malaysia West | ![Region](https://img.shields.io/badge/Region-Malaysia%20West-0078D4?style=flat-square&logo=microsoftazure&logoColor=white) |

</div>

---

##  Live Environment

| Service | URL |
|---|---|
| **Production Dashboard** | [sentitrex-web-crgsc0d5bve4d8e2.malaysiawest-01.azurewebsites.net](https://sentitrex-web-crgsc0d5bve4d8e2.malaysiawest-01.azurewebsites.net) |
| **API Gateway** | `https://sentitrex-api-bmf6dvdchabkcedx.malaysiawest-01.azurewebsites.net/api` |

> ⚠️ **Note on Availability:** As this is a university course project, the live deployment links below may be temporarily paused or inaccessible due to Azure credit limitations or post-grading resource management.

---

## What It Does

SentitreX is a cloud-native BI engine that:

- **Ingests** institutional financial news from Alpha Vantage (hourly, 24×/day) and SOXL price data from yfinance (every 5 minutes, 288×/day)
- **Filters** out noise — only articles with a SOXL relevance score `> 0.4` are persisted
- **Stores** deduplicated JSON documents in Azure Cosmos DB using MD5-hashed article URLs as unique IDs, with a 90-day TTL policy
- **Visualises** a dual-axis Plotly candlestick + sentiment chart on a Streamlit dashboard secured by JWT authentication

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SentitreX Cloud                          │
│                                                                 │
│   ┌─────────────┐     HTTPS / JWT     ┌──────────────────────┐ │
│   │  Streamlit  │◄───────────────────►│  Azure Functions     │ │
│   │  App Service│  (REST API calls)   │  (HTTP Trigger)      │ │
│   │  (Frontend) │                     └──────────┬───────────┘ │
│   └─────────────┘                                │             │
│                                        ┌─────────▼──────────┐  │
│   ┌─────────────┐   Timer (Hourly)    │  Azure Functions   │  │
│   │Alpha Vantage│────────────────────►│  (Timer Trigger)   │  │
│   │    API      │                     └─────────┬──────────┘  │
│   └─────────────┘                               │             │
│                                                 ▼             │
│   ┌─────────────┐  Timer (5-min)    ┌───────────────────────┐ │
│   │  yfinance   │──────────────────►│   Azure Cosmos DB     │ │
│   │  (Yahoo)    │                   │  (newsArticles,       │ │
│   └─────────────┘                   │   priceSnapshots,     │ │
│                                     │   users containers)   │ │
│   ┌─────────────┐                   └───────────────────────┘ │
│   │  Key Vault  │◄── Managed Identity ──── All Functions      │
│   │ (Secrets)   │                                              │
│   └─────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

**Design Patterns used:** Event-Driven Serverless · Pipe-and-Filter · Decoupled Three-Tier (Presentation / Logic / Data)

---

## Azure Functions

| Function | Trigger | Schedule | Purpose |
|---|---|---|---|
| `sentiment_scraper` | Timer | `0 0 * * * *` (hourly) | Fetch & persist news sentiment from Alpha Vantage |
| `price_scraper` | Timer | Every 5 min | Fetch SOXL OHLCV snapshots via yfinance |
| `get_news` | HTTP GET | On demand | Return filtered sentiment data to frontend |
| `get_prices` | HTTP GET | On demand | Return price history to frontend |
| `login_user` | HTTP POST | On demand | Validate credentials, issue JWT |
| `register_user` | HTTP POST | On demand | Create bcrypt-hashed user account |

---

## Security

| Measure | Implementation |
|---|---|
| **Secrets management** | Azure Key Vault via System-Assigned Managed Identity — no hardcoded credentials |
| **Transport security** | HTTPS Only enforced on App Service (TLS 1.2+) |
| **Auth** | JWT session tokens + bcrypt password hashing |
| **Data at rest** | Cosmos DB Microsoft-managed encryption |
| **RBAC** | Anonymous → Auth page only · Trader → Dashboard + API · Scraper → Cosmos DB write · Admin → Full manage |
| **Idempotency** | MD5-hashed article URLs as Cosmos DB document IDs prevent duplicates |

---

## Data Strategy

| Parameter | Value |
|---|---|
| **Asset targeted** | SOXL (Direxion Daily Semiconductor Bull 3X ETF) |
| **News source** | Alpha Vantage (institutional news only, English-language) |
| **Sentiment calls/day** | 24 (stays within free tier 25-call limit) |
| **Price polling** | Every 5 min via yfinance (no quota limit) |
| **Relevance filter** | Articles with SOXL score `< 0.4` discarded |
| **Freshness filter** | 24-hour lookback window on every scraper run |
| **Data retention** | 90-day TTL on all containers (auto-purge) |
| **Partition key** | `/ticker` for sub-10ms query latency |

---

## Local Setup

### Prerequisites

```bash
Python 3.10+
Azure Functions Core Tools v4
Azurite (local storage emulator)
```

### Steps

```bash
# 1. Clone and activate environment
git clone https://github.com/Alone1101/SentitreX.git
cd SentitreX
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Windows
# source .venv/bin/activate       # macOS/Linux
pip install -r requirements.txt

# 2. Create local.settings.json (never commit this file)
```

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "KEY_VAULT_URL": "YOUR_KEY_VAULT_URI",
    "CosmosDbConnectionString": "YOUR_LOCAL_COSMOS_CONNECTION_STRING",
    "ALPHA-VANTAGE-KEY": "YOUR_API_KEY",
    "JWT-SECRET": "YOUR_LOCAL_SECRET"
  }
}
```

```bash
# 3. Start Azurite (VS Code: Ctrl+Shift+P → "Azurite: Start")

# 4. Terminal 1 — Backend
func start

# 5. Terminal 2 — Frontend
streamlit run app.py
```

---

## Monitoring

- **Azure Application Insights** — Server response time, failed requests, availability (tracked live)
- **Live Metrics Stream** — CPU, request rates, real-time execution logs (sub-second latency, no persistent alert cost)
- **Structured logs** — `INFO` / `WARNING` / `ERROR` levels piped to Application Insights Traces table

---

## Team

| Member | Contributions |
|---|---|
| **Wong Jin Xuan** | Report, Azure Functions backend, CI/CD pipeline, Key Vault, Application Insights, JWT/bcrypt auth |
| **Ng Kin Yew Dexter** | Azure subscriptions & IAM, Resource Group, Cosmos DB partitioning, ERD, Streamlit dashboard |
| **Seon Hong Kok Meng** | Use case diagrams, DFD, Streamlit dashboard UI, login & sign-up pages |

---

## Course

**COMP3207 – Cloud Application Development (UoSM) 2025/26**
University of Southampton Malaysia (UoSM)

---

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Azure](https://img.shields.io/badge/Microsoft%20Azure-0078D4?style=flat-square&logo=microsoftazure&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Cosmos DB](https://img.shields.io/badge/Cosmos%20DB-003087?style=flat-square&logo=microsoftazure&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat-square&logo=plotly&logoColor=white)

*Built with cloud on Microsoft Azure · Deployed in Malaysia West*

</div>
