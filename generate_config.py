import os
import yaml
from core.yaml_merge import merge_subscriptions

def generate_config_from_url(sub_url):
    """
    下载用户输入的订阅链接并合并生成 config.yaml
    """
    if not sub_url or not sub_url.strip():
        raise ValueError("订阅链接不能为空")
    
    sub_url = sub_url.strip()
    if not sub_url.startswith("http"):
        raise ValueError("请输入有效的 HTTP/HTTPS 链接")

    print(f"[Config] 正在获取订阅内容: {sub_url}")
    
    try:
        # 传入 URL 列表给合并工具
        config_data = merge_subscriptions([sub_url])
    except Exception as e:
        raise RuntimeError(f"解析订阅失败: {str(e)}")

    if not config_data or not config_data.get("proxies"):
        raise RuntimeError("该链接未返回任何有效的 Clash 节点")

    # 修复：使用项目根目录而不是当前文件目录
    # 获取当前工作目录（项目根目录）
    project_root = os.getcwd()
    config_dir = os.path.join(project_root, "config")
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "config.yaml")

    print(f"[Config] 配置将保存到: {config_path}")

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, allow_unicode=True, sort_keys=False)
    
    print(f"[Config] 配置已保存，共 {len(config_data.get('proxies', []))} 个节点")
    
    return config_path