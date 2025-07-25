import os
from apify_client import ApifyClient

def fetch_wallets():
    api_token = os.getenv("apify_api_token")
    if not api_token:
        print("[ERROR] No Apify API token found in environment variables.")
        return []

    try:
        client = ApifyClient(api_token)

        run_input = {
            "chain": "sol",
            "traderType": "all",
            "sortBy": "profit_7days",
            "sortDirection": "desc",
            "proxyConfiguration": {"useApifyProxy": True},
        }

        print("[INFO] Fetching smart wallets from Apify...")
        run = client.actor("jgxPNaFu0r4jDOXD1").call(run_input=run_input)
        wallets = []

        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            address = item.get("wallet_address") or item.get("walletAddress") or item.get("address")
            if address:
                print("[DEBUG] Item fetched:", item)
                wallets.append(address)

        print(f"[INFO] Retrieved {len(wallets)} wallets from Apify.")
        return wallets

    except Exception as e:
        print(f"[ERROR] Apify fetch failed: {e}")
        return []
