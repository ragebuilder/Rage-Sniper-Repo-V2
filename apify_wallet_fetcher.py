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
        print("[DEBUG] Dataset ID:", run.get("defaultDatasetId"))

        wallets = []

        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            print("[DEBUG] Item fetched:", item)

            # Adjusted based on Apify dataset actual key
            address = item.get('trackedWalletAddress')  # Most likely correct key
            if address:
                wallets.append(address)

        print(f"[INFO] Retrieved {len(wallets)} wallets from Apify.")
        return wallets

    except Exception as e:
        print(f"[ERROR] Apify fetch failed: {e}")
        return []
