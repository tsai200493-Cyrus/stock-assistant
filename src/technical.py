import pandas as pd
import ta


def analyze_technical(history: pd.DataFrame) -> dict:
    df = history.copy()
    close = df["Close"]
    volume = df["Volume"]

    rsi_series = ta.momentum.RSIIndicator(close=close, window=14).rsi()
    macd_ind = ta.trend.MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
    bb_ind = ta.volatility.BollingerBands(close=close, window=20, window_dev=2)
    ma5_series = ta.trend.SMAIndicator(close=close, window=5).sma_indicator()
    ma20_series = ta.trend.SMAIndicator(close=close, window=20).sma_indicator()
    ma60_series = ta.trend.SMAIndicator(close=close, window=60).sma_indicator()
    vol_ma5_series = ta.trend.SMAIndicator(close=volume, window=5).sma_indicator()

    def safe(series):
        val = series.iloc[-1]
        return float(val) if pd.notna(val) else None

    def safe_prev(series):
        val = series.iloc[-2] if len(series) >= 2 else None
        return float(val) if val is not None and pd.notna(val) else None

    rsi = safe(rsi_series)
    macd_val = safe(macd_ind.macd())
    macd_sig = safe(macd_ind.macd_signal())
    prev_macd = safe_prev(macd_ind.macd())
    prev_sig = safe_prev(macd_ind.macd_signal())
    bb_upper = safe(bb_ind.bollinger_hband())
    bb_lower = safe(bb_ind.bollinger_lband())
    ma5 = safe(ma5_series)
    ma20 = safe(ma20_series)
    ma60 = safe(ma60_series)
    price = float(df["Close"].iloc[-1])
    vol = float(df["Volume"].iloc[-1])
    vol_ma5 = safe(vol_ma5_series)

    signals = []

    if rsi is not None:
        if rsi < 30:
            signals.append(f"RSI {rsi:.1f}，超賣區，留意反彈機會")
        elif rsi > 70:
            signals.append(f"RSI {rsi:.1f}，超買區，注意拉回風險")
        else:
            signals.append(f"RSI {rsi:.1f}，中性區間")

    if all(v is not None for v in [macd_val, macd_sig, prev_macd, prev_sig]):
        if prev_macd < prev_sig and macd_val > macd_sig:
            signals.append("MACD 黃金交叉，短線買入信號")
        elif prev_macd > prev_sig and macd_val < macd_sig:
            signals.append("MACD 死亡交叉，短線賣出信號")
        elif macd_val > macd_sig:
            signals.append("MACD 多頭排列，趨勢偏多")
        else:
            signals.append("MACD 空頭排列，趨勢偏空")

    if ma5 and ma20 and ma60:
        if price > ma5 > ma20 > ma60:
            signals.append("多頭排列：股價 > MA5 > MA20 > MA60")
        elif price < ma5 < ma20 < ma60:
            signals.append("空頭排列：股價 < MA5 < MA20 < MA60")
        elif price > ma20:
            signals.append(f"股價站上 MA20（{ma20:.2f}），短中期偏多")
        else:
            signals.append(f"股價跌破 MA20（{ma20:.2f}），短中期偏空")

    if bb_upper and bb_lower:
        if price >= bb_upper:
            signals.append(f"股價觸及布林上軌（{bb_upper:.2f}），注意壓力")
        elif price <= bb_lower:
            signals.append(f"股價觸及布林下軌（{bb_lower:.2f}），注意支撐")

    if vol_ma5 and vol > vol_ma5 * 1.5:
        signals.append(f"成交量爆量（是五日均量的 {vol/vol_ma5:.1f} 倍），需確認方向")

    recent_candles = []
    for _, row in df[["Open", "High", "Low", "Close", "Volume"]].tail(5).iterrows():
        recent_candles.append({
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]),
        })

    return {
        "current_price": price,
        "rsi": rsi,
        "macd": macd_val,
        "macd_signal": macd_sig,
        "ma5": ma5,
        "ma20": ma20,
        "ma60": ma60,
        "bb_upper": bb_upper,
        "bb_lower": bb_lower,
        "signals": signals,
        "recent_candles": recent_candles,
    }
