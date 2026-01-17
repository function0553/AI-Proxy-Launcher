# yaml_merge.py（Gemini 优化版 - 完全修复）

import yaml
import requests
import base64
import re

def preprocess_yaml(content: str) -> str:
    """预处理 YAML 内容，移除特殊标签"""
    content = re.sub(r'!\<[a-zA-Z]+\>\s*', '', content)
    return content

def parse_proxy_uri(uri: str):
    """解析代理 URI（需要你的完整实现）"""
    return None

def merge_subscriptions(sub_urls):
    """合并订阅并生成配置"""
    proxies = []

    for url in sub_urls:
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            yml = response.text.strip()
            yml_clean = preprocess_yaml(yml)

            parsed = False
            try:
                data = yaml.safe_load(yml_clean)
                if isinstance(data, dict):
                    found_proxies = data.get("proxies", [])
                    if found_proxies:
                        proxies.extend(found_proxies)
                        parsed = True
                elif isinstance(data, list):
                    proxies.extend(data)
                    parsed = True
            except yaml.YAMLError:
                pass

            if not parsed:
                try:
                    decoded = base64.b64decode(yml + "===").decode("utf-8").strip()
                    decoded_clean = preprocess_yaml(decoded)
                    data = yaml.safe_load(decoded_clean)
                    if isinstance(data, dict):
                        found_proxies = data.get("proxies", [])
                        if found_proxies:
                            proxies.extend(found_proxies)
                            parsed = True
                    elif isinstance(data, list):
                        proxies.extend(data)
                        parsed = True
                except Exception:
                    pass

        except Exception:
            continue

    # 去重
    seen = set()
    unique_proxies = []
    for i, p in enumerate(proxies):
        if isinstance(p, dict) and p.get("name"):
            name = p["name"]
            if name not in seen:
                seen.add(name)
                unique_proxies.append(p)
        else:
            p["name"] = f"Node-{i+1}"
            unique_proxies.append(p)

    if not unique_proxies:
        raise ValueError("未能从订阅链接中解析出任何有效节点")

    proxy_names = [p["name"] for p in unique_proxies]

    # 代理组配置
    proxy_groups = [
        {
            "name": "节点选择",
            "type": "select",
            "proxies": ["自动选择", "DIRECT"] + proxy_names
        },
        {
            "name": "自动选择",
            "type": "url-test",
            "url": "http://www.gstatic.com/generate_204",
            "interval": 300,
            "tolerance": 50,
            "proxies": proxy_names
        }
    ]

    # 🔥🔥🔥 针对 Gemini 的完整 DNS 配置
    dns_config = {
        "enable": True,
        "ipv6": False,
        "prefer-h3": False,
        "listen": "0.0.0.0:53",
        "enhanced-mode": "redir-host",
        
        "default-nameserver": [
            "223.5.5.5",
            "119.29.29.29"
        ],
        
        "nameserver": [
            "223.5.5.5",
            "119.29.29.29",
            "https://1.1.1.1/dns-query",
            "https://8.8.8.8/dns-query"
        ],
        
        "fallback": [
            "https://1.1.1.1/dns-query",
            "https://1.0.0.1/dns-query",
            "https://8.8.8.8/dns-query",
            "https://8.8.4.4/dns-query",
            "tls://1.1.1.1:853",
            "tls://8.8.8.8:853"
        ],
        
        "fallback-filter": {
            "geoip": True,
            "geoip-code": "CN",
            "ipcidr": [
                "240.0.0.0/4",
                "0.0.0.0/32",
                "127.0.0.1/32"
            ],
            "domain": [
                "+.google.com",
                "+.googleapis.com",
                "+.gstatic.com",
                "+.googleusercontent.com",
                "+.youtube.com",
                "+.googlevideo.com",
                "+.google.co.jp",
                "+.google.co.uk",
                "+.google.de",
                "+.google.fr",
                "+.ggpht.com",
                "+.googleadservices.com",
                "+.googlesyndication.com",
                "+.googletagmanager.com",
                "+.googletagservices.com",
                
                "+.openai.com",
                "+.chatgpt.com",
                "+.oaiusercontent.com",
                "+.oaistatic.com",
                
                "+.anthropic.com",
                "+.claude.ai",
                
                "+.cloudflare.com",
                "+.github.com"
            ]
        },
        
        # 🔥🔥🔥 关键：针对 Google/Gemini 的 DNS 策略
        "nameserver-policy": {
            # Google 主域名及所有子域名
            "*.google.com": "https://8.8.8.8/dns-query",
            "*.googleapis.com": "https://8.8.8.8/dns-query",
            "*.gstatic.com": "https://8.8.8.8/dns-query",
            "*.googleusercontent.com": "https://8.8.8.8/dns-query",
            "*.ggpht.com": "https://8.8.8.8/dns-query",
            
            # Gemini 特定域名
            "gemini.google.com": "https://8.8.8.8/dns-query",
            "ai.google.dev": "https://8.8.8.8/dns-query",
            "makersuite.google.com": "https://8.8.8.8/dns-query",
            "generativelanguage.googleapis.com": "https://8.8.8.8/dns-query",
            
            # Google 其他服务
            "*.youtube.com": "https://8.8.8.8/dns-query",
            "*.ytimg.com": "https://8.8.8.8/dns-query",
            "*.googlevideo.com": "https://8.8.8.8/dns-query",
            
            # OpenAI
            "*.openai.com": "https://1.1.1.1/dns-query",
            "*.chatgpt.com": "https://1.1.1.1/dns-query",
            "*.oaiusercontent.com": "https://1.1.1.1/dns-query",
            "*.oaistatic.com": "https://1.1.1.1/dns-query",
            
            # Anthropic
            "*.anthropic.com": "https://1.1.1.1/dns-query",
            "*.claude.ai": "https://1.1.1.1/dns-query",
            
            # 国内域名使用国内 DNS
            "*.cn": "223.5.5.5",
            "*.taobao.com": "223.5.5.5",
            "*.tmall.com": "223.5.5.5",
            "*.alipay.com": "223.5.5.5",
            "*.jd.com": "223.5.5.5",
            "*.baidu.com": "223.5.5.5",
            "*.qq.com": "223.5.5.5",
            "*.bilibili.com": "223.5.5.5"
        }
    }

    # 🔥🔥🔥 针对 Gemini 优化的规则（更细致的匹配）
    rules = [
        # 本地网络直连
        "DOMAIN-SUFFIX,local,DIRECT",
        "IP-CIDR,127.0.0.0/8,DIRECT",
        "IP-CIDR,172.16.0.0/12,DIRECT",
        "IP-CIDR,192.168.0.0/16,DIRECT",
        "IP-CIDR,10.0.0.0/8,DIRECT",
        
        # 🔥🔥🔥 Google/Gemini 相关域名（最高优先级）
        # Gemini 核心域名
        "DOMAIN,gemini.google.com,节点选择",
        "DOMAIN-SUFFIX,gemini.google.com,节点选择",
        "DOMAIN,ai.google.dev,节点选择",
        "DOMAIN,makersuite.google.com,节点选择",
        "DOMAIN,generativelanguage.googleapis.com,节点选择",
        
        # Google 主域名和常用服务
        "DOMAIN-SUFFIX,google.com,节点选择",
        "DOMAIN-SUFFIX,googleapis.com,节点选择",
        "DOMAIN-SUFFIX,gstatic.com,节点选择",
        "DOMAIN-SUFFIX,googleusercontent.com,节点选择",
        "DOMAIN-SUFFIX,ggpht.com,节点选择",
        "DOMAIN-SUFFIX,googleadservices.com,节点选择",
        "DOMAIN-SUFFIX,googlesyndication.com,节点选择",
        "DOMAIN-SUFFIX,googletagmanager.com,节点选择",
        "DOMAIN-SUFFIX,googletagservices.com,节点选择",
        
        # Google 国际域名
        "DOMAIN-SUFFIX,google.co.jp,节点选择",
        "DOMAIN-SUFFIX,google.co.uk,节点选择",
        "DOMAIN-SUFFIX,google.de,节点选择",
        "DOMAIN-SUFFIX,google.fr,节点选择",
        
        # YouTube
        "DOMAIN-SUFFIX,youtube.com,节点选择",
        "DOMAIN-SUFFIX,ytimg.com,节点选择",
        "DOMAIN-SUFFIX,googlevideo.com,节点选择",
        
        # 🔥 OpenAI
        "DOMAIN-SUFFIX,openai.com,节点选择",
        "DOMAIN-SUFFIX,chatgpt.com,节点选择",
        "DOMAIN-SUFFIX,oaiusercontent.com,节点选择",
        "DOMAIN-SUFFIX,oaistatic.com,节点选择",
        "DOMAIN-SUFFIX,auth0.com,节点选择",
        
        # 🔥 Anthropic
        "DOMAIN-SUFFIX,anthropic.com,节点选择",
        "DOMAIN-SUFFIX,claude.ai,节点选择",
        
        # 其他国际服务
        "DOMAIN-SUFFIX,github.com,节点选择",
        "DOMAIN-SUFFIX,githubusercontent.com,节点选择",
        "DOMAIN-SUFFIX,twitter.com,节点选择",
        "DOMAIN-SUFFIX,x.com,节点选择",
        "DOMAIN-SUFFIX,facebook.com,节点选择",
        "DOMAIN-SUFFIX,instagram.com,节点选择",
        "DOMAIN-SUFFIX,cloudflare.com,节点选择",
        
        # 国内服务直连
        "DOMAIN-SUFFIX,cn,DIRECT",
        "DOMAIN-SUFFIX,taobao.com,DIRECT",
        "DOMAIN-SUFFIX,tmall.com,DIRECT",
        "DOMAIN-SUFFIX,alipay.com,DIRECT",
        "DOMAIN-SUFFIX,jd.com,DIRECT",
        "DOMAIN-SUFFIX,baidu.com,DIRECT",
        "DOMAIN-SUFFIX,bilibili.com,DIRECT",
        "DOMAIN-SUFFIX,qq.com,DIRECT",
        "DOMAIN-SUFFIX,163.com,DIRECT",
        "DOMAIN-SUFFIX,126.com,DIRECT",
        "DOMAIN-SUFFIX,sina.com.cn,DIRECT",
        "DOMAIN-SUFFIX,weibo.com,DIRECT",
        "DOMAIN-SUFFIX,douban.com,DIRECT",
        "DOMAIN-SUFFIX,zhihu.com,DIRECT",
        
        # Apple & Microsoft
        "DOMAIN-SUFFIX,apple.com,DIRECT",
        "DOMAIN-SUFFIX,icloud.com,DIRECT",
        "DOMAIN-SUFFIX,microsoft.com,DIRECT",
        
        # 中国大陆 IP
        "GEOIP,CN,DIRECT",
        
        # 最终规则
        "MATCH,节点选择"
    ]

    return {
        "mixed-port": 7890,
        "allow-lan": True,
        "bind-address": "*",
        "mode": "rule",
        "log-level": "info",
        "external-controller": "127.0.0.1:9090",
        "secret": "",
        
        # DNS 配置
        "dns": dns_config,
        
        "proxies": unique_proxies,
        "proxy-groups": proxy_groups,
        "rules": rules
    }