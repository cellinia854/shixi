from __future__ import annotations

import math
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SegmentScore:
    path: Path
    index: int
    start_seconds: float
    end_seconds: float
    score: float
    label: str
    details: dict[str, float]


def score_segment(path: Path, index: int, start_seconds: float, end_seconds: float) -> SegmentScore:
    audio_score = _audio_energy_score(path)
    scene_score = _scene_change_score(path)
    duration = max(end_seconds - start_seconds, 0.1)
    position_bonus = _position_bonus(start_seconds)
    score = audio_score * 0.45 + scene_score * 0.45 + position_bonus * 0.10
    return SegmentScore(
        path=path,
        index=index,
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        score=score,
        label=f"clip_{index:03d}",
        details={
            "audio_score": audio_score,
            "scene_score": scene_score,
            "position_bonus": position_bonus,
            "duration": duration,
        },
    )


def _audio_energy_score(path: Path) -> float:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-i",
        str(path),
        "-af",
        "volumedetect",
        "-f",
        "null",
        "-",
    ]
    output = _run_capture(command)
    match = re.search(r"max_volume:\s*(-?\d+(?:\.\d+)?) dB", output)
    if not match:
        return 0.0
    max_volume = float(match.group(1))
    # Typical video peaks are between roughly -45 dB and 0 dB.
    return _clamp((max_volume + 45.0) / 45.0)


def _scene_change_score(path: Path) -> float:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-i",
        str(path),
        "-vf",
        "select='gt(scene,0.18)',metadata=print",
        "-an",
        "-f",
        "null",
        "-",
    ]
    output = _run_capture(command)
    changes = output.count("lavfi.scene_score")
    return _clamp(math.log1p(changes) / math.log1p(8))


def _position_bonus(start_seconds: float) -> float:
    if start_seconds < 8:
        return 0.25
    return 0.5


def _run_capture(command: list[str]) -> str:
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    return f"{completed.stdout}\n{completed.stderr}"


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
