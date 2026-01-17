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
        # PyInstaller 打包后的临时目录
        return os.path.join(sys._MEIPASS, relative_path)
    # 开发环境
    return os.path.join(os.getcwd(), relative_path)


# =====================================================
# Clash 路径
# =====================================================
def get_clash_exe_path():
    """
    返回运行时 clash-core.exe 路径
    
    🔥 修复：支持 PyInstaller 打包后的路径
    """
    # 1️⃣ 优先查找打包后的资源路径
    exe_path = resource_path(os.path.join("clash", "clash-core.exe"))
    
    if os.path.exists(exe_path):
        print(f"[Clash] 找到 Clash 核心: {exe_path}")
        return exe_path
    
    # 2️⃣ 检查当前工作目录
    exe_path_cwd = os.path.join(os.getcwd(), "clash", "clash-core.exe")
    if os.path.exists(exe_path_cwd):
        print(f"[Clash] 找到 Clash 核心: {exe_path_cwd}")
        return exe_path_cwd
    
    # 3️⃣ 检查程序所在目录
    if getattr(sys, 'frozen', False):
        # 打包后的 exe 所在目录
        exe_dir = os.path.dirname(sys.executable)
        exe_path_exe = os.path.join(exe_dir, "clash", "clash-core.exe")
        if os.path.exists(exe_path_exe):
            print(f"[Clash] 找到 Clash 核心: {exe_path_exe}")
            return exe_path_exe
    
    # 4️⃣ 打印调试信息
    print(f"[Clash] ❌ 未找到 clash-core.exe")
    print(f"[Clash] 查找路径:")
    print(f"  1. {exe_path}")
    print(f"  2. {exe_path_cwd}")
    if getattr(sys, 'frozen', False):
        print(f"  3. {exe_path_exe}")
    print(f"[Clash] 当前工作目录: {os.getcwd()}")
    print(f"[Clash] sys._MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")
    
    raise FileNotFoundError(
        "未找到 clash/clash-core.exe\n"
        "请确保 clash 文件夹与程序在同一目录下"
    )


def get_config_path():
    """
    返回 Clash 配置路径
    
    🔥 修复：配置文件应该在工作目录，而不是打包目录
    """
    # 配置文件始终在当前工作目录的 config 文件夹
    config_dir = os.path.join(os.getcwd(), "config")
    os.makedirs(config_dir, exist_ok=True)
    
    config_path = os.path.join(config_dir, "config.yaml")
    print(f"[Clash] 配置文件路径: {config_path}")
    
    return config_path


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
            print("[Clash] Clash 已在运行")
            return True

        try:
            exe = get_clash_exe_path()
            config = get_config_path()

            if not os.path.exists(config):
                print(f"[Clash] ⚠️ 配置文件不存在: {config}")
                raise RuntimeError(f"配置文件不存在: {config}")

            print(f"[Clash] 启动命令: {exe} -f {config}")
            
            _clash_process = subprocess.Popen(
                [exe, "-f", config],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            print(f"[Clash] ✅ Clash 进程已启动 (PID: {_clash_process.pid})")
            time.sleep(0.8)
            
            # 验证进程是否还在运行
            if _clash_process.poll() is not None:
                print(f"[Clash] ❌ Clash 进程启动后立即退出")
                return False
            
            return True
            
        except FileNotFoundError as e:
            print(f"[Clash] ❌ 文件未找到: {e}")
            raise
        except Exception as e:
            print(f"[Clash] ❌ 启动失败: {e}")
            return False


def stop_clash():
    """
    停止 Clash
    """
    global _clash_process

    with _clash_lock:
        if _clash_process:
            try:
                print(f"[Clash] 正在停止 Clash 进程 (PID: {_clash_process.pid})")
                _clash_process.terminate()
                _clash_process.wait(timeout=3)
                print("[Clash] ✅ Clash 已停止")
            except subprocess.TimeoutExpired:
                print("[Clash] ⚠️ 进程未响应，强制终止")
                _clash_process.kill()
                _clash_process.wait()
            except Exception as e:
                print(f"[Clash] ⚠️ 停止进程时出错: {e}")
            finally:
                _clash_process = None


# =====================================================
# 状态接口
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
        "node": "当前节点",
        "delay": "-"
    }


# =====================================================
# 测试函数
# =====================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Clash Runner 测试")
    print("=" * 60)
    print()
    
    try:
        print("📍 测试路径查找...")
        exe = get_clash_exe_path()
        print(f"✅ Clash 核心: {exe}")
        print()
        
        config = get_config_path()
        print(f"✅ 配置路径: {config}")
        print()
        
        if not os.path.exists(config):
            print("⚠️  配置文件不存在，跳过启动测试")
        else:
            print("🚀 测试启动...")
            if start_clash():
                print("✅ 启动成功")
                time.sleep(2)
                
                status = get_clash_status()
                print(f"📊 状态: {status}")
                
                print("🛑 测试停止...")
                stop_clash()
                print("✅ 停止成功")
            else:
                print("❌ 启动失败")
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 60)
    print("✅ 测试完成")
    print("=" * 60)