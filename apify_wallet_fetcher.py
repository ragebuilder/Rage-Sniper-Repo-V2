import os
from apify_client import ApifyClient

def fetch_wallets():
    api_token = os.getenv("apify_api_token")
    client = ApifyClient(api_token)

    run_input = {
        "chain": "sol",
        "traderType": "all",
        "sortBy": "profit_7days",
        "sortDirection": "desc",
        "proxyConfiguration": {"useApifyProxy": True},
    }

    run = client.actor("jgxPNaFu0r4jDOXD1").call(run_input=run_input)
    wallets = [item['walletAddress'] for item in client.dataset(run["defaultDatasetId"]).iterate_items()]
    return wallets
