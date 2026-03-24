import os
import time
import requests
_cached_rates = None
_cached_at = 0
CACHE_TTL = 3600  # 1 hour (tweak if needed)
from typing import Dict

def get_exchange_rates():
    global _cached_rates, _cached_at

    now = time.time()
    if _cached_rates and now - _cached_at < CACHE_TTL:
        return _cached_rates

    try:
        exchange_rates_key = os.getenv("EXCHANGE_RATES_API")
        url = f"http://api.exchangeratesapi.io/v1/latest?access_key={exchange_rates_key}"
        resp = requests.get(url, timeout=5)
        data = resp.json()

        gbp_per_eur = data["rates"]["GBP"]
        inr_per_eur = data["rates"]["INR"]

        inr_to_gbp = gbp_per_eur / inr_per_eur
        gbp_to_inr = inr_per_eur / gbp_per_eur

        _cached_rates = {
            "inr_to_gbp": inr_to_gbp,
            "gbp_to_inr": gbp_to_inr
        }
        _cached_at = now

    except Exception:
        # fallback to last known rates
        if _cached_rates:
            return _cached_rates
        raise Exception("Exchange rate service unavailable")

    return _cached_rates


def inr_to_gbp(amount_inr):
    rates = get_exchange_rates()
    return amount_inr * rates["inr_to_gbp"]


def gbp_to_inr(amount_gbp):
    rates = get_exchange_rates()
    return amount_gbp * rates["gbp_to_inr"]