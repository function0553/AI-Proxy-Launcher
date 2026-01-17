"""
Windows 系统代理管理模块（增强版）
解决中国大陆环境下的代理问题
"""

import winreg
import ctypes
import time

class WindowsProxyManager:
    """Windows 系统代理管理器"""
    
    INTERNET_SETTINGS = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
    
    def __init__(self):
        self.original_proxy_enable = None
        self.original_proxy_server = None
        self.original_proxy_override = None
        
    def _read_registry_value(self, key_path, value_name, default=None):
        """读取注册表值"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, value_name)
                return value
        except (WindowsError, FileNotFoundError):
            return default
    
    def _write_registry_value(self, key_path, value_name, value, value_type=winreg.REG_SZ):
        """写入注册表值"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, value_name, 0, value_type, value)
            return True
        except Exception as e:
            print(f"[Proxy] 写入注册表失败: {e}")
            return False
    
    def _notify_system(self):
        """通知系统代理设置已更改"""
        try:
            INTERNET_OPTION_SETTINGS_CHANGED = 39
            INTERNET_OPTION_REFRESH = 37
            
            internet_set_option = ctypes.windll.wininet.InternetSetOptionW
            
            # 多次通知确保生效
            for _ in range(3):
                internet_set_option(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
                internet_set_option(0, INTERNET_OPTION_REFRESH, 0, 0)
                time.sleep(0.1)
            
            return True
        except Exception as e:
            print(f"[Proxy] 通知系统失败: {e}")
            return False
    
    def save_current_settings(self):
        """保存当前的代理设置"""
        try:
            self.original_proxy_enable = self._read_registry_value(
                self.INTERNET_SETTINGS, "ProxyEnable", 0
            )
            self.original_proxy_server = self._read_registry_value(
                self.INTERNET_SETTINGS, "ProxyServer", ""
            )
            self.original_proxy_override = self._read_registry_value(
                self.INTERNET_SETTINGS, "ProxyOverride", ""
            )
            
            print(f"[Proxy] 已保存原始代理设置:")
            print(f"  - ProxyEnable: {self.original_proxy_enable}")
            print(f"  - ProxyServer: {self.original_proxy_server}")
            
            return True
        except Exception as e:
            print(f"[Proxy] 保存原始设置失败: {e}")
            return False
    
    def enable_proxy(self, proxy_server="127.0.0.1:7890", bypass_list="localhost;127.*;10.*;172.16.*;172.31.*;192.168.*;*.cn;*.alipay.com;*.taobao.com;*.tmall.com;*.jd.com;*.baidu.com;*.qq.com"):
        """
        启用系统代理（优化版）
        
        Args:
            proxy_server: 代理服务器地址
            bypass_list: 绕过代理的地址（包含国内常见域名）
        """
        try:
            if self.original_proxy_enable is None:
                self.save_current_settings()
            
            # 🔥 关键：确保先禁用再启用，避免残留配置
            self._write_registry_value(
                self.INTERNET_SETTINGS,
                "ProxyEnable",
                0,
                winreg.REG_DWORD
            )
            time.sleep(0.2)
            
            # 设置代理服务器
            success = self._write_registry_value(
                self.INTERNET_SETTINGS,
                "ProxyServer",
                proxy_server,
                winreg.REG_SZ
            )
            
            if not success:
                return False
            
            # 设置绕过列表（国内域名直连）
            self._write_registry_value(
                self.INTERNET_SETTINGS,
                "ProxyOverride",
                bypass_list,
                winreg.REG_SZ
            )
            
            # 启用代理
            success = self._write_registry_value(
                self.INTERNET_SETTINGS,
                "ProxyEnable",
                1,
                winreg.REG_DWORD
            )
            
            if not success:
                return False
            
            # 通知系统（多次确保生效）
            self._notify_system()
            
            # 等待系统应用设置
            time.sleep(0.5)
            
            # 验证设置是否生效
            current_enable = self._read_registry_value(
                self.INTERNET_SETTINGS, "ProxyEnable", 0
            )
            current_server = self._read_registry_value(
                self.INTERNET_SETTINGS, "ProxyServer", ""
            )
            
            if current_enable == 1 and current_server == proxy_server:
                print(f"[Proxy] ✅ 系统代理已启用: {proxy_server}")
                print(f"[Proxy] 绕过列表: {bypass_list[:50]}...")
                return True
            else:
                print(f"[Proxy] ⚠️ 代理设置可能未完全生效")
                return False
            
        except Exception as e:
            print(f"[Proxy] ❌ 启用代理失败: {e}")
            return False
    
    def disable_proxy(self):
        """禁用系统代理（恢复原始设置）"""
        try:
            if self.original_proxy_enable is None:
                print("[Proxy] ⚠️ 没有保存的原始设置，将完全禁用代理")
                self.original_proxy_enable = 0
                self.original_proxy_server = ""
                self.original_proxy_override = ""
            
            # 恢复代理启用状态
            self._write_registry_value(
                self.INTERNET_SETTINGS,
                "ProxyEnable",
                self.original_proxy_enable,
                winreg.REG_DWORD
            )
            
            # 恢复代理服务器
            if self.original_proxy_server:
                self._write_registry_value(
                    self.INTERNET_SETTINGS,
                    "ProxyServer",
                    self.original_proxy_server,
                    winreg.REG_SZ
                )
            
            # 恢复绕过列表
            if self.original_proxy_override:
                self._write_registry_value(
                    self.INTERNET_SETTINGS,
                    "ProxyOverride",
                    self.original_proxy_override,
                    winreg.REG_SZ
                )
            
            # 通知系统
            self._notify_system()
            
            time.sleep(0.3)
            
            print("[Proxy] ✅ 系统代理已恢复到原始状态")
            return True
            
        except Exception as e:
            print(f"[Proxy] ❌ 恢复代理失败: {e}")
            return False
    
    def get_current_proxy(self):
        """获取当前的代理设置"""
        try:
            proxy_enable = self._read_registry_value(
                self.INTERNET_SETTINGS, "ProxyEnable", 0
            )
            proxy_server = self._read_registry_value(
                self.INTERNET_SETTINGS, "ProxyServer", ""
            )
            
            if proxy_enable and proxy_server:
                return f"已启用: {proxy_server}"
            else:
                return "未启用"
                
        except Exception as e:
            print(f"[Proxy] 获取当前代理失败: {e}")
            return "未知"


# 全局实例
_proxy_manager = None

def get_proxy_manager():
    """获取全局代理管理器实例"""
    global _proxy_manager
    if _proxy_manager is None:
        _proxy_manager = WindowsProxyManager()
    return _proxy_manager

def enable_system_proxy():
    """启用系统代理"""
    manager = get_proxy_manager()
    return manager.enable_proxy()

def disable_system_proxy():
    """禁用系统代理"""
    manager = get_proxy_manager()
    return manager.disable_proxy()

def get_current_proxy_status():
    """获取当前代理状态"""
    manager = get_proxy_manager()
    return manager.get_current_proxy()