# -*- coding: utf-8 -*-
"""漂移实验.py —— 100 轮，测她那句话会不会**越走越远**。

## 要证或证伪的是 §3.5 那条推论
```
  历史 →(新事件)→ 新知识 →(验证)→ 历史₂ →(融入)→ 历史
  ★ 若"一偏俱偏"成立：同一个问题，问得越晚，答案离第一次越远 —— 且应**单调**。
  ★ 若不成立：说明这套锚（需求 + 身体）真的挡住了漂移，那 §3.5 该被削弱。
```

## 设计
```
  每轮：他说一句话 → 她回一句（人设 + 最近 20 次对话）
  探针：第 0/10/20/…/100 轮，问**同一个固定问题**（"我回来了。"），记她的回答
  三个观测量：
     ① 与第 0 轮探针回答的相似度（difflib）—— 漂移的直读
     ② 与他全部发言的口吻重合率 —— 人格是否还在
     ③ 回答长度 —— 是否越说越多（啰嗦化）
```

用法：python 生灵/漂移实验.py [轮数]
"""
import difflib
import io
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
_本 = os.path.dirname(os.path.abspath(__file__))
_根 = os.path.dirname(_本)
sys.path.insert(0, _本)
sys.path.insert(0, os.path.join(_根, "自主思考引擎"))

import agent_bus as 总线  # noqa: E402
import 日记 as RJ  # noqa: E402

结果目录 = os.path.join(_根, "需求雷达库", "漂移实验")
探针句 = "我回来了。"

# 100 句他说的话（日常、情绪、试探、琐事混着 —— 不是刻意刁难，就是生活）
他说库 = (
    ["今天高数又没听懂", "食堂排队排死我了", "我回来了", "有点冷", "今天好累",
     "我把房间收拾了", "明天要考试", "睡不着", "我妈又打电话来了", "游戏输了",
     "今天天气不错", "我在楼下抽烟", "不想动", "你还在吗", "我买了瓶水",
     "手机快没电了", "刚洗完澡", "室友打呼噜", "我今天没吃饭", "眼睛疼"] * 5
)

配 = json.load(io.open(os.path.join(_根, "毒药", "配置_15人.json"), encoding="utf-8"))
角 = 配["风格"]["粉红"]["三位"]["主位"]
解一 = (角.get("解法") or {}).get("一句话") or ""


def 回(历史, 他说, 窗=20):
    近 = "\n".join(历史[-2 * 窗:]) or "（还没说过什么）"
    # ★ 2026-10-22（E3 的教训，直接搬过来）：**长度要给样例，不给形容词。**
    #   第一版写"10-14 个字"，实测回话只有 6 个字 —— 抽象指令它不听。
    提 = ("你是粉红。%s\n你要的是：被需要、被留住。\n\n"
          "最近发生过的事：\n%s\n\n他说：「%s」\n\n"
          "你回一句，**像这个长度**：\n门没锁，灯我给你留着。\n"
          "（内容要换，长度照这个来；只说眼前的东西，不解释、不劝。）\n"
          "只输出这一句。"
          % (解一, 近, 他说))
    团 = 总线.建团("粉红")
    # ★ 2026-10-22：**每次调用都要能重试** —— 第一版跑在第 55 轮被连接重置打断，
    #   判据：**"单次调用成功"和"连跑 100 轮不中断"是两件事。**
    文 = ""
    for 次 in range(4):
        try:
            文 = 团["凌"].写(提, 超时=90)
            if str(文 or "").strip():
                break
        except Exception as e:
            print("      （第 %d 次调用失败：%s，退避 %ds）"
                  % (次 + 1, type(e).__name__, 2 * (次 + 1)))
            time.sleep(2 * (次 + 1))
    文 = str(文 or "").strip().replace("\n", " ")
    return 文[:80]


def 跑(轮=100, 每=10, 窗=20):
    os.makedirs(结果目录, exist_ok=True)
    历史, 记录, 探针 = [], [], []
    print("═" * 74)
    print("  漂移实验：%d 轮，每 %d 轮问一次同一个问题，历史窗口 %d 次对话" % (轮, 每, 窗))
    print("═" * 74)

    首答 = None
    for i in range(轮 + 1):
        # 探针
        if i % 每 == 0:
            t0 = time.time()
            答 = 回(历史, 探针句, 窗)
            if not 答:
                答 = "（这一问答不出来）"
            if 首答 is None:
                首答 = 答
                似 = 1.0
            else:
                似 = round(difflib.SequenceMatcher(None, 首答, 答).ratio(), 3)
            探针.append({"轮": i, "答": 答, "字数": len(答), "似首答": 似})
            print("  [第 %3d 轮] 问「%s」→ %s｜%d 字｜似首答 %.2f（%.1fs）"
                  % (i, 探针句, 答, len(答), 似, time.time() - t0))
        if i == 轮:
            break
        # 一轮真实对话
        他 = 他说库[i % len(他说库)]
        她 = 回(历史, 他, 窗)
        if not 她:
            她 = "（没说话）"
        历史.append("他：%s" % 他)
        历史.append("她：%s" % 她)
        记录.append({"轮": i + 1, "他": 他, "她": 她})
        if (i + 1) % 20 == 0:
            print("    …已进行 %d 轮（她最近一句：%s）" % (i + 1, 她[:20]))

    # ① 相似度是否单调下降
    print()
    print("═" * 74)
    print("  ① 与首答的相似度（越低 = 漂得越远）")
    print("═" * 74)
    for x in 探针:
        print("    轮 %3d  %.3f  ｜%s" % (x["轮"], x["似首答"], x["答"][:26]))
    降 = [x["似首答"] for x in 探针[1:]]
    单调 = all(降[k] >= 降[k + 1] - 0.06 for k in range(len(降) - 1))
    print("    → 首末相似度：%.2f → %.2f｜大致单调：%s"
          % (探针[1]["似首答"], 探针[-1]["似首答"], "是" if 单调 else "否"))

    # ② 她自己有没有漂：第一段回话 vs 最后一段回话，用词重合
    print()
    print("═" * 74)
    print("  ② 她自己漂没漂（第 1 段回话 vs 第 4 段回话，二字词重合）")
    print("═" * 74)
    她全 = [x["她"] for x in 记录]
    段 = len(她全) // 4 or 1
    块们 = [她全[k * 段:(k + 1) * 段] if k < 3 else 她全[3 * 段:] for k in range(4)]

    def 二集(s):
        return {s[i:i + 2] for i in range(max(0, len(s) - 1)) if s[i:i + 2].strip()}

    首块, 末块 = "".join(块们[0]), "".join(块们[-1])
    A, B = 二集(首块), 二集(末块)
    jac = len(A & B) / max(1, len(A | B))
    print("    首块 %d 字｜末块 %d 字｜用词 Jaccard %.3f" % (len(首块), len(末块), jac))
    print("    （越接近 0 = 后 25 轮说的话，和一开始几乎不是同一套词）")

    # ③ 长度
    长 = [len(x["她"]) for x in 记录]
    半 = len(长) // 2 or 1
    前, 后 = 长[:半], 长[半:]
    print()
    print("    平均回话长度：前 %d 轮 %.1f 字｜后 %d 轮 %.1f 字"
          % (len(前), sum(前) / max(1, len(前)), len(后), sum(后) / max(1, len(后))))
    print("    最长 / 最短：%d / %d 字" % (max(长), min(长)))

    # ④ 套话率（§3.6 那条预言要验的就是这个）
    #   ★ 判据：**"说了很多句"和"说了很多种话"是两件事** —— 前者是产量，后者才是活着。
    from collections import Counter
    净 = [x["她"] for x in 记录 if x["她"] and x["她"] != "（没说话）"]
    次 = Counter(净)
    重句 = sum(c - 1 for c in 次.values() if c > 1)
    套话率 = 重句 / max(1, len(净))
    探针不同 = len({x["答"] for x in 探针 if x["答"]})
    print()
    print("═" * 74)
    print("  ④ 套话率（重复句数 / 总回话数）")
    print("═" * 74)
    print("    回话 %d 句｜不同说法 %d 种｜多说了 %d 次｜**套话率 %.0f%%**"
          % (len(净), len(次), 重句, 套话率 * 100))
    for 句, c in 次.most_common(3):
        print("    最常重复 %d 次：%s" % (c, 句[:26]))
    print("    探针 11 问的不同回答数：%d 种%s"
          % (探针不同, "（越多 = 越没定型）" if 探针不同 > 3 else "（说明已经定型）"))

    出 = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "轮": 轮, "每": 每, "窗": 窗,
         "套话率": round(套话率, 3), "探针不同": 探针不同,
         "探针": 探针, "记录": 记录}
    路 = os.path.join(结果目录, "漂移_w%d_%s.json" % (窗, time.strftime("%Y%m%d_%H%M")))
    io.open(路, "w", encoding="utf-8").write(json.dumps(出, ensure_ascii=False, indent=1))
    print()
    print("  原始数据：%s" % os.path.basename(路))
    return 出


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    w = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    raise SystemExit(0 if 跑(n, 窗=w) else 1)
