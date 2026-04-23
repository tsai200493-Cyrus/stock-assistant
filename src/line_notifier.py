import requests

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"
MAX_CHARS = 4900


def _split_message(text: str) -> list[str]:
    if len(text) <= MAX_CHARS:
        return [text]
    chunks = []
    while text:
        chunks.append(text[:MAX_CHARS])
        text = text[MAX_CHARS:]
    return chunks


def send_line_message(access_token: str, user_id: str, text: str) -> bool:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    chunks = _split_message(text)
    messages = [{"type": "text", "text": chunk} for chunk in chunks[:5]]

    resp = requests.post(
        LINE_PUSH_URL,
        headers=headers,
        json={"to": user_id, "messages": messages},
        timeout=10,
    )

    if resp.status_code != 200:
        print(f"Line API 錯誤 {resp.status_code}: {resp.text}")
        return False
    return True
