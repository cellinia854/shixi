from __future__ import annotations

from src.highlight import SegmentScore


QUERY_HINTS = {
    "钥匙": "重点观察桌面、口袋、包、门口、沙发、床边、运动装备附近是否出现钥匙。",
    "吃": "重点观察食物、餐具、饮料、餐桌、厨房、餐厅或手部拿取食物的画面。",
    "喝": "重点观察杯子、瓶子、饮料、咖啡、奶茶、水杯等物体。",
    "运动": "重点观察跑步、骑行、球类、健身、跳跃、出汗和高动作强度片段。",
    "高光": "重点观察动作强、情绪变化明显、镜头切换快或声音能量高的片段。",
}


def rank_candidates_for_query(query: str, segments: list[SegmentScore]) -> list[SegmentScore]:
    query = query.strip()
    if not query:
        return segments

    boost = _query_boost(query)
    ranked = sorted(
        segments,
        key=lambda item: item.score + boost * _segment_prior(item),
        reverse=True,
    )
    return ranked


def build_seedance_prompt(query: str, candidates: list[SegmentScore]) -> str:
    hint = _query_hint(query)
    clip_lines = "\n".join(
        f"- {item.label}: {item.start_seconds:.1f}s to {item.end_seconds:.1f}s"
        for item in candidates[:3]
    )
    return (
        "You are creating a short Seedance video response from a vlog reference clip.\n"
        f"User question: {query}\n"
        f"Visual focus: {hint}\n"
        "Use the selected reference clip as visual evidence. Create a concise recap that "
        "emphasizes the moment most relevant to the question. Keep it realistic and avoid "
        "inventing objects that are not visible in the reference.\n"
        "Candidate local clips:\n"
        f"{clip_lines}"
    )


def _query_hint(query: str) -> str:
    for keyword, hint in QUERY_HINTS.items():
        if keyword in query:
            return hint
    return "重点观察与用户问题相关的人、物体、动作和场景变化。"


def _query_boost(query: str) -> float:
    if any(keyword in query for keyword in QUERY_HINTS):
        return 0.15
    return 0.05


def _segment_prior(segment: SegmentScore) -> float:
    return segment.details.get("scene_score", 0.0) * 0.6 + segment.details.get("audio_score", 0.0) * 0.4
