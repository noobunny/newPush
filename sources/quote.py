import random
import requests

# Hitokoto 一言 API 分类参数说明:
# a-动漫 b-漫画 c-游戏 d-文学 e-原创 f-来自网络 g-其他 h-影视 i-诗词 j-网易云 k-哲学 l-抖机灵
# 只用 d(文学) i(诗词) k(哲学)，这几个分类质量最高，几乎不混二次元
QUOTE_CATEGORIES = ["d", "i", "k"]

# 需要过滤的二次元/游戏来源关键词
BLOCK_SOURCES = [
    "二次元", "动漫", "游戏", "刀酱", "原神", "崩坏", "王者", "和平精英",
    "明日方舟", "碧蓝", "FGO", "fgo", "LOL", "lol", "DNF", "dnf",
    "B站", "bilibili", "番剧", "轻小说", "galgame", "Galgame",
]

# 备用微语池 — 名人名言 + 幽默搞笑 + 哲理
FALLBACK_QUOTES = [
    {"text": "世界上只有一种真正的英雄主义，那就是在认清生活真相之后依然热爱生活。", "source": "罗曼·罗兰"},
    {"text": "生活不是等待暴风雨过去，而是学会在雨中起舞。", "source": "佚名"},
    {"text": "人生的意义不在于拿到一手好牌，而在于打好一手烂牌。", "source": "佚名"},
    {"text": "种一棵树最好的时间是十年前，其次是现在。", "source": "非洲谚语"},
    {"text": "我们读过的书，走过的路，最终都会成为我们的一部分。", "source": "佚名"},
    {"text": "保持好奇心，是永葆青春的秘诀。", "source": "爱因斯坦"},
    {"text": "你不必生来勇敢，天赋过人。只要能投入勤奋，诚诚恳恳。", "source": "佚名"},
    {"text": "今天不想跑，所以才去跑。这才是长距离跑者的思维方式。", "source": "村上春树"},
    {"text": "大部分人在二三十岁就已经死去了，因为过了这个年龄，他们只是自己的影子。", "source": "罗曼·罗兰"},
    {"text": "一个人知道自己为什么而活，就可以忍受任何一种生活。", "source": "尼采"},
    {"text": "世界上最快乐的事，莫过于为理想而奋斗。", "source": "苏格拉底"},
    {"text": "聪明是一种天赋，而善良是一种选择。", "source": "杰夫·贝索斯"},
    {"text": "如果你的面前有阴影，那是因为你的背后有阳光。", "source": "佚名"},
    {"text": "不要因为走得太远，而忘记为什么出发。", "source": "纪伯伦"},
    {"text": "每一个不曾起舞的日子，都是对生命的辜负。", "source": "尼采"},
    {"text": "要么你去驾驭生命，要么生命驾驭你。你的心态决定谁是坐骑，谁是骑师。", "source": "佚名"},
    {"text": "当你觉得为时已晚的时候，恰恰是最早的时候。", "source": "佚名"},
    {"text": "你现在的气质里，藏着你走过的路，读过的书和爱过的人。", "source": "《卡萨布兰卡》"},
    {"text": "活着就是为了改变世界，难道还有其他原因吗？", "source": "乔布斯"},
    {"text": "愿你在被打击时，记起你的珍贵，抵抗恶意；愿你在迷茫时，坚信你的珍贵。", "source": "《无问西东》"},
    {"text": "真正的自由不是想做什么就做什么，而是不想做什么就不做什么。", "source": "康德"},
    {"text": "你成为今天的你，定是因为一些事的发生。它们或大或小，但必定在你的记忆中留下了烙印。", "source": "克莱儿·麦克福尔"},
    {"text": "只要有想见的人，就不再是孤身一人。", "source": "《夏目友人帐》"},
    {"text": "把自己活成一道光，因为你不知道，谁会借着你的光，走出了黑暗。", "source": "泰戈尔"},
    {"text": "对未来的真正慷慨，是把一切都献给现在。", "source": "加缪"},
    {"text": "没有不可治愈的伤痛，没有不能结束的沉沦，所有失去的，会以另一种方式归来。", "source": "约翰·肖尔斯"},
    {"text": "人这一生，自私很容易，爱自己却很难。", "source": "佚名"},
    {"text": "所谓无底深渊，下去，也是前程万里。", "source": "木心"},
    {"text": "心之所向，素履以往；生如逆旅，一苇以航。", "source": "七堇年"},
    {"text": "我走得很慢，但我从不后退。", "source": "林肯"},
    {"text": "满地都是六便士，他却抬头看见了月亮。", "source": "毛姆"},
    {"text": "人要是不那么死心眼，不那么执着地去追忆往昔的不幸，会更多考虑如何应对现实。", "source": "笛福"},
    {"text": "家人闲坐，灯火可亲。", "source": "汪曾祺"},
    {"text": "生活总是让我们遍体鳞伤，但到后来，那些受伤的地方一定会变成我们最强壮的地方。", "source": "海明威"},
    {"text": "我是个百依百顺的孩子，至死不变，但只顺从我自己。", "source": "萨特"},
    {"text": "每个人都会死，但不是每个人都真正活过。", "source": "《勇敢的心》"},
    {"text": "你见过凌晨四点的洛杉矶吗？", "source": "科比"},
    {"text": "不要努力成为一个成功者，努力成为一个有价值的人。", "source": "爱因斯坦"},
    {"text": "弱小和无知不是生存的障碍，傲慢才是。", "source": "《三体》"},
    {"text": "给时光以生命，而不是给生命以时光。", "source": "帕斯卡"},
]


def _is_quality_quote(text: str, source: str) -> bool:
    """检查微语质量：太短、太口语化(如'我不道啊')、或来自二次元/游戏来源则不合格"""
    if len(text) < 8:
        return False
    # 过滤过于口语化的短句
    junk_patterns = ["我不道", "不知道啊", "草", "哈哈", "卧槽"]
    for p in junk_patterns:
        if p in text:
            return False
    # 过滤二次元/游戏来源
    for kw in BLOCK_SOURCES:
        if kw.lower() in source.lower():
            return False
    return True


def fetch_quote() -> dict:
    """从 Hitokoto 一言 API 获取每日微语（文学/诗词/哲学类，自动过滤二次元）"""
    # 尝试 3 次，每次随机选不同分类
    for attempt in range(3):
        try:
            category = random.choice(QUOTE_CATEGORIES)
            resp = requests.get(
                "https://v1.hitokoto.cn/",
                params={"c": category},
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            resp.raise_for_status()
            data = resp.json()
            text = data.get("hitokoto", "").strip()
            source = data.get("from", "").strip()

            if _is_quality_quote(text, source):
                return {
                    "success": True,
                    "text": text,
                    "source": source if source else "佚名",
                }
        except Exception:
            continue

    # API 全部不合格或失败时从备用池取
    fb = random.choice(FALLBACK_QUOTES)
    return {
        "success": True,
        "text": fb["text"],
        "source": fb["source"],
    }
