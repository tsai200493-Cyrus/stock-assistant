import time
from google import genai

SYSTEM_PROMPT = (
    "你是一位資深台股分析師，擅長技術分析（K線、均線、指標）與消息面整合，"
    "提供清晰、有依據的投資建議。所有建議僅供參考，投資人需自行承擔風險。"
    "請用繁體中文回覆，格式清晰易讀。"
)


def analyze_with_ai(
    stock_data: dict,
    technical: dict,
    news: list[dict],
    api_key: str,
) -> str:
    client = genai.Client(api_key=api_key)

    candle_lines = "\n".join(
        f"  開:{c['open']} 高:{c['high']} 低:{c['low']} 收:{c['close']} 量:{c['volume']:,}"
        for c in technical["recent_candles"]
    )

    news_lines = (
        "\n".join(f"- {a['title']}" for a in news)
        if news else "（無近期相關新聞）"
    )

    def fmt(val, decimals=2):
        return f"{val:.{decimals}f}" if val is not None else "N/A"

    price = technical["current_price"]
    prev_price = stock_data.get("prev_close")
    change_str = ""
    if prev_price:
        pct = (price - prev_price) / prev_price * 100
        arrow = "+" if pct >= 0 else ""
        change_str = f"（{arrow}{pct:.2f}%）"

    signals_text = "\n".join(f"  - {s}" for s in technical["signals"]) or "  - 無明顯信號"

    prompt = f"""{SYSTEM_PROMPT}

請分析以下台股資料，給出投資建議。

## 股票：{stock_data['code']} {stock_data.get('name', '')}
- 當前股價：{price:.2f} 元 {change_str}

## 近五日 K 線
{candle_lines}

## 技術指標
- RSI(14)：{fmt(technical['rsi'])}
- MACD：{fmt(technical['macd'], 4)} / Signal：{fmt(technical['macd_signal'], 4)}
- MA5：{fmt(technical['ma5'])} / MA20：{fmt(technical['ma20'])} / MA60：{fmt(technical['ma60'])}
- 布林上軌：{fmt(technical['bb_upper'])} / 布林下軌：{fmt(technical['bb_lower'])}

## 技術信號
{signals_text}

## 近期相關新聞
{news_lines}

---
請依下列格式回覆：

1. 技術面解讀
（K線走勢、均線排列、指標狀態）

2. 消息面評估
（新聞對股價的潛在影響）

3. 操作建議
（明確說明買入 / 持有 / 觀望 / 減碼 / 賣出，並給出理由與參考價位）

4. 風險提示
（需特別注意的風險點）

最後一行請單獨標示最終結論，格式：
[建議買入] 或 [建議持有觀望] 或 [建議賣出/減碼]"""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            if attempt < 2 and ("503" in str(e) or "UNAVAILABLE" in str(e)):
                time.sleep(15)
                continue
            raise
