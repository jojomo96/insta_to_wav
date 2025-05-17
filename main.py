import os
import uuid
import shutil
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Body
from fastapi.responses import FileResponse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import transcribe

# Make sure a reusable temp directory exists
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Reel → WAV micro-service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # or a list of specific origins
    allow_methods=["*"], # GET, POST, etc.
    allow_headers=["*"], # e.g. Content-Type
    expose_headers=["*"],
)


def cleanup_dir(path: Path) -> None:
    """Delete the directory created for this job."""
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


@app.post("/convert/", response_class=FileResponse)
async def convert_reel(
    background_tasks: BackgroundTasks,
    url: str = Body(..., embed=True, examples={"url": {"value": "https://www.instagram.com/reel/CR-……/"}}),
):
    """
    Download an Instagram reel and return its audio as WAV.
    The `url` **must** point to a public reel.
    """
    job_dir = TEMP_DIR / uuid.uuid4().hex
    job_dir.mkdir(exist_ok=True)

    try:
        audio_path = transcribe.convert_video_to_wav(url, job_dir)
    except transcribe.ReelError as exc:
        # Map library / custom exceptions to HTTP 400
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Clean up the whole job directory once the response is sent
    background_tasks.add_task(cleanup_dir, job_dir)

    return FileResponse(
        audio_path,
        media_type="audio/wav",
        filename="audio.wav",
    )
