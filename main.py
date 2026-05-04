import io
import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import requests

from src.fetcher import fetch_stock_data
from src.technical import analyze_technical
from src.news import fetch_stock_news
from src.ai_analyzer import analyze_with_ai
from src.line_notifier import send_line_message

BASE = Path(__file__).parent


def load_config() -> dict:
    import os
    if os.environ.get("GEMINI_API_KEY"):
        return {
            "gemini_api_key": os.environ["GEMINI_API_KEY"],
            "line_channel_access_token": os.environ["LINE_CHANNEL_ACCESS_TOKEN"],
            "line_user_id": os.environ["LINE_USER_ID"],
            "line_group_id": os.environ.get("LINE_GROUP_ID", ""),
        }
    with open(BASE / "config.json", encoding="utf-8") as f:
        return json.load(f)


def load_stocks() -> list[dict]:
    with open(BASE / "stocks.json", encoding="utf-8") as f:
        return json.load(f)["stocks"]


def is_trading_day() -> bool:
    from datetime import date
    today = date.today()
    print(f"[DEBUG] 今日日期: {today}, weekday: {today.weekday()}")
    if today.weekday() >= 5:
        return False
    url = "https://www.twse.com.tw/holidaySchedule/holidaySchedule?response=json"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        print(f"[DEBUG] API stat: {data.get('stat')}, 筆數: {len(data.get('data', []))}")
        if data.get("data"):
            print(f"[DEBUG] 第一筆日期格式: {data['data'][0][0]}")
        today_str = today.strftime("%Y/%m/%d")
        non_trading = {row[0] for row in data.get("data", [])}
        result = today_str not in non_trading
        print(f"[DEBUG] today_str={today_str}, is_trading={result}")
        return result
    except Exception as e:
        print(f"[DEBUG] API 例外: {e}")
        return True


def validate_line_token(config: dict) -> bool:
    token = config["line_channel_access_token"]
    try:
        res = requests.get(
            "https://api.line.me/v2/bot/info",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if res.status_code == 200:
            return True
        print(f"LINE Token 驗證失敗 {res.status_code}: {res.text}")
        return False
    except Exception as e:
        print(f"LINE Token 驗證例外：{e}")
        return False


def build_stock_report(stock: dict, config: dict) -> str:
    code = stock["code"]
    name = stock.get("name", code)

    stock_data = fetch_stock_data(code)
    technical = analyze_technical(stock_data["history"])
    news = fetch_stock_news(code, name)
    analysis = analyze_with_ai(stock_data, technical, news, config["gemini_api_key"])

    price = technical["current_price"]
    prev = stock_data.get("prev_close")
    change_str = ""
    if prev:
        pct = (price - prev) / prev * 100
        arrow = "▲" if pct >= 0 else "▼"
        change_str = f" {arrow}{abs(pct):.2f}%"

    header = (
        f"📈 {code} {name}\n"
        f"💰 現價：{price:.2f} 元{change_str}\n"
        f"{'─' * 28}\n"
    )
    return header + analysis


def send_to_all(config: dict, message: str):
    token = config["line_channel_access_token"]
    targets = [config["line_user_id"]]
    if config.get("line_group_id"):
        targets.append(config["line_group_id"])
    for target in targets:
        send_line_message(token, target, message)


def run_analysis(dry_run: bool = False):
    config = load_config()

    if not dry_run:
        if not is_trading_day():
            print("今日非交易日，跳過分析。")
            return
        if not validate_line_token(config):
            print("LINE Token 無效，中止執行。")
            sys.exit(1)

    stocks = load_stocks()
    date_str = datetime.now().strftime("%Y/%m/%d")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 開始分析 {len(stocks)} 檔股票...")

    header_msg = f"📊 台股每日分析\n📅 {date_str}\n共追蹤 {len(stocks)} 檔"
    if not dry_run:
        send_to_all(config, header_msg)

    for stock in stocks:
        code = stock["code"]
        print(f"  → {code} {stock.get('name', '')} ...", end=" ", flush=True)
        try:
            report = build_stock_report(stock, config)
            print("完成")
            if dry_run:
                print(report)
                print()
            else:
                send_to_all(config, report)
        except Exception as e:
            msg = f"❗ {code} 分析失敗：{e}"
            print(f"\n  {msg}")
            if not dry_run:
                send_to_all(config, msg)

    print("✅ 全部完成")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    run_analysis(dry_run=dry_run)