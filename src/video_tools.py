from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path


class VideoToolError(RuntimeError):
    pass


def require_ffmpeg() -> None:
    for binary in ["ffmpeg", "ffprobe"]:
        if shutil.which(binary) is None:
            raise VideoToolError(f"{binary} is required but was not found on PATH.")


def probe_duration_seconds(path: Path) -> float:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise VideoToolError(completed.stderr.strip())
    data = json.loads(completed.stdout)
    return float(data["format"]["duration"])


def split_video(path: Path, output_dir: Path, segment_seconds: int) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    duration = probe_duration_seconds(path)
    total_segments = max(1, math.ceil(duration / segment_seconds))
    outputs: list[Path] = []

    for index in range(total_segments):
        start = index * segment_seconds
        output_path = output_dir / f"{path.stem}_clip_{index:03d}.mp4"
        command = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            str(start),
            "-i",
            str(path),
            "-t",
            str(segment_seconds),
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            raise VideoToolError(completed.stderr.strip())
        outputs.append(output_path)

    return outputs