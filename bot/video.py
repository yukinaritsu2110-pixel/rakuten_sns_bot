from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def make_reel(slides: list[Path], out_path: Path, seconds_each: int = 2) -> bool:
    if not slides:
        return False
    if shutil.which("ffmpeg") is None:
        return False

    out_path.parent.mkdir(parents=True, exist_ok=True)
    list_file = out_path.parent / "_slides.txt"
    with list_file.open("w", encoding="utf-8") as f:
        for slide in slides:
            f.write(f"file '{slide.as_posix()}'\n")
            f.write(f"duration {seconds_each}\n")
        f.write(f"file '{slides[-1].as_posix()}'\n")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-vf",
        "fps=30,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-pix_fmt",
        "yuv420p",
        str(out_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except Exception:
        return False
    finally:
        if list_file.exists():
            list_file.unlink()
