from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from src.highlight import SegmentScore, score_segment
from src.video_tools import probe_duration_seconds, require_ffmpeg, split_video


@dataclass
class DemoPaths:
    root: Path = Path("data")

    @property
    def uploads(self) -> Path:
        return self.root / "uploads"

    @property
    def segments(self) -> Path:
        return self.root / "segments"

    @property
    def outputs(self) -> Path:
        return self.root / "outputs"

    def ensure(self) -> None:
        self.uploads.mkdir(parents=True, exist_ok=True)
        self.segments.mkdir(parents=True, exist_ok=True)
        self.outputs.mkdir(parents=True, exist_ok=True)


@dataclass
class AnalysisResult:
    video_path: Path
    duration_seconds: float
    segments: list[SegmentScore]
    top_segments: list[SegmentScore]


def save_uploaded_file(uploaded_file: BinaryIO, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    original_name = getattr(uploaded_file, "name", "upload.mp4")
    safe_name = _safe_filename(original_name)
    path = output_dir / safe_name
    with path.open("wb") as handle:
        handle.write(uploaded_file.getbuffer())
    return path


def analyze_video(
    video_path: Path,
    paths: DemoPaths,
    segment_seconds: int,
    top_k: int,
) -> AnalysisResult:
    require_ffmpeg()
    duration = probe_duration_seconds(video_path)
    segment_dir = paths.segments / video_path.stem
    clip_paths = split_video(video_path, segment_dir, segment_seconds)

    scores: list[SegmentScore] = []
    for index, clip_path in enumerate(clip_paths):
        start = index * segment_seconds
        end = min((index + 1) * segment_seconds, duration)
        scores.append(score_segment(clip_path, index, start, end))

    top_segments = sorted(scores, key=lambda item: item.score, reverse=True)[:top_k]
    return AnalysisResult(
        video_path=video_path,
        duration_seconds=duration,
        segments=scores,
        top_segments=top_segments,
    )


def _safe_filename(name: str) -> str:
    stem = Path(name).stem
    suffix = Path(name).suffix or ".mp4"
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", stem).strip("._") or "upload"
    return f"{stem}{suffix.lower()}"
