import feedparser
import urllib.parse


def fetch_stock_news(stock_code: str, stock_name: str, max_items: int = 5) -> list[dict]:
    queries = [f"{stock_code} {stock_name} 股票", f"{stock_name} 財報 營收"]
    articles = []
    seen = set()

    for query in queries:
        encoded = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        feed = feedparser.parse(url)

        for entry in feed.entries:
            if entry.title not in seen:
                seen.add(entry.title)
                articles.append({
                    "title": entry.title,
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", ""),
                })
            if len(articles) >= max_items:
                return articles

    return articles
