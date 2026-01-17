import requests
from datetime import datetime, timezone


def get_network_datetime():
    urls = [
        "https://www.google.com",
        "https://www.cloudflare.com",
        "https://www.baidu.com",
    ]

    for url in urls:
        try:
            r = requests.get(url, timeout=5)
            date_str = r.headers.get("Date")
            if date_str:
                return datetime.strptime(
                    date_str, "%a, %d %b %Y %H:%M:%S GMT"
                ).replace(tzinfo=timezone.utc)
        except Exception:
            continue

    # 兜底：本地时间
    return datetime.now(timezone.utc)
