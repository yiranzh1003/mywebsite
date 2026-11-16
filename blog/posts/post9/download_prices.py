"""Download the original script's Yahoo Finance price fields."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parent


def fetch(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5y"
    with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as response:
        result = json.load(response)["chart"]["result"][0]
    fields = result["indicators"]
    prices = pd.DataFrame(fields["quote"][0])
    prices["symbol"] = symbol
    prices["date"] = pd.to_datetime(result["timestamp"], unit="s", utc=True).tz_convert(
        "America/New_York").date
    prices["adjusted"] = fields["adjclose"][0]["adjclose"]
    return prices[prices.date.astype(str).between("2022-01-01", "2026-11-13")]


def main():
    tickers = (ROOT / "data/tickers.txt").read_text().split()
    result, failed = [], {}
    with ThreadPoolExecutor(max_workers=6) as workers:
        for ticker, task in [(t, workers.submit(fetch, t)) for t in tickers]:
            try:
                result.append(task.result())
            except Exception as error:
                failed[ticker] = str(error)
    if failed:
        raise RuntimeError(f"Price downloads failed: {failed}")
    prices = pd.concat(result, ignore_index=True).sort_values(["symbol", "date"])
    prices.to_csv(ROOT / "data/prices.csv", index=False)
    print(prices.date.min(), prices.date.max(), len(prices))


if __name__ == "__main__":
    main()
