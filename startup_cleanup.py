"""
启动清理模块（增强版）
在程序启动时自动执行必要的清理操作
支持通过配置文件自定义行为
"""

import os
import subprocess
import time
import yaml


class StartupCleaner:
    """启动清理器"""
    
    def __init__(self, config_path="cleanup_config.yaml"):
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path):
        """加载配置文件"""
        default_config = {
            "startup_cleanup": {
                "enabled": True,
                "kill_clash": True,
                "flush_dns": True,
                "reset_proxy": True,
                "wait_time": 0.5
            },
            "logging": {
                "verbose": True,
                "warnings_only": True
            }
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        # 合并配置
                        default_config.update(user_config)
            except Exception as e:
                print(f"[Cleanup] ⚠️ 加载配置文件失败，使用默认配置: {e}")
        
        return default_config
    
    def _log(self, message, is_error=False):
        """记录日志"""
        verbose = self.config["logging"]["verbose"]
        warnings_only = self.config["logging"]["warnings_only"]
        
        if is_error and warnings_only:
            # 将错误降级为警告
            message = message.replace("❌", "⚠️")
        
        if verbose or is_error:
            print(message)
    
    def kill_clash_process(self):
        """停止可能残留的 Clash 进程"""
        if not self.config["startup_cleanup"]["kill_clash"]:
            return True
        
        try:
            result = subprocess.run(
                ["taskkill", "/F", "/IM", "clash-core.exe"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self._log("[Cleanup] ✓ 已停止残留的 Clash 进程")
                time.sleep(1)
            return True
                
        except Exception as e:
            self._log(f"[Cleanup] ❌ 停止 Clash 进程时出错: {e}", is_error=True)
            return False
    
    def flush_dns_cache(self):
        """清除系统 DNS 缓存（最关键的操作）"""
        if not self.config["startup_cleanup"]["flush_dns"]:
            return True
        
        try:
            result = subprocess.run(
                ["ipconfig", "/flushdns"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self._log("[Cleanup] ✓ DNS 缓存已清除")
                return True
            else:
                self._log(f"[Cleanup] ❌ DNS 缓存清除失败", is_error=True)
                return False
                
        except Exception as e:
            self._log(f"[Cleanup] ❌ 清除 DNS 缓存时出错: {e}", is_error=True)
            return False
    
    def reset_system_proxy(self):
        """重置系统代理设置"""
        if not self.config["startup_cleanup"]["reset_proxy"]:
            return True
        
        try:
            import winreg
            
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            
            self._log("[Cleanup] ✓ 系统代理已重置")
            return True
            
        except Exception as e:
            self._log(f"[Cleanup] ❌ 重置系统代理时出错: {e}", is_error=True)
            return False
    
    def cleanup(self):
        """执行完整的清理流程"""
        if not self.config["startup_cleanup"]["enabled"]:
            self._log("[Cleanup] ⚠️ 启动清理已禁用")
            return
        
        verbose = self.config["logging"]["verbose"]
        
        if verbose:
            print("\n" + "=" * 60)
            print("🧹 执行启动清理...")
            print("=" * 60)
        
        # 执行清理操作
        self.kill_clash_process()
        self.flush_dns_cache()
        self.reset_system_proxy()
        
        if verbose:
            print("=" * 60)
            print("✅ 启动清理完成")
            print("=" * 60 + "\n")
        
        # 等待所有操作生效
        wait_time = self.config["startup_cleanup"]["wait_time"]
        if wait_time > 0:
            time.sleep(wait_time)


# 全局清理器实例
_cleaner = None

def get_cleaner():
    """获取全局清理器实例"""
    global _cleaner
    if _cleaner is None:
        _cleaner = StartupCleaner()
    return _cleaner

def perform_startup_cleanup():
    """
    执行启动清理（便捷函数）
    在 main.py 中调用此函数即可
    """
    cleaner = get_cleaner()
    cleaner.cleanup()


if __name__ == "__main__":
    # 测试清理功能
    print("🧪 测试启动清理功能\n")
    perform_startup_cleanup()
    print("\n✅ 测试完成")