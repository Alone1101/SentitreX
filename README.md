# SentitreX: Real-Time Market Sentiment Correlation Engine
**Coursework:** COMP3207 Cloud Application Development  
**Target Asset:** SOXL (Semiconductor ETF)

## 1. Overview
SentitreX is an automated cloud-native tool that correlates Alpha Vantage news sentiment with SOXL market volatility. It uses a serverless architecture to ensure scalability and cost-efficiency.

## 2. Prerequisites
Before running the project, you **must** install the following:
* **Python 3.10+**
* **Azure Functions Core Tools v4** (Install via MSI, not npm)
* **VS Code Extensions:**
    * Python (Microsoft)
    * Azure Functions (Microsoft)
    * Azurite (Local Storage Emulator)

## 3. Local Setup & Installation

### Step 1: Virtual Environment
```powershell
python -m venv .venv
.\.venv\bin\Activate.ps1  # Note: Use 'bin' if on Git Bash/Unix, 'Scripts' if on standard CMD
pip install -r requirements.txt