"""
使用方式：
  python manage_stocks.py list
  python manage_stocks.py add 2454 聯發科
  python manage_stocks.py remove 2454
"""
import json
import sys
from pathlib import Path

STOCKS_FILE = Path(__file__).parent / "stocks.json"


def load() -> dict:
    with open(STOCKS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save(data: dict):
    with open(STOCKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cmd_list():
    data = load()
    stocks = data["stocks"]
    if not stocks:
        print("追蹤清單為空")
        return
    print(f"目前追蹤 {len(stocks)} 檔：")
    for s in stocks:
        print(f"  {s['code']}  {s['name']}")


def cmd_add(code: str, name: str):
    data = load()
    for s in data["stocks"]:
        if s["code"] == code:
            print(f"❗ {code} 已在清單中")
            return
    data["stocks"].append({"code": code, "name": name})
    save(data)
    print(f"✅ 已新增 {code} {name}")


def cmd_remove(code: str):
    data = load()
    before = len(data["stocks"])
    data["stocks"] = [s for s in data["stocks"] if s["code"] != code]
    if len(data["stocks"]) == before:
        print(f"❗ 找不到 {code}")
        return
    save(data)
    print(f"✅ 已移除 {code}")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    cmd = args[0]
    if cmd == "list":
        cmd_list()
    elif cmd == "add" and len(args) >= 3:
        cmd_add(args[1], args[2])
    elif cmd == "remove" and len(args) >= 2:
        cmd_remove(args[1])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
