import os
import sys
import subprocess
import threading
import time

# =====================================================
# 全局状态
# =====================================================
_clash_process = None
_clash_lock = threading.Lock()


# =====================================================
# PyInstaller 资源路径
# =====================================================
def resource_path(relative_path: str) -> str:
    """
    获取资源路径（兼容 PyInstaller）
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.getcwd(), relative_path)


# =====================================================
# Clash 路径
# =====================================================
def get_clash_exe_path():
    """
    返回运行时 clash-core.exe 路径
    """
    exe_path = os.path.join("clash", "clash-core.exe")
    if not os.path.exists(exe_path):
        raise FileNotFoundError("未找到 clash/clash-core.exe")
    return exe_path


def get_config_path():
    """
    返回 Clash 配置路径
    """
    return os.path.join("config", "config.yaml")


# =====================================================
# Clash 控制
# =====================================================
def start_clash():
    """
    启动 Clash（无黑窗）
    """
    global _clash_process

    with _clash_lock:
        if _clash_process and _clash_process.poll() is None:
            return True  # 已运行

        exe = get_clash_exe_path()
        config = get_config_path()

        if not os.path.exists(config):
            raise RuntimeError("config/config.yaml 不存在")

        try:
            _clash_process = subprocess.Popen(
                [
                    exe,
                    "-f", config,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(0.8)
            return True
        except Exception as e:
            print(f"[Clash] 启动失败: {e}")
            return False


def stop_clash():
    """
    停止 Clash
    """
    global _clash_process

    with _clash_lock:
        if _clash_process:
            try:
                _clash_process.terminate()
                _clash_process.wait(timeout=3)
            except Exception:
                pass
            _clash_process = None


# =====================================================
# 状态接口（🔥 给 main.py / 托盘 / API 用）
# =====================================================
def get_clash_status():
    """
    获取 Clash 当前状态
    """
    running = False

    with _clash_lock:
        if _clash_process and _clash_process.poll() is None:
            running = True

    return {
        "running": running,
        # 下面两个暂时占位，后期可接 Clash API
        "node": "当前节点",
        "delay": "-"
    }
