# 📋 每日新闻速览 · 邮件推送

每天早上 10:00 自动推送精美邮件到你的邮箱，包含天气、热点、新闻、微语。

## 📊 内容板块

| 板块 | 数据源 | 数量 |
|------|--------|:---:|
| ☀️ 天气 | [wttr.in](https://wttr.in) | 今日天气 |
| 🔥 热点事件 | 微博热搜 + 百度热搜 + 知乎热榜 + 头条热榜 | 各 5 条 |
| 🏛️ 国内要闻 | 人民网 / 新华网 / 澎湃 RSS | 3 条 |
| 💹 经济消费 | 新浪财经 / 第一财经 RSS | 3 条 |
| 🔬 科技教育 | 36氪 / 虎嗅 / 少数派 RSS | 3 条 |
| 🌍 国际观察 | 环球网 / 参考消息 RSS | 3 条 |
| 💬 每日微语 | Hitokoto 一言 API | 1 条 |
| 📅 节日倒计时 | 本地计算 + 农历 | 自动 |

> 所有数据源免费，无需任何 API Key！

## 🚀 快速开始

### 1. 获取 163 邮箱 SMTP 授权码

登录 [mail.163.com](https://mail.163.com) → 设置 → POP3/SMTP/IMAP → 开启 SMTP 服务 → 新增授权码

### 2. Fork 或克隆本项目

### 3. 配置 GitHub Secrets

进仓库 Settings → Secrets and variables → Actions → 添加 3 个 secret：

| Name | Value |
|------|-------|
| `SMTP_USER` | 你的 163 邮箱地址 |
| `SMTP_PASSWORD` | 163 SMTP 授权码 |
| `TO_EMAIL` | 收件邮箱（多个用逗号分隔） |

### 4. 启用 Actions

Actions → Daily Email Push → Enable workflow

每天北京时间 10:00 自动发送，也可以在 Actions 页面手动触发测试。

## 🧪 本地测试

```bash
pip install -r requirements.txt

# 设置环境变量后运行
SMTP_USER=xxx@163.com SMTP_PASSWORD=xxxx TO_EMAIL=xxx@qq.com python main.py
```

## 📝 配置说明

编辑 `config.yaml`：

- `weather.city` — 天气城市
- `sections.xxx` — 板块开关（true/false）
- `limits.hot_events` — 每个热点源取几条
- `limits.news_per_category` — 每类新闻取几条

## 📧 多邮箱推送

在 `TO_EMAIL` secret 中用逗号分隔即可：

```
2390826485@qq.com, another@qq.com, third@gmail.com
```
