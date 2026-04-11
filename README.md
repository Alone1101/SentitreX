# SentitreX: Real-Time Market Sentiment Correlation Engine

**Coursework:** COMP3207 Cloud Application Development  
**Target Asset:** SOXL (Semiconductor ETF)  
**Status:** 🟢 **Production Live**

SentitreX is a cloud-native tool that correlates Alpha Vantage news sentiment with SOXL market volatility. It uses a serverless Azure Functions backend for ingestion and a Streamlit dashboard for real-time visualization.

---

## 1. Live Environment

The SentitreX ecosystem is fully deployed in the **Azure Malaysia West** region using a serverless architecture.

* **Production Dashboard:** [https://sentitrex-web-crgsc0d5bve4d8e2.malaysiawest-01.azurewebsites.net]
* **API Gateway:** `https://sentitrex-api-bmf6dvdchabkcedx.malaysiawest-01.azurewebsites.net/api`

---

## 2. Cloud Architecture

SentitreX uses a decoupled, serverless microservices architecture designed for high availability and zero-trust security.

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Streamlit (Azure App Service, Linux) | Python-based UI for real-time data visualization. |
| **Backend** | Azure Functions (Python 3.10) | Serverless REST API and automated data scrapers. |
| **Database** | Azure Cosmos DB (NoSQL) | Document store for news sentiment and price history; partition key strategy on `/ticker`. |
| **Security** | Azure Key Vault | Managed identity–based secret injection (no plaintext secrets in code). |
| **Auth** | JWT + bcrypt | Secure user registration and tokenized session management. |
| **Monitoring** | Application Insights | Real-time telemetry and log aggregation. |

---

## 3. Developer Setup (Local Evaluation)

### Prerequisites

* Python 3.10+
* Azure Functions Core Tools v4
* Azurite (local storage emulator)

### Local configuration

Create a `local.settings.json` in the project root. **Note:** In production, secrets are handled via Key Vault. For local runs, use your own placeholders (or a dev Key Vault URI if configured).

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

### Execution

**Virtual environment**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Storage emulator:** Before starting the backend, run Azurite so Azure Functions can use local storage and timers. In VS Code: **Ctrl+Shift+P** → **Azurite: Start**.

**Two terminals**

1. **Backend:** `func start`
2. **Frontend:** `streamlit run app.py` (with the virtual environment activated)

---

## 4. Production Implementation & Security

* **Managed identities:** System-assigned managed identities on the App Service and Function App with **Key Vault Secrets User** roles, avoiding hardcoded credentials.
* **Network security:** CORS restricted to the production frontend domain to reduce unauthorized API use.
* **Port mapping:** The web app uses `WEBSITES_PORT=8000` so Streamlit aligns with the Azure load balancer.
* **Automated ingestion:**
  * **Sentiment scraper:** Hourly timer trigger for Alpha Vantage news.
  * **Price scraper:** Periodic snapshots via yfinance with weekend and market-close error handling.
* **Data integrity:** News articles are hashed (MD5) to avoid duplicate documents in the Cosmos DB `newsArticles` container.
* **API protection:** Endpoints such as `/news` and `/prices` expect Bearer JWT validation where applicable.
