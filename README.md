# SentitreX: Real-Time Market Sentiment Correlation Engine

**Coursework:** COMP3207 Cloud Application Development  
**Target Asset:** SOXL (Semiconductor ETF)

## 1. Overview

SentitreX is an automated cloud-native tool that correlates Alpha Vantage news sentiment with SOXL market volatility. It uses a serverless Azure Functions architecture for data ingestion and a Streamlit dashboard for real-time visualization.

## 2. Prerequisites

Before running the project, you **must** install the following:

- **Python 3.10+**
- **Azure Functions Core Tools v4** (install via MSI, not npm)
- **VS Code Extensions:**
  - Python (Microsoft)
  - Azure Functions (Microsoft)
  - Azurite (Local Storage Emulator)

## 3. Local Setup & Installation

### Step 1: Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 2: Environment Variables

Create a `local.settings.json` file in the root directory to store your API keys securely (**do not commit this file to Git**):

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "KEY_VAULT_URL": "https://sentitrex-keyvault.vault.azure.net/"
  }
}
```

Optional (Streamlit): you can override the backend URL via `SENTITREX_API_BASE_URL` (defaults to `http://localhost:7071/api`).

## 4. How to Run Locally

Before starting the backend, you must start the local storage emulator so the Azure Functions can track their timers.

In VS Code, press Ctrl + Shift + P to open the Command Palette, then type Azurite: Start and press Enter

This project runs the backend data ingestion and frontend UI simultaneously. You will need two terminal windows open in VS Code.

### Terminal 1: Start the Backend (Azure Functions)

```powershell
func start
```

### Terminal 2: Start the Frontend (Streamlit Dashboard)

Make sure your virtual environment is activated, then run:

```powershell
streamlit run app.py
```

## 5. Cloud Architecture & Tech Stack

SentitreX leverages a decoupled, serverless microservices architecture:

- **Compute:** Azure Functions (Serverless Python backend)
- **Database:** Azure Cosmos DB (NoSQL Document Store)
- **Security:** Azure Key Vault (Managed Identity secret injection) & bcrypt/JWT authentication
- **Frontend:** Streamlit (Python-based data visualization)
- **Monitoring:** Azure Application Insights

## 6. Security Implementation

- **Azure Key Vault:** No plain-text credentials exist in the codebase. All connection strings and API keys are fetched dynamically at runtime via Azure Managed Identities.
- **Authentication:** Users are securely registered with `bcrypt` password hashing.
- **Authorization:** API endpoints (`/news`, `/prices`) are protected via stateless JSON Web Tokens (JWT) requiring Bearer token validation.