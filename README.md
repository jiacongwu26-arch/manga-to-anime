# manga-to-anime

漫画转动画的**约束层**。

视频模型会画，但它不会读漫画。它会搞错谁在说话、把拟声词当台词、把同一个角色的不同年龄当成两个人、把黑白页的浅发认成金发、为了演完偷偷删格——而且它不会报错。

这套 skill 把这些错误逐条写成**可执行的约束**：每条规则附失败案例、判定方法和验收方式。先读懂，再生成。

## 约束清单

| 编号 | 约束 | 一句话 |
|---|---|---|
| C1 | 阅读顺序 | 右→左、上→下；最后一排仍是右先左后 |
| C2 | 岛分组 | 视线相邻=同一时刻；跨岛才换场，不用叠化 |
| C3 | 分格类型 | 无框=情绪长镜；出血=定场；内嵌=插入特写 |
| C4 | 气泡归属 | 尾羽指向谁就是谁；分不清标 unknown |
| C5 | 气泡类型 | 拟声词/旁白/心声**不按对白配音** |
| C6 | 判定优先级 | 尾羽 → 框形 → 手写体 → 云朵 → 锯齿 |
| C7 | 身份 | 不同年龄不是同一个人；看服装不看发色 |
| C8 | 配角 | 路人不要升级成主角 |
| C9 | 发色 | 黑白页不可信；只用上色参考 |
| C10 | 台词时长 | 日语按 mora，不按字数 |
| C11 | 无台词基准 | 定场 3.5s / 动作 2.5s / 情绪 2.2s |
| C12 | 总账 | 装不下就删格，台词格不动，不许偷压 |
| C13 | 禁止填时间 | 不用静帧/慢放凑时长，加镜头 |
| C14 | 格≠镜头 | 一页 2–4 格 → 3–5 镜 |
| C15 | 反应镜 | 只在情绪转折处，一页 1–2 个 |
| C16 | 动作顺序 | 写死 AしてからB，仍要逐格验收 |

完整说明与失败案例见 [SKILL.md](SKILL.md)。

## 目录

```
SKILL.md                  约束主体：规则 + 失败案例 + 验收表
reference/
  reading_rules.md        阅读顺序、分格类型、常见误读
  bubble_taxonomy.md      六类气泡与判定优先级
  shot_grammar.md         格到镜头的拆法与镜头预算
  duration_budget.md      mora 计时、基准时长、总账校验
  example.md              两页完整走查，含每步判定理由
  api_integration.md      （可选）渲染接口形状与客户端纪律
  h3_rendering.md         （可选）模型能力边界与音频策略
scripts/
  plan_duration.py        按约束算时长并核对总账
  mora_count.py           日语 mora 与时长估算
  check_motion.py         帧间稳定性指标
  pitch_check.py          跨段声线 F0 对比
examples/
  page_plan.sample.json   机器可读页面解析（台词 + 假名读法）
```

## 快速开始

```bash
# 1. 写页面解析：分格、气泡类型、说话人、日语台词、假名读法
#    格式见 examples/page_plan.sample.json

# 2. 算时长并核对总账（缺秒会明确报出来，不会替你拉长镜头）
#    Windows 上若 python 指向应用商店空壳，把 python 换成 py
python scripts/plan_duration.py --target 28 --unit 30 --segment 15,13 \
  < examples/page_plan.sample.json > plan.json

# 3. 生成后验收
python scripts/check_motion.py --input clip.mp4
python scripts/pitch_check.py --input audio.wav --segments "0-3,3-8,8-13"
```

`plan_duration.py` 默认 `--reactions auto`：只给**两句以上**的对话格加反应镜，每页最多 2 个。
需要全加用 `--reactions all`，一个都不要用 `--reactions none`。

## 依赖

```
python >= 3.10
numpy, opencv-python, soundfile, scipy
ffmpeg / ffprobe
```

可选：`openai-whisper`（台词核对）、`pykakasi`（日语注音）。

## 适用范围

这套约束适用于任何"漫画 → 动画"的编排，与用哪个视频模型无关。约束先立住，模型换了也不用重写。

## License

MIT
