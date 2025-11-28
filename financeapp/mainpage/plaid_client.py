import os
import plaid
from plaid.api import plaid_api

from dotenv import load_dotenv
load_dotenv("/home/financeguru/apps/financeapp/.env")


PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox").lower()

if PLAID_ENV == "sandbox":
    host = plaid.Environment.Sandbox
elif PLAID_ENV == "development":
    host = plaid.Environment.Development
else:
    host = plaid.Environment.Production

configuration = plaid.Configuration(
    host=host,
    api_key={
        "clientId": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
    },
)

api_client = plaid.ApiClient(configuration)
plaid_client = plaid_api.PlaidApi(api_client)

