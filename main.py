import os
import sys
import threading
import time
import webbrowser
import requests
import uvicorn
import pystray
from PIL import Image, ImageDraw
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ==================================================
# PyInstaller 资源路径
# ==================================================
def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# ==================================================
# 项目模块
# ==================================================
from generate_config import generate_config_from_url
from core.clash_runner import start_clash, stop_clash
from core.windows_proxy import (
    enable_system_proxy,
    disable_system_proxy,
    get_current_proxy_status,
)
from startup_cleanup import perform_startup_cleanup

# ==================================================
# 配置
# ==================================================
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.yaml")
DASHBOARD_URL = "http://127.0.0.1:8080/"
CLASH_API_PROXIES = "http://127.0.0.1:9090/proxies"

app = FastAPI()
proxy_enabled = False

# ==================================================
# 数据模型
# ==================================================
class UpdateSubRequest(BaseModel):
    url: str

class SwitchNodeRequest(BaseModel):
    name: str

# ==================================================
# API（保持你原样，不动）
# ==================================================
@app.post("/api/update_subscription")
async def update_subscription(req: UpdateSubRequest):
    global proxy_enabled
    if proxy_enabled:
        disable_system_proxy()
        proxy_enabled = False

    generate_config_from_url(req.url)
    stop_clash()
    time.sleep(1)
    start_clash()

    return {"status": "success", "message": "订阅更新成功"}

@app.get("/api/proxy_status")
async def get_proxy_status():
    return {
        "enabled": proxy_enabled,
        "status": get_current_proxy_status()
    }

# ==================================================
# 静态文件
# ==================================================
web_dir = resource_path("web")
app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")

# ==================================================
# 托盘状态
# ==================================================
current_node = "未选择"
current_delay = "N/A"
proxy_status = "未启用"

def poll_clash_status(icon):
    global current_node, current_delay, proxy_status
    while True:
        try:
            resp = requests.get(CLASH_API_PROXIES, timeout=2).json()
            selector = resp["proxies"].get("节点选择", {})
            current_node = selector.get("now", "未选择")
            proxy_status = "已启用" if proxy_enabled else "未启用"
            icon.update_menu()
        except:
            current_node = "Clash 未运行"
            current_delay = "N/A"
            proxy_status = "未启用"
        time.sleep(5)

# ==================================================
# 托盘
# ==================================================
def create_tray_icon():
    img = Image.new("RGB", (64, 64), (15, 23, 42))
    d = ImageDraw.Draw(img)
    d.ellipse((16, 16, 48, 48), fill=(56, 189, 248))

    def on_open(icon, item):
        webbrowser.open(DASHBOARD_URL)

    def on_toggle_proxy(icon, item):
        global proxy_enabled
        if proxy_enabled:
            disable_system_proxy()
            proxy_enabled = False
        else:
            enable_system_proxy()
            proxy_enabled = True
        icon.update_menu()

    def on_exit(icon, item):
        if proxy_enabled:
            disable_system_proxy()
        stop_clash()
        icon.stop()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem("打开控制面板", on_open),
        pystray.MenuItem(lambda _: f"当前节点: {current_node}", None, enabled=False),
        pystray.MenuItem(lambda _: f"系统代理: {proxy_status}", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            lambda _: "禁用系统代理" if proxy_enabled else "启用系统代理",
            on_toggle_proxy
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出程序", on_exit),
    )

    return pystray.Icon("AI_Proxy_Launcher", img, "AI Proxy Launcher", menu)

# ==================================================
# 主入口
# ==================================================
def main():
    global proxy_enabled

    perform_startup_cleanup()

    if os.path.exists(CONFIG_PATH):
        start_clash()

    # 后台启动 FastAPI
    threading.Thread(
        target=lambda: uvicorn.run(
            app,
            host="127.0.0.1",
            port=8080,
            log_config=None
        ),
        daemon=True
    ).start()

    # 创建托盘（主线程）
    icon = create_tray_icon()
    threading.Thread(target=poll_clash_status, args=(icon,), daemon=True).start()
    threading.Timer(1.2, lambda: webbrowser.open(DASHBOARD_URL)).start()

    # ❗ 必须在主线程
    icon.run()

if __name__ == "__main__":
    main()
