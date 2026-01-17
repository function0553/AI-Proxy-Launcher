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
from core.clash_runner import start_clash, stop_clash, get_clash_status
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
# API (修复版)
# ==================================================
@app.post("/api/update_subscription")
async def update_subscription(req: UpdateSubRequest):
    """
    更新订阅配置并启动 Clash
    """
    global proxy_enabled
    
    try:
        # 1️⃣ 如果代理已启用，先禁用
        if proxy_enabled:
            disable_system_proxy()
            proxy_enabled = False
            print("[API] 已禁用系统代理")

        # 2️⃣ 停止现有的 Clash 进程
        print("[API] 正在停止现有 Clash 进程...")
        stop_clash()
        time.sleep(1.5)

        # 3️⃣ 生成新的配置文件
        print(f"[API] 正在生成配置文件: {req.url}")
        config_path = generate_config_from_url(req.url)
        
        # 4️⃣ 验证配置文件是否生成成功
        if not os.path.exists(config_path):
            raise RuntimeError(f"配置文件生成失败: {config_path}")
        
        print(f"[API] ✅ 配置文件已生成: {config_path}")
        
        # 5️⃣ 启动 Clash
        print("[API] 正在启动 Clash...")
        clash_started = start_clash()
        
        if not clash_started:
            raise RuntimeError("Clash 启动失败，请检查配置文件")
        
        # 6️⃣ 等待 Clash 完全启动
        time.sleep(2)
        
        # 7️⃣ 验证 Clash 是否成功运行
        max_retries = 5
        for i in range(max_retries):
            try:
                response = requests.get(CLASH_API_PROXIES, timeout=2)
                if response.status_code == 200:
                    print(f"[API] ✅ Clash 已成功启动 (尝试 {i+1}/{max_retries})")
                    break
            except requests.RequestException:
                if i < max_retries - 1:
                    print(f"[API] ⏳ 等待 Clash 启动... ({i+1}/{max_retries})")
                    time.sleep(1)
                else:
                    print("[API] ⚠️ Clash 可能未完全启动，但配置已更新")
        
        return {
            "status": "success",
            "message": "订阅更新成功，Clash 已启动",
            "clash_running": get_clash_status()["running"]
        }
        
    except Exception as e:
        print(f"[API] ❌ 更新订阅失败: {str(e)}")
        return {
            "status": "error",
            "message": f"更新失败: {str(e)}"
        }


@app.get("/api/nodes")
async def get_nodes():
    """
    获取节点列表 (修复版 - 处理边界情况)
    """
    try:
        # 检查 Clash 是否运行
        clash_status = get_clash_status()
        if not clash_status["running"]:
            return {
                "nodes": [],
                "current": None,
                "message": "Clash 未运行，请先更新订阅"
            }
        
        response = requests.get(CLASH_API_PROXIES, timeout=3)
        data = response.json()
        
        # 🔥 修复：安全获取代理组信息
        proxies = data.get("proxies", {})
        selector_group = proxies.get("节点选择", {})
        
        # 🔥 修复：处理空列表情况
        all_nodes = selector_group.get("all", [])
        current = selector_group.get("now", "")
        
        if not all_nodes:
            print("[API] ⚠️ 未找到任何节点")
            return {
                "nodes": [],
                "current": None,
                "message": "配置文件中没有可用节点"
            }
        
        nodes = []
        for name in all_nodes:
            # 跳过代理组
            if name in ["自动选择", "DIRECT"]:
                continue
            
            # 🔥 修复：安全获取节点信息
            node_info = proxies.get(name, {})
            
            # 🔥 修复：安全获取延迟信息
            history = node_info.get("history", [])
            if history and len(history) > 0:
                # 获取最后一次测速记录
                last_test = history[-1]
                delay = last_test.get("delay", 0) if isinstance(last_test, dict) else 0
                
                if delay > 0:
                    delay_str = f"{delay}ms"
                else:
                    delay_str = "未测速"
            else:
                delay_str = "未测速"
            
            nodes.append({
                "name": name,
                "delay": delay_str,
                "type": node_info.get("type", "unknown")
            })
        
        print(f"[API] ✅ 获取到 {len(nodes)} 个节点，当前选择: {current}")
        
        return {
            "nodes": nodes,
            "current": current,
            "total": len(nodes)
        }
        
    except requests.RequestException as e:
        print(f"[API] ❌ 获取节点失败 (网络错误): {str(e)}")
        return {
            "nodes": [],
            "current": None,
            "message": f"无法连接到 Clash API: {str(e)}"
        }
    except KeyError as e:
        print(f"[API] ❌ 获取节点失败 (数据格式错误): {str(e)}")
        print(f"[API] 原始数据: {data if 'data' in locals() else 'N/A'}")
        return {
            "nodes": [],
            "current": None,
            "message": f"配置文件格式错误: {str(e)}"
        }
    except Exception as e:
        print(f"[API] ❌ 获取节点失败 (未知错误): {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "nodes": [],
            "current": None,
            "message": f"获取节点失败: {str(e)}"
        }


@app.post("/api/switch_node")
async def switch_node(req: SwitchNodeRequest):
    """
    切换节点
    """
    global proxy_enabled
    
    try:
        # 检查 Clash 是否运行
        clash_status = get_clash_status()
        if not clash_status["running"]:
            raise RuntimeError("Clash 未运行，请先更新订阅")
        
        # 切换节点
        response = requests.put(
            f"{CLASH_API_PROXIES}/节点选择",
            json={"name": req.name},
            timeout=3
        )
        
        if response.status_code != 204:
            raise RuntimeError(f"切换节点失败: HTTP {response.status_code}")
        
        print(f"[API] ✅ 已切换到节点: {req.name}")
        
        # 首次切换节点时自动启用系统代理
        was_enabled = proxy_enabled
        if not proxy_enabled:
            print("[API] 首次选择节点，正在启用系统代理...")
            enable_system_proxy()
            proxy_enabled = True
        
        return {
            "status": "success",
            "message": f"已切换到 {req.name}",
            "proxy_enabled": proxy_enabled,
            "first_time": not was_enabled
        }
        
    except Exception as e:
        print(f"[API] ❌ 切换节点失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/proxy_status")
async def get_proxy_status():
    """获取代理状态"""
    clash_status = get_clash_status()
    return {
        "enabled": proxy_enabled,
        "status": get_current_proxy_status(),
        "clash_running": clash_status["running"]
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
    """轮询 Clash 状态（用于托盘显示）"""
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

    # 启动清理
    perform_startup_cleanup()

    # 只有在配置文件存在时才尝试启动 Clash
    if os.path.exists(CONFIG_PATH):
        print("[Main] 检测到配置文件，正在启动 Clash...")
        start_clash()
        time.sleep(1)
    else:
        print("[Main] 未检测到配置文件，等待用户输入订阅链接...")

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

    # 必须在主线程
    icon.run()

if __name__ == "__main__":
    main()