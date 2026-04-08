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
    "ALPHA_VANTAGE_KEY": "YOUR_API_KEY",
    "CosmosDbConnectionString": "YOUR_COSMOS_CONNECTION_STRING",
    "JWT_SECRET": "CHANGE_ME_TO_A_LONG_RANDOM_SECRET"
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