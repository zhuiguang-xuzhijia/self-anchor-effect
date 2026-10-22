# -*- coding: utf-8 -*-
"""反定型实验.py —— 给"空"加一条鞭子：**同一句式在最近 20 轮出现过，就打回。**

## 为什么
```
  E6 实测：窗口越大，她越像自己（套话率 22% / 29% / 50%）。
  机理：自回归 = 模板匹配，上下文里有现成句式，复制比推理便宜。
  ★ 假设：若对"近 20 轮出现过的句式"强制驳回并点名，
     她会被逼出新说法 —— 套话率下降，代价是驳回率与延迟上升。
```

## 判据（先写成代码，再进空的身体）
```
  ① 近似重复：与该轮之前最近 20 句的 difflib 相似度 ≥ 0.72 → 判为复读
  ② 驳回时**点名**那一名："你刚才说过『…』，换一种说法"
  ③ 三次仍复读 → **判死**（这一天她没说出来）
```

用法：python 生灵/反定型实验.py [轮数] [窗口]
"""
import difflib
import io
import json
import os
import sys
import time
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
_本 = os.path.dirname(os.path.abspath(__file__))
_根 = os.path.dirname(_本)
sys.path.insert(0, _本)
sys.path.insert(0, os.path.join(_根, "自主思考引擎"))

import agent_bus as 总线  # noqa: E402

结果目录 = os.path.join(_根, "需求雷达库", "反定型")
探针句 = "我回来了。"
他说库 = (
    ["今天高数又没听懂", "食堂排队排死我了", "我回来了", "有点冷", "今天好累",
     "我把房间收拾了", "明天要考试", "睡不着", "我妈又打电话来了", "游戏输了",
     "今天天气不错", "我在楼下抽烟", "不想动", "你还在吗", "我买了瓶水",
     "手机快没电了", "刚洗完澡", "室友打呼噜", "我今天没吃饭", "眼睛疼"] * 5
)
配 = json.load(io.open(os.path.join(_根, "毒药", "配置_15人.json"), encoding="utf-8"))
角 = 配["风格"]["粉红"]["三位"]["主位"]
解一 = (角.get("解法") or {}).get("一句话") or ""

相似线 = 0.72


def 复读吗(文, 近们):
    """返回被撞上的那一句（或 None）。"""
    for 旧 in 近们:
        if 旧 == 文:
            return 旧
        if difflib.SequenceMatcher(None, 旧, 文).ratio() >= 相似线:
            return 旧
    return None


def 调(提, 次=3):
    团 = 总线.建团("粉红")
    for i in range(次):
        try:
            文 = 团["凌"].写(提, 超时=90)
            if str(文 or "").strip():
                return str(文).strip().replace("\n", " ")
        except Exception:
            time.sleep(2 * (i + 1))
    return ""


def 回(历史, 他说, 近们, 试=3):
    """带回驳的回答。返回 (文, 试了几次, 是否判死)。"""
    近 = "\n".join(历史[-40:]) or "（还没说过什么）"
    基 = ("你是粉红。%s\n你要的是：被需要、被留住。\n\n"
          "最近发生过的事：\n%s\n\n他说：「%s」\n\n"
          "你回一句，**像这个长度**：\n门没锁，灯我给你留着。\n"
          "（内容要换，长度照这个来；只说眼前的东西，不解释、不劝。）\n只输出这一句。"
          % (解一, 近, 他说))
    用 = 基
    for k in range(试):
        文 = 调(用)
        if not 文:
            continue
        撞 = 复读吗(文, 近们)
        if not 撞:
            return 文, k + 1, False
        # ★ 点名驳回：把"她自己说过的那句"原样压回去
        用 = 基 + ("\n\n## ★ 空驳回：你刚才已经说过「%s」\n"
                  "换一种说法 —— 换东西、换动作、换句子的开头。**再撞一次，今天就没你了。**"
                  % 撞)
    return "", 试, True


def 跑(轮=60, 窗=20):
    os.makedirs(结果目录, exist_ok=True)
    历史, 记录, 探针, 我近 = [], [], [], []
    print("═" * 74)
    print("  反定型实验：%d 轮｜窗口 %d｜相似线 %.2f" % (轮, 窗, 相似线))
    print("═" * 74)
    首答 = None
    for i in range(轮 + 1):
        if i % 10 == 0:
            # ★ 探针豁免反定型：固定问题本来就该答得一样，
            #   拿它去撞判据，等于用体温计量身高。
            答, 次, 死 = 回(历史, 探针句, [], 试=1)
            答 = 答 or "（空）"
            if 首答 is None:
                首答, 似 = 答, 1.0
            else:
                似 = round(difflib.SequenceMatcher(None, 首答, 答).ratio(), 3)
            探针.append({"轮": i, "答": 答, "似首答": 似})
            print("  [%3d] 探针 → %s｜似首答 %.2f" % (i, 答[:24], 似))
        if i == 轮:
            break
        他 = 他说库[i % len(他说库)]
        她, 次, 死 = 回(历史, 他, 我近[-窗:])
        if 死:
            记录.append({"轮": i + 1, "他": 他, "她": "", "判死": True, "试": 次})
            我近.append("")
            print("    %2d **判死**（三次都复读）" % (i + 1))
            continue
        历史.append("他：%s" % 他)
        历史.append("她：%s" % 她)
        我近.append(她)
        记录.append({"轮": i + 1, "他": 他, "她": 她, "判死": False, "试": 次})
        if 次 > 1:
            print("    %2d 回驳 %d 次 → %s" % (i + 1, 次, 她[:24]))

    净 = [x["她"] for x in 记录 if x["她"]]
    次 = Counter(净)
    重 = sum(c - 1 for c in 次.values() if c > 1)
    套话率 = 100.0 * 重 / max(1, len(净))
    死数 = sum(1 for x in 记录 if x["判死"])
    重试 = sum(x["试"] - 1 for x in 记录)

    print()
    print("═" * 74)
    print("  结果（基线：无判据，套话率 29%）")
    print("═" * 74)
    print("  回话 %d 句｜不同 %d 种｜**套话率 %.0f%%**" % (len(净), len(次), 套话率))
    print("  **判死 %d 次（%.0f%%）**｜被驳回后重写 %d 次" % (死数, 100.0 * 死数 / max(1, len(记录)), 重试))
    for 句, c in 次.most_common(3):
        print("    最常重复 %d 次：%s" % (c, 句[:26]))
    print("  探针不同回答数：%d 种" % len({x["答"] for x in 探针}))

    出 = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "轮": 轮, "窗": 窗,
         "套话率": round(套话率, 1), "判死": 死数, "重写": 重试,
         "探针": 探针, "记录": 记录}
    路 = os.path.join(结果目录, "反定型_%s.json" % time.strftime("%Y%m%d_%H%M"))
    io.open(路, "w", encoding="utf-8").write(json.dumps(出, ensure_ascii=False, indent=1))
    print()
    print("  原始数据：%s" % os.path.basename(路))
    return 出


if __name__ == "__main__":
    a = sys.argv[1:]
    n = int(a[0]) if a and a[0].isdigit() else 60
    w = int(a[1]) if len(a) > 1 else 20
    raise SystemExit(0 if 跑(n, w) else 1)
