import re
import azure.functions as func
import logging
import requests
import datetime
import os
import hashlib
import bcrypt
import json
import uuid
import jwt
import yfinance as yf
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

app = func.FunctionApp()

# Key vault setup
KEY_VAULT_URL = os.getenv("KEY_VAULT_URL")
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential) if KEY_VAULT_URL else None

def _get_jwt_secret() -> str:
    if secret_client:
        return secret_client.get_secret("JWT-SECRET").value
    raise ValueError("KEY_VAULT_URL is not configured.")

def _require_jwt(req: func.HttpRequest) -> dict:
    auth_header = req.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise PermissionError("Missing or invalid Authorization header.")

    token = auth_header[len("Bearer ") :].strip()
    if not token:
        raise PermissionError("Missing bearer token.")

    secret_key = _get_jwt_secret()
    return jwt.decode(token, secret_key, algorithms=["HS256"])

def _get_cosmos_container(container_name: str):
    if not secret_client:
        raise ValueError("KEY_VAULT_URL is not configured.")

    conn_str = secret_client.get_secret("COSMOS-CONNECTION-STRING").value
    from azure.cosmos import CosmosClient
    client = CosmosClient.from_connection_string(conn_str)
    database = client.get_database_client("sentitrex-market-db")
    return database.get_container_client(container_name)

# Changed schedule to every hour at minute 0, second 0
@app.timer_trigger(schedule="0 0 * * * *", arg_name="mytimer", run_on_startup=True)
@app.cosmos_db_output(arg_name="outputDocument", 
                      database_name="sentitrex-market-db", 
                      container_name="newsArticles", 
                      connection="CosmosDbConnectionString")
def sentiment_scraper(mytimer: func.TimerRequest, outputDocument: func.Out[func.Document]) -> None:
    if not secret_client:
        raise ValueError("KEY_VAULT_URL is not configured.")
    
    api_key = secret_client.get_secret("ALPHA-VANTAGE-KEY").value
    symbol = "SOXL"
    
    # Time filter
    # Calculate cutoff for the last 24 hours in Alpha Vantage format: YYYYMMDDTHHMM
    time_limit = (datetime.datetime.utcnow() - datetime.timedelta(hours=24)).strftime("%Y%m%dT%H%M")
    
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&time_from={time_limit}&apikey={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        news_items = data.get("feed", [])
        
        if not news_items:
            logging.warning(f"No fresh news items found for {symbol} in the last 24h.")
            return

        processed_articles = []
        for article in news_items:
            # Relevance filter
            ticker_sentiment = article.get("ticker_sentiment", [])
            relevance = next((float(t.get("relevance_score", 0)) for t in ticker_sentiment if t.get("ticker") == symbol), 0)

            # Skip articles where SOXL is a minor mention
            if relevance < 0.4:
                continue

            # Idempotency & Data integrity
            raw_url = article.get("url", "")
            # Generate MD5 hash of URL to prevent duplicate entries 
            safe_id = hashlib.md5(raw_url.encode('utf-8')).hexdigest() if raw_url else "unknown-id"

            doc = {
                "id": safe_id,
                "articleId": safe_id,
                "ticker": symbol,
                "sourceName": article.get("source"),
                "title": article.get("title"),
                "articleUrl": raw_url,
                "publishedAt": article.get("time_published"), # Use actual news time for correlation
                "sentiment": {
                    "sentimentScore": float(article.get("overall_sentiment_score", 0)),
                    "relevanceScore": relevance,
                    "sentimentLabel": article.get("overall_sentiment_label"),
                    "sentimentTimestamp": datetime.datetime.utcnow().isoformat()
                }
            }
            processed_articles.append(func.Document.from_dict(doc))
        
        if processed_articles:
            # Batch save to Cosmos DB via output binding
            outputDocument.set(processed_articles)
            logging.info(f"Successfully saved {len(processed_articles)} relevant news articles.")

    except Exception as e:
        logging.error(f"Error during sentiment scraping: {str(e)}")

# Changed schedule to every 5 minutes per hour, second 30
@app.timer_trigger(schedule="30 0/12 * * * *", arg_name="mytimer", run_on_startup=True)
@app.cosmos_db_output(arg_name="outputDocument", 
                      database_name="sentitrex-market-db", 
                      container_name="priceSnapshots", 
                      connection="CosmosDbConnectionString")
def price_scraper(mytimer: func.TimerRequest, outputDocument: func.Out[func.Document]) -> None:
    import yfinance as yf
    import datetime
    import logging

    # Force the scraper to wait 10 seconds, even if Azure triggers it instantly
    logging.info("Price scraper triggered. Fetching from yfinance...")
    
    symbol = "SOXL"
    
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d")
        
        if hist.empty:
            logging.warning("No price data found via yfinance. (Market might be closed or on holiday)")
            return
        
        hist = hist.dropna(subset=['Close'])
        hist = hist[hist['Close'] > 0.01] 
        
        # Double check that we still have data after filtering
        if hist.empty:
            logging.warning("All recent price data was invalid (0.0 or NaN).")
            return
        
        latest = hist.iloc[-1]

        now_str = datetime.datetime.utcnow().isoformat()
        safe_id = f"{symbol}-{now_str}".replace(":", "-").replace(".", "-")

        doc = {
            "id": safe_id,
            "ticker": symbol,
            "priceTimestamp": now_str,
            "openPrice": float(latest["Open"]),
            "highPrice": float(latest["High"]),
            "lowPrice": float(latest["Low"]),
            "closePrice": float(latest["Close"]),
            "volume": int(latest["Volume"])
        }
        
        outputDocument.set(func.Document.from_dict(doc))
        logging.info(f"Successfully saved price snapshot for {symbol}: ${doc['closePrice']}")

    except Exception as e:
        logging.error(f"Error during price scraping: {str(e)}")

@app.route(route="register", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def register_user(req: func.HttpRequest) -> func.HttpResponse:
    import logging
    logging.info('Processing user registration request.')
    
    try:
        # 1. Grab the JSON data
        req_body = req.get_json()
        email = req_body.get('email')
        password = req_body.get('password')
        full_name = req_body.get('fullName', 'New User')
        role = "user"

        if not email or not password:
            return func.HttpResponse(
                json.dumps({"error": "Email and password are required."}), 
                status_code=400, 
                mimetype="application/json"
            )

        # Check email format using regex
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            return func.HttpResponse(
                json.dumps({"error": "Invalid email format."}), 
                status_code=400, 
                mimetype="application/json"
            )
            
        # Check password strength
        if len(password) < 8:
            return func.HttpResponse(
                json.dumps({"error": "Password must be at least 8 characters long."}), 
                status_code=400, 
                mimetype="application/json"
            )

        # 2. Connect to Cosmos DB
        container = _get_cosmos_container("users")

        # 3. Check if email already exists
        query = "SELECT * FROM c WHERE c.email = @email"
        parameters = [{"name": "@email", "value": email}]
        existing_users = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))

        if len(existing_users) > 0:
            return func.HttpResponse(
                json.dumps({"error": "Email already registered."}), 
                status_code=409, 
                mimetype="application/json"
            )

        # 4. Hash the password with bcrypt
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

        # 5. Generate IDs and Timestamps
        new_id = f"user-{str(uuid.uuid4())[:8]}"
        now_str = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # 6. Build the JSON document
        user_doc = {
            "id": new_id,
            "UserID": new_id,
            "fullName": full_name,
            "email": email,
            "passwordHash": hashed_password,
            "role": role,
            "createdAt": now_str,
            "lastLoginAt": None,
            "dashboardViews": []
        }
        
        container.create_item(user_doc)

        return func.HttpResponse(
            json.dumps({"message": f"Successfully registered: {email}", "userId": new_id, "role": role}), 
            status_code=201, 
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error during registration."}), 
            status_code=500, 
            mimetype="application/json"
        )

@app.route(route="login", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def login_user(req: func.HttpRequest) -> func.HttpResponse:
    import logging
    logging.info('Processing user login request.')
    
    try:
        # 1. Grab credentials from the request
        req_body = req.get_json()
        email = req_body.get('email')
        password = req_body.get('password')

        if not email or not password:
            return func.HttpResponse(
                json.dumps({"error": "Email and password are required."}), 
                status_code=400, 
                mimetype="application/json"
            )

        # 2. Connect to Cosmos DB
        container = _get_cosmos_container("users")

        # 3. Find the user by email
        query = "SELECT * FROM c WHERE c.email = @email"
        parameters = [{"name": "@email", "value": email}]
        users = list(container.query_items(
            query=query, 
            parameters=parameters, 
            enable_cross_partition_query=True
        ))

        # If email not found, return generic error
        if len(users) == 0:
            return func.HttpResponse(
                json.dumps({"error": "Invalid credentials."}), 
                status_code=401, 
                mimetype="application/json"
            )
        
        user = users[0]

        # 4. Verify the password using bcrypt
        if not bcrypt.checkpw(password.encode('utf-8'), user['passwordHash'].encode('utf-8')):
             return func.HttpResponse(
                 json.dumps({"error": "Invalid credentials."}), 
                 status_code=401, 
                 mimetype="application/json"
             )

        # 5. Mint the JWT if passwords match
        secret_key = _get_jwt_secret()
        
        # Grab UserID
        user_id = user.get('UserID') 
        
        payload = {
            "UserID": user_id,
            "role": user.get('role', 'user'),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24) # Token expires in 24 hours
        }
        
        # Generate the encoded token string
        token = jwt.encode(payload, secret_key, algorithm="HS256")

        # 6. Send the token back to the frontend
        return func.HttpResponse(
            json.dumps({
                "message": "Login successful", 
                "token": token, 
                "role": user.get('role'),
                "userId": user_id
            }), 
            status_code=200, 
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error during login."}), 
            status_code=500, 
            mimetype="application/json"
        )

@app.route(route="news", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def get_news(req: func.HttpRequest) -> func.HttpResponse:
    try:
        _require_jwt(req)

        news_container = _get_cosmos_container("newsArticles")
        query = """
            SELECT TOP 200
                c.title,
                c.sourceName,
                c.publishedAt,
                c.articleUrl,
                c.sentiment.sentimentScore,
                c.sentiment.sentimentLabel
            FROM c
            WHERE c.ticker = 'SOXL'
            ORDER BY c.publishedAt DESC
        """
        items = list(
            news_container.query_items(
                query=query,
                enable_cross_partition_query=False,
                partition_key="SOXL",
            )
        )

        return func.HttpResponse(
            json.dumps(items),
            status_code=200,
            mimetype="application/json",
        )
    except PermissionError:
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=401,
            mimetype="application/json",
        )
    except jwt.ExpiredSignatureError:
        return func.HttpResponse(
            json.dumps({"error": "Token expired"}),
            status_code=401,
            mimetype="application/json",
        )
    except jwt.InvalidTokenError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid token"}),
            status_code=401,
            mimetype="application/json",
        )
    except Exception as e:
        logging.error(f"get_news error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )

@app.route(route="prices", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def get_prices(req: func.HttpRequest) -> func.HttpResponse:
    try:
        _require_jwt(req)

        price_container = _get_cosmos_container("priceSnapshots")
        query = """
            SELECT TOP 500
                c.priceTimestamp,
                c.openPrice,
                c.highPrice,
                c.lowPrice,
                c.closePrice,
                c.volume
            FROM c
            WHERE c.ticker = 'SOXL'
            ORDER BY c.priceTimestamp ASC
        """
        items = list(
            price_container.query_items(
                query=query,
                enable_cross_partition_query=False,
                partition_key="SOXL",
            )
        )

        return func.HttpResponse(
            json.dumps(items),
            status_code=200,
            mimetype="application/json",
        )
    except PermissionError:
        return func.HttpResponse(
            json.dumps({"error": "Unauthorized"}),
            status_code=401,
            mimetype="application/json",
        )
    except jwt.ExpiredSignatureError:
        return func.HttpResponse(
            json.dumps({"error": "Token expired"}),
            status_code=401,
            mimetype="application/json",
        )
    except jwt.InvalidTokenError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid token"}),
            status_code=401,
            mimetype="application/json",
        )
    except Exception as e:
        logging.error(f"get_prices error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )