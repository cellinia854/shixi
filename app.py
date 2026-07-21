from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.config import Settings
from src.query import build_seedance_prompt, rank_candidates_for_query
from src.seedance_client import SeedanceClient, SeedanceError
from src.workflow import DemoPaths, analyze_video, save_uploaded_file


st.set_page_config(page_title="Seedance Vlog Demo", layout="wide")

st.title("Seedance Vlog Demo")
st.caption("上传 vlog，提取候选高光片段，并把片段交给 Seedance 系列 API 做生成式 demo。")

settings = Settings.from_env()
paths = DemoPaths()
paths.ensure()

with st.sidebar:
    st.header("Seedance API")
    api_key = st.text_input("API key", value=settings.api_key, type="password")
    api_base = st.text_input("API base", value=settings.api_base)
    model = st.text_input("Model", value=settings.model)
    st.divider()
    segment_seconds = st.slider("切片秒数", min_value=4, max_value=15, value=12)
    top_k = st.slider("候选片段数", min_value=1, max_value=8, value=3)
    st.caption("Seedance reference-to-video 通常适合短片段，因此默认按 12 秒切。")

settings.api_key = api_key
settings.api_base = api_base.rstrip("/")
settings.model = model

uploaded = st.file_uploader("上传一段 1-5 分钟左右的视频", type=["mp4", "mov", "m4v", "webm"])

if uploaded:
    video_path = save_uploaded_file(uploaded, paths.uploads)
    st.success(f"已保存上传视频：{video_path.name}")
    st.video(str(video_path))

    if st.button("分析并切片", type="primary"):
        with st.spinner("正在用 ffmpeg 切片并计算候选高光分数..."):
            result = analyze_video(video_path, paths, segment_seconds=segment_seconds, top_k=top_k)
        st.session_state["analysis"] = result

analysis = st.session_state.get("analysis")

if analysis:
    st.subheader("候选高光片段")
    st.write(f"视频时长约 `{analysis.duration_seconds:.1f}s`，共生成 `{len(analysis.segments)}` 个片段。")

    cols = st.columns(min(len(analysis.top_segments), 3) or 1)
    for idx, segment in enumerate(analysis.top_segments):
        with cols[idx % len(cols)]:
            st.markdown(f"**Top {idx + 1}: {segment.label}**")
            st.caption(
                f"{segment.start_seconds:.1f}s - {segment.end_seconds:.1f}s | "
                f"score={segment.score:.2f}"
            )
            st.video(str(segment.path))

    st.subheader("与视频交互")
    query = st.text_input("试着提问", placeholder="例如：我的钥匙丢在哪儿了 / 我今天吃了什么")
    if query:
        candidates = rank_candidates_for_query(query, analysis.top_segments)
        prompt = build_seedance_prompt(query, candidates)
        st.markdown("**候选证据片段**")
        for candidate in candidates[:3]:
            st.caption(
                f"{candidate.label}: {candidate.start_seconds:.1f}s - "
                f"{candidate.end_seconds:.1f}s"
            )
            st.video(str(candidate.path))

        st.markdown("**Seedance prompt 草稿**")
        st.code(prompt, language="text")
        st.info(
            "当前是 Seedance-only 约束：这里展示候选片段和生成 prompt，"
            "不伪造视频理解模型的文本答案。"
        )

    st.subheader("Seedance 生成")
    selected = st.selectbox(
        "选择一个候选片段",
        options=analysis.top_segments,
        format_func=lambda item: f"{item.label} ({item.start_seconds:.1f}s-{item.end_seconds:.1f}s)",
    )
    reference_url = st.text_input(
        "Seedance reference video URL",
        placeholder="需要是 Seedance API 可访问的公网视频 URL",
    )
    generation_prompt = st.text_area(
        "生成 prompt",
        value=(
            "Create a concise cinematic highlight recap based on the reference vlog clip. "
            "Keep the original event structure, improve pacing, add energetic camera motion, "
            "and preserve a realistic daily-vlog style."
        ),
        height=110,
    )

    col_a, col_b = st.columns([1, 2])
    with col_a:
        submit = st.button("提交 Seedance 任务", disabled=not settings.api_key)
    with col_b:
        if not settings.api_key:
            st.warning("请先在侧边栏填写 API key。")

    if submit:
        client = SeedanceClient(settings)
        payload = {
            "prompt": generation_prompt,
            "generation_type": "reference-to-video" if reference_url else "text-to-video",
            "duration": min(8, int(selected.end_seconds - selected.start_seconds)),
            "resolution": "720p",
        }
        if reference_url:
            payload["video_urls"] = [reference_url]

        try:
            task = client.create_video_task(payload)
            st.session_state["seedance_task_id"] = task.task_id
            st.success(f"已提交任务：{task.task_id}")
        except SeedanceError as exc:
            st.error(str(exc))

task_id = st.session_state.get("seedance_task_id")
if task_id:
    st.subheader("Seedance 任务状态")
    st.code(task_id)
    if st.button("刷新任务状态"):
        client = SeedanceClient(settings)
        try:
            status = client.get_task(task_id)
            st.json(status.raw)
            if status.result_urls:
                st.success("任务已完成")
                for url in status.result_urls:
                    st.video(url)
        except SeedanceError as exc:
            st.error(str(exc))
