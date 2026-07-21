# Seedance Vlog Demo

一个临时 Streamlit demo，用于探索“只使用 Seedance 系列模型”的 vlog 高光生成与片段交互流程。

## 能力边界

Seedance 系列公开 API 主要是视频生成、图生视频、参考素材生成视频。它适合把输入片段生成 recap、风格化短片或转场，但公开接口并不是长视频问答模型。因此本 demo 采用：

- 本地工程处理：上传、切片、基础高光候选排序、裁剪片段。
- Seedance API：对候选片段或文本 prompt 发起视频生成任务。
- 片段交互：基于查询展示候选证据片段，并可把查询组织成 Seedance 生成 prompt。

如果后续允许使用 Seed/Doubao 视觉理解模型，可以把 `src/query.py` 替换成真正的视频问答检索模块。

## 项目结构

```text
.
├── app.py
├── requirements.txt
├── .env.example
├── src
│   ├── config.py
│   ├── highlight.py
│   ├── query.py
│   ├── seedance_client.py
│   ├── video_tools.py
│   └── workflow.py
└── data
    ├── uploads
    ├── segments
    └── outputs
```

`data/` 会在运行时自动创建。

## 快速开始

1. 安装 Python 依赖：

```bash
pip install -r requirements.txt
```

2. 确认本机有 `ffmpeg` 和 `ffprobe`：

```bash
ffmpeg -version
ffprobe -version
```

3. 配置环境变量：

```bash
cp .env.example .env
```

把 `.env` 里的 `SEEDANCE_API_KEY` 换成你的 key。

4. 启动 demo：

```bash
streamlit run app.py
```

## 推荐演示流程

1. 上传一个 1-5 分钟 vlog 或运动视频。
2. 点击“分析并切片”，系统会按不超过 15 秒切片并排序候选高光。
3. 预览 Top clips，选择一个片段作为演示高光。
4. 如果该片段有公网 URL，粘贴到“Seedance reference video URL”，点击生成 recap。
5. 在问答框输入“我的钥匙丢在哪儿了”或“我今天吃了什么”，demo 会展示候选证据片段，并生成一段适合提交给 Seedance 的 prompt。

## 为什么切成 15 秒

多个 Seedance 2.0 API 平台的 reference-to-video 输入/输出通常围绕 4-15 秒短片段设计。5 分钟视频应先被切片，再挑选候选片段进入 Seedance。
