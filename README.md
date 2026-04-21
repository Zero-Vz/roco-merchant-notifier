# 洛克王国世界：远行商人自动提醒助手 🛒

![License](https://img.shields.io/github/license/你的用户名/Roco-Merchant)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Actions](https://img.shields.io/badge/GitHub-Actions-orange)

这是一个基于 **GitHub Actions** 的轻量化自动化工具，专门用于监控《洛克王国世界》中“远行商人”的刷新状态。每当商人带着稀有道具或精灵刷新时，系统会自动抓取图文数据，并精准推送到你的手机（支持 iOS 和 Android）。

### ✨ 特性

* **云端运行**：无需本地挂机，由 GitHub Actions 自动触发，0 成本、0 维护。
* **多端适配**：完美支持 **Bark (iOS)** 和 **NotifyMe (Android)**，可根据需求自行选择或双端同时推送。
* **富文本排版**：推送内容包含道具/精灵图标，支持 Markdown 渲染，视觉体验直观。
* **安全脱敏**：采用 GitHub Secrets 管理 API Key 和推送 ID，代码公开也无须担心隐私泄露。
* **准时触发**：支持 GitHub Cron 触发，并推荐配合 `cron-job.org` 实现秒级准时推送。

---

### 🚀 快速上手

#### 1. Fork 仓库或创建新仓库
点击页面右上角的 `Fork` 按钮，将本项目复制到你的账号下；或者直接新建一个私有/公开仓库，并上传 `main.py`。

#### 2. 申请 API Key
本项目的数据源由 [Entropy-Increase-Team](https://github.com/Entropy-Increase-Team/) 提供。
你需要前往该项目主页或相关社区，获取用于调用 WeGame 接口的 `ROCOM_API_KEY`。

#### 3. 配置 GitHub Secrets (核心步骤)
进入你的仓库设置：`Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`，依次添加以下变量：

| 变量名 | 是否必填 | 说明 |
| :--- | :--- | :--- |
| `ROCOM_API_KEY` | **是** | 游戏数据接口的 API Key |
| `NOTIFYME_UUID` | 选填 | NotifyMe (Android) 的设备 UUID |
| `BARK_KEY` | 选填 | Bark (iOS) 的专属推送 Key |

> **提示**：NotifyMe 和 Bark 至少需要配置一个，脚本才会发送推送。

#### 4. 开启 GitHub Actions
点击仓库上方的 `Actions` 选项卡，确保它已启用（点击 `I understand my workflows, go ahead and enable them`）。

---

### ⏰ 定时任务说明

本项目默认在 `.github/workflows/schedule.yml` 中配置了 GitHub 定时任务，对应北京时间 **08:00、12:00、16:00、20:00** 运行。

**💡 进阶技巧：如何保证秒级准时？**
由于 GitHub 官方的 Cron 触发存在排队延迟（可能延迟 5-30 分钟），追求极致准时的玩家可以：
1.  在 [cron-job.org](https://cron-job.org/) 创建任务。
2.  配置 POST 请求通过 GitHub API 远程触发本项目的 `workflow_dispatch`。
3.  详细教程可参考 [新闻联播文字稿自动化推送系统](https://github.com/ALLCAPS-Droid/xin-wen-lian-bo)。

---

### 🛠️ 技术实现

* **数据层**：调用 `wegame.shallow.ink` 的开放 API。
* **逻辑层**：使用 Python 3.10 处理 JSON 数据并生成 Markdown 模板。
* **推送层**：适配 NotifyMe 新版 UUID 协议及 Bark HTTP 请求协议。

---

### ⚖️ 免责声明
本项目仅供学习交流使用，数据来源于第三方开源社区。作者对接口的稳定性不作保证，请勿用于商业用途。

---

### 🤝 致谢
感谢 [Entropy-Increase-Team](https://github.com/Entropy-Increase-Team) 提供的洛克王国数据网关支持。
