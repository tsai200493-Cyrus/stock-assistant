"""
每日定時執行股票分析，時間設定在 config.json 的 schedule_time。
只在週一至週五執行（台股交易日）。

執行：python scheduler.py
"""
import json
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from main import run_analysis

BASE = Path(__file__).parent


def load_config() -> dict:
    with open(BASE / "config.json", encoding="utf-8") as f:
        return json.load(f)


def main():
    config = load_config()
    time_str = config.get("schedule_time", "08:30")
    hour, minute = time_str.split(":")

    scheduler = BlockingScheduler(timezone="Asia/Taipei")
    scheduler.add_job(
        run_analysis,
        CronTrigger(
            hour=int(hour),
            minute=int(minute),
            day_of_week="mon-fri",
            timezone="Asia/Taipei",
        ),
    )

    print(f"📅 排程器已啟動")
    print(f"   執行時間：每個工作日 {time_str}")
    print(f"   按 Ctrl+C 停止\n")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\n排程器已停止")


if __name__ == "__main__":
    main()
