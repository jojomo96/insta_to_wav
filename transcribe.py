"""
Utility helpers for:
1. Downloading an Instagram reel to a working directory
2. Extracting its audio track to WAV

Used by `main.py`.  Separated to keep endpoint code tidy.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Final

import instaloader
import moviepy.editor as mp

__all__ = ["convert_video_to_wav", "ReelError"]


class ReelError(RuntimeError):
    """Raised for any problem when handling the reel."""


def _download_reel(url: str, dest_dir: Path) -> Path:
    """
    Download a reel and return the local .mp4 path.
    `dest_dir` must already exist.
    """
    try:
        loader = instaloader.Instaloader(dirname_pattern=str(dest_dir), quiet=True)
        shortcode = url.rstrip("/").split("/")[-1]  # expects .../reel/<shortcode>/
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target="")
        mp4_files = list(dest_dir.glob("*.mp4"))
        if not mp4_files:
            raise ReelError("Reel downloaded but no MP4 file found")
        return mp4_files[0]
    except Exception as exc:
        raise ReelError(f"Failed to download reel: {exc}") from exc


def _convert_video_to_audio(video_file: Path, dest_wav: Path) -> Path:
    """
    Extract the audio track of `video_file` and write it to `dest_wav`.
    Returns the WAV path
    """
    clip = mp.VideoFileClip(str(video_file))
    clip.audio.write_audiofile(str(dest_wav))
    clip.close()
    return dest_wav


def convert_video_to_wav(url: str, work_dir: Path) -> Path:
    """
    High-level helper used by the FastAPI route:
    - downloads reel
    - extracts audio -> WAV
    - returns WAV path
    All intermediate artefacts land inside `work_dir`.
    """
    video_path = _download_reel(url, work_dir)
    wav_path = work_dir / "audio.wav"
    return _convert_video_to_audio(video_path, wav_path)


# ── CLI usage for quick local testing ──────────────────────────────────────────
if __name__ == "__main__":
    url_in = input("Enter Instagram Reel URL: ").strip()
    tmp_dir = Path("temp") / "cli-test"
    tmp_dir.mkdir(exist_ok=True, parents=True)
    try:
        wav = convert_video_to_wav(url_in, tmp_dir)
        print(f"WAV written to {wav}")
    finally:
        # Comment this out if you want to inspect files afterwards
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
