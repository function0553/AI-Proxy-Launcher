# AI Proxy Launcher
- AI ChatGPT Grok Gemini Cluade 代理 VPN 魔法上网
- AI Proxy Launcher 是一个支持 Clash 节点管理的工具，旨在简化代理节点的配置和切换，适用于中国大陆等地区的代理需求。该项目提供了一个简易的用户界面，允许用户通过输入 Clash 订阅链接，自动更新代理配置，并选择和切换代理节点。
- 项目结构：
- AI-Proxy-Launcher/
- │
- ├── clash/
- │   └── clash-core.exe
- ├── config/
- │   └── config.yaml
- ├── resources/
- │   └── clash-core.exe
- ├── src/
- │   ├── clash_runner.py
- │   ├── clashn_format.py
- │   ├── update_manager.py
- │   ├── windows_proxy.py
- │   ├── yaml_merge.py
- │   └── freeclash_fetch.py
- ├── index.html
- ├── nodes.html
- ├── README.md
- └── LICENSE

## 功能概述

- 支持 Clash 节点自动更新。
- 提供一个简易的界面来选择代理节点。
- 自动启用系统代理，支持浏览器直接使用代理。
- 支持定时更新和自定义代理配置。
- 兼容多个代理服务，如 Gemini、ChatGPT、Clash 和 Sing-Box 等。

## 安装与配置

### 环境要求

- Python 3.7 及以上版本
- Windows 操作系统
- 必要的 Python 库：
  - `requests`
  - `beautifulsoup4`
  - `pyinstaller`（用于打包）

### 安装步骤

1. **克隆仓库**：
    ```bash
    git clone https://github.com/function0553/ai-proxy-launcher.git
    cd ai-proxy-launcher
    ```

2. **安装依赖**：
    ```bash
    pip install -r requirements.txt
    ```

3. **配置 Clash**：
    确保将 `clash-core.exe` 放在 `clash` 文件夹下，并配置好 `config.yaml` 文件。

4. **运行程序**：
    运行以下命令启动代理：
    ```bash
    python clash_runner.py
    ```

5. **打包 EXE 文件**：
    如果需要将程序打包为 EXE 文件，可以使用 PyInstaller：
    ```bash
    pyinstaller --onefile clash_runner.py
    ```

### 使用步骤

1. **输入订阅链接**：在主界面输入 Clash 订阅链接并点击 "更新配置"。
2. **选择节点**：点击 "节点选择" 页面，选择一个节点。
3. **启用代理**：选中节点后，系统会自动启用代理，所有浏览器都可以通过该代理访问互联网。

## 功能介绍

### 1. 节点选择

你可以从 "节点选择" 页面选择你希望使用的代理节点。选择后，代理将立即生效，并可以在浏览器中使用。

### 2. 自动更新

系统会定期检查 Clash 配置的更新，并自动下载最新的节点配置，确保你的代理节点始终是最新的。

### 3. 系统代理管理

系统会自动启用 Windows 的系统代理设置，并允许你在不同的节点之间切换。
#### 4.目前版本为1.0

## 开发与贡献

我们欢迎开发者贡献代码！如果你发现 bug 或者有改进的建议，欢迎提交 Issue 或者 Pull Request。

### 如何贡献

1. **Fork** 本仓库。
2. 创建自己的分支：
    ```bash
    git checkout -b feature-branch
    ```
3. 提交你的修改：
    ```bash
    git commit -am "Add new feature"
    ```
4. 推送并创建 Pull Request。

## 许可证

本项目采用 MIT 许可证，详情请参见 [LICENSE](LICENSE) 文件。

