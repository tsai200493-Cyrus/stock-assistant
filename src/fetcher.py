import yfinance as yf
import pandas as pd


def fetch_stock_data(stock_code: str, period: str = "3mo") -> dict:
    ticker = yf.Ticker(f"{stock_code}.TW")
    hist = ticker.history(period=period)

    if hist.empty:
        raise ValueError(f"無法取得 {stock_code} 的資料，請確認股票代號是否正確")

    info = {}
    try:
        info = ticker.info
    except Exception:
        pass

    return {
        "code": stock_code,
        "name": info.get("longName") or info.get("shortName") or stock_code,
        "history": hist,
        "current_price": float(hist["Close"].iloc[-1]),
        "prev_close": float(hist["Close"].iloc[-2]) if len(hist) >= 2 else None,
    }
