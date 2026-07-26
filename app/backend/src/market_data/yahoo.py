import httpx
import os
from datetime import datetime, timezone
from typing import Optional

YAHOO_HOSTS = [
    "https://query1.finance.yahoo.com",
    "https://query2.finance.yahoo.com",
]

TIMEFRAME_MAP = {
    "1D": ("1m", "1d"),
    "5D": ("1h", "5d"),
    "1M": ("1d", "1mo"),
    "1Y": ("1d", "1y"),
    "5Y": ("1wk", "5y"),
    "Max": ("1mo", "max"),
}


def _get_host() -> str:
    return os.getenv("YAHOO_FINANCE_HOST", YAHOO_HOSTS[0])


def _headers() -> dict:
    return {
        "User-Agent": "Mozilla/5.0 (compatible; TradingAssistant/1.0)",
        "Accept": "application/json",
    }


def fetch_chart(symbol: str, interval: str, range_: str) -> dict:
    url = f"{_get_host()}/v8/finance/chart/{symbol}?interval={interval}&range={range_}"
    with httpx.Client(timeout=15) as client:
        resp = client.get(url, headers=_headers())
        resp.raise_for_status()
        return resp.json()


def fetch_chart_period(symbol: str, interval: str, period1: int, period2: int) -> dict:
    url = (
        f"{_get_host()}/v8/finance/chart/{symbol}"
        f"?interval={interval}&period1={period1}&period2={period2}"
    )
    with httpx.Client(timeout=15) as client:
        resp = client.get(url, headers=_headers())
        resp.raise_for_status()
        return resp.json()


def _extract_series(payload: dict) -> list[dict]:
    chart = payload.get("chart") or {}
    results = chart.get("result") or []
    if not results:
        return []

    result = results[0]
    timestamps = result.get("timestamp") or []
    indicators = result.get("indicators") or {}
    quotes = indicators.get("quote") or []
    quote = quotes[0] if quotes else {}

    closes = quote.get("close") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []

    series = []
    for i, ts in enumerate(timestamps):
        close = closes[i] if i < len(closes) else None
        high = highs[i] if i < len(highs) else None
        low = lows[i] if i < len(lows) else None
        if close is None:
            continue
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        series.append({
            "date": dt.isoformat(),
            "price": round(float(close), 4),
            "high": round(float(high), 4) if high is not None else None,
            "low": round(float(low), 4) if low is not None else None,
        })
    return series


def get_price_history(symbol: str = "PEN=X", timeframe: str = "1M") -> list[dict]:
    interval, range_ = TIMEFRAME_MAP.get(timeframe, ("1d", "1mo"))
    payload = fetch_chart(symbol, interval, range_)
    return _extract_series(payload)


def get_latest_price(symbol: str = "PEN=X") -> Optional[float]:
    payload = fetch_chart(symbol, "1m", "5d")
    series = _extract_series(payload)
    if not series:
        return None
    return series[-1]["price"]
