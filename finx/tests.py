import requests
import time
import os
import json

# File-based caching system
CACHE_FILE = "daily_exchange_rate_cache.json"
CACHE_EXPIRATION = 12 * 60 * 60  # 12 hours (in seconds)

def load_cache():
    """
    Load the cache from the file if it exists.
    """
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as file:
            cache_data = json.load(file)
            return cache_data
    return {}

def save_cache(cache_data):
    """
    Save the cache data to a file.
    """
    with open(CACHE_FILE, "w") as file:
        json.dump(cache_data, file)

def fetch_exchange_rates(base_currency="USD", api_key="bb8ea1368774d09c283fe82107218c99"):
    """
    Fetches currency exchange rates with a limit of two requests per day.
    
    Args:
        base_currency (str): The base currency for exchange rates. Default is 'USD'.
        api_key (str): Your API access key.
    
    Returns:
        dict: A dictionary containing exchange rates or an error message.
    """
    cache = load_cache()
    current_time = time.time()

    # Check if rates are cached and still valid
    if base_currency in cache:
        cached_data = cache[base_currency]
        if current_time - cached_data["timestamp"] < CACHE_EXPIRATION:
            print("Using cached exchange rates.")
            return cached_data["rates"]

    # Fetch new data from the API
    url = "https://api.exchangerate.host/latest"
    try:
        response = requests.get(url, params={"base": base_currency, "access_key": api_key})
        response.raise_for_status()
        data = response.json()

        if data.get("success", False):
            # Save rates to cache
            cache[base_currency] = {
                "rates": data["rates"],
                "timestamp": current_time
            }
            save_cache(cache)
            print("Fetched new exchange rates from the API.")
            return data["rates"]
        else:
            return {"error": data.get("error", {}).get("info", "Unknown error occurred.")}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# Example usage
if __name__ == "__main__":
    rates = fetch_exchange_rates("USD")
    if "error" in rates:
        print("Error:", rates["error"])
    else:
        print("Exchange rates relative to USD:")
        for currency, rate in rates.items():
            print(f"{currency}: {rate}")
