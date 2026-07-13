"""
每日 IT 知识点
通过 AI 生成一个随机的 IT 技术知识点（一句话 + 一小段说明）
"""
import json
import random
import urllib.request
import urllib.error

# 本地兜底知识点（AI 调用失败时随机选一个）
FALLBACK_KNOWLEDGE = [
    {
        "title": "HTTP/2 多路复用",
        "description": "HTTP/2 允许在单个 TCP 连接上并发发送多个请求和响应，避免了 HTTP/1.1 的队头阻塞问题，大幅提升页面加载速度。服务器还可以主动推送资源给客户端。",
    },
    {
        "title": "Docker 层缓存机制",
        "description": "Docker 镜像由多个只读层组成，每一条 Dockerfile 指令创建一个新层。构建时会复用未变化的层缓存，因此把不常变动的依赖安装放在前面，可以显著加速构建。",
    },
    {
        "title": "Python GIL 全局解释器锁",
        "description": "CPython 的 GIL 保证同一时刻只有一个线程执行 Python 字节码。这意味着多线程在 CPU 密集型任务中无法利用多核，但 I/O 密集型任务仍能受益于线程切换。多进程或使用 C 扩展可以绕过 GIL。",
    },
    {
        "title": "HTTPS 握手过程",
        "description": "TLS 握手时：客户端发送支持的密码套件 → 服务器选择加密方式并返回证书 → 双方通过非对称加密交换密钥 → 后续通信使用对称加密。整个过程通常耗时 1-2 个 RTT。",
    },
    {
        "title": "SQL 索引的 B+ 树结构",
        "description": "关系型数据库常用 B+ 树作为索引结构。所有数据存在叶子节点，叶子节点之间通过指针相连形成有序链表，非叶子节点只存键值用于导航。这使得范围查询和全表扫描都很高效。",
    },
    {
        "title": "Git rebase vs merge",
        "description": "merge 保留完整的分支历史，产生一个合并提交；rebase 将当前分支的提交「嫁接」到目标分支顶部，历史更线性整洁。公共分支推荐 merge，个人分支可用 rebase 保持整洁。",
    },
    {
        "title": "Redis 持久化：RDB vs AOF",
        "description": "RDB 是定时快照，适合备份恢复，但可能丢失最近数据；AOF 记录每条写命令，数据更安全但文件更大。生产环境通常两者结合使用：RDB 做冷备，AOF 保证数据不丢。",
    },
    {
        "title": "微服务中的服务发现",
        "description": "服务发现让微服务能动态找到彼此的位置。客户端模式由调用方查询注册中心（如 Eureka）；服务端模式通过负载均衡代理转发（如 Kubernetes Service）。Consul、Nacos 等同时支持健康检查和配置管理。",
    },
    {
        "title": "Linux /proc 文件系统",
        "description": "/proc 是一个伪文件系统，不占用磁盘，是内核数据结构的窗口。比如 /proc/cpuinfo 显示 CPU 信息，/proc/meminfo 显示内存信息，/proc/[pid]/ 目录下可以查看任意进程的详细运行状态。",
    },
    {
        "title": "CORS 跨域资源共享",
        "description": "浏览器同源策略阻止页面请求不同源的资源。CORS 通过服务器设置响应头（Access-Control-Allow-Origin 等）来声明允许哪些源跨域访问。预检请求（OPTIONS）用于检查非简单请求是否被允许。",
    },
    {
        "title": "JWT 的结构与工作原理",
        "description": "JSON Web Token 由三部分组成：Header（算法类型）、Payload（声明数据）、Signature（签名）。用 base64 编码后以点号连接。服务端验证签名即可确认令牌未被篡改，无需查询数据库。",
    },
    {
        "title": "TCP 三次握手与四次挥手",
        "description": "建立连接需三次握手：SYN → SYN-ACK → ACK。断开连接需四次挥手：FIN → ACK → FIN → ACK。TIME_WAIT 状态持续 2MSL 确保最后的 ACK 能被对方收到，同时让旧连接的残留报文在网络中消失。",
    },
    {
        "title": "Kubernetes Pod 的生命周期",
        "description": "Pod 状态从 Pending（调度中）→ Running（运行中）→ Succeeded/Failed（终止）。容器有 postStart 和 preStop 钩子，终止时会先发 SIGTERM 等待优雅关闭，超时后发 SIGKILL 强制杀死。",
    },
    {
        "title": "CDN 内容分发网络原理",
        "description": "CDN 将静态资源缓存到全球各地的边缘节点，用户请求被智能 DNS 解析到最近的节点。源站只需推送一次，边缘节点负责分发，兼具加速和抗 DDoS 的效果。适合图片、JS/CSS、视频等场景。",
    },
    {
        "title": "消息队列的三种消费模式",
        "description": "点对点：一条消息只被一个消费者处理；发布/订阅：一条消息被所有订阅者收到；流式处理：按分区顺序消费。Kafka 适合高吞吐日志，RabbitMQ 适合复杂路由，RocketMQ 适合金融级可靠性。",
    },
    {
        "title": "OAuth 2.0 授权码模式",
        "description": "最安全的 OAuth 流程：用户点击授权 → 跳转授权服务器 → 返回授权码（一次性）→ 后端用授权码换 access_token → 用 token 访问资源。授权码不经过浏览器前端，避免 token 泄露。",
    },
    {
        "title": "正则表达式回溯陷阱",
        "description": "嵌套量词如 (a+)+b 在匹配失败时会导致灾难性回溯，时间复杂度可达 O(2^n)。攻击者可利用此构造 ReDoS 攻击。解决方法是使用占有量词（++）、原子组或改用确定性有限自动机。",
    },
    {
        "title": "数据库事务隔离级别",
        "description": "四种级别从低到高：读未提交（脏读）、读已提交（不可重复读）、可重复读（幻读）、串行化。MySQL InnoDB 默认可重复读，通过 MVCC 和间隙锁解决幻读；PostgreSQL 默认读已提交。",
    },
    {
        "title": "WebSocket 与 HTTP 长轮询",
        "description": "WebSocket 是全双工协议，一次握手后保持连接，服务端可主动推送；长轮询是客户端发请求后服务端 hold 住直到有数据才返回。WebSocket 开销更低，但需要客户端和代理支持。",
    },
    {
        "title": "设计模式：单例模式的实现",
        "description": "单例确保一个类只有一个实例并提供全局访问点。Python 中常用模块级变量（模块天然单例）、__new__ 方法控制、或装饰器实现。多线程下需加锁，但 Python 的 import 自带线程安全。",
    },
]


def fetch_knowledge(api_key: str) -> dict:
    """
    通过 AI 生成一个随机的 IT 知识点
    返回: {"success": True, "title": "...", "description": "..."}
    """
    if not api_key:
        return _fallback()

    prompt = (
        "请生成一个随机的IT/计算机技术知识点。"
        "要求：标题是一句话（10-20字），说明是一小段话（80-150字），要实用、有干货。"
        "主题可以涵盖：编程语言、网络、操作系统、数据库、云计算、容器、安全、算法、架构设计等。"
        "每次生成不同的主题，不要重复常见内容。"
        "请严格按JSON格式返回：{\"title\": \"...\", \"description\": \"...\"}"
    )

    payload = json.dumps({
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": "你是一个IT知识科普助手，每次生成一个不同的IT技术知识点。请严格返回JSON格式。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.9,
        "max_tokens": 300,
        "thinking": {"type": "disabled"},
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"].get("content", "").strip()

            # 清理可能的 markdown 代码块包裹
            if content.startswith("```"):
                content = content.split("\n", 1)[-1]
                if content.endswith("```"):
                    content = content[:-3].strip()
                # 去掉可能的 json 标记
                if content.startswith("json\n"):
                    content = content[5:]

            result = json.loads(content)
            title = result.get("title", "").strip()
            desc = result.get("description", "").strip()

            if title and desc:
                return {"success": True, "title": title, "description": desc}
            else:
                return _fallback()

    except json.JSONDecodeError:
        # AI 返回格式问题，用兜底
        return _fallback()
    except urllib.error.URLError:
        return _fallback()
    except Exception:
        return _fallback()


def _fallback() -> dict:
    """随机选一个本地兜底知识点"""
    item = random.choice(FALLBACK_KNOWLEDGE)
    return {"success": True, "title": item["title"], "description": item["description"]}
