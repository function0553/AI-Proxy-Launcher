import requests
from bs4 import BeautifulSoup

def build_freeclash_url(dt):
    return (
        f"https://www.freeclashnode.com/free-node/"
        f"{dt.year}-{dt.month}-{dt.day}-free-node-subscribe-links.htm"
    )

def extract_clash_subscriptions(url):
    html = requests.get(url, timeout=10).text
    soup = BeautifulSoup(html, "html.parser")
    lines = soup.get_text().splitlines()

    subs = []
    record = False

    for line in lines:
        line = line.strip()
        if "Clash免费节点" in line:
            record = True
            continue
        if "Sing-Box免费节点" in line:
            break
        if record and line.startswith("http"):
            subs.append(line)

    return subs
