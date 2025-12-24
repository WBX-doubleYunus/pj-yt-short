import os
import shutil
import pathlib

import pytest

from app import process

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
TMP_DIR = os.path.join(OUTPUT_DIR, "tmp")


@pytest.fixture(autouse=True)
def clean_tmp():
    # ensure clean tmp folder for each test
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)
    os.makedirs(TMP_DIR, exist_ok=True)
    yield
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)


def touch_dummy_input():
    p = os.path.join(TMP_DIR, "input.mp4")
    with open(p, "wb") as f:
        f.write(b"dummy")
    return p


def test_handle_new_video_with_mocks(monkeypatch):
    # Prepare dummy input file
    in_file = touch_dummy_input()

    # Patch subprocess.run to no-op
    monkeypatch.setattr("subprocess.run", lambda *a, **k: None)

    # Patch transcribe to return sample text
    monkeypatch.setattr("app.transcribe.transcribe_from_video", lambda vp, language="id": "Ini adalah momen lucu dan menarik.")

    # Patch moderation to flag first segment
    monkeypatch.setattr("app.moderation.moderate_segments", lambda segments: [0])

    # Patch censor functions to just return provided paths
    monkeypatch.setattr("app.censor.bleep_audio_for_segments", lambda vp, s, f, out: out)
    monkeypatch.setattr("app.censor.replace_audio_in_video", lambda v, a, out: out)
    monkeypatch.setattr("app.censor.blur_video_segments", lambda v, segs, out: out)

    # Patch subtitles and soundboard/visual overlay to be no-op
    monkeypatch.setattr("app.subtitles.burn_subtitles_into_video", lambda vin, srt, out: out)
    monkeypatch.setattr("app.soundboard.overlay_soundboard", lambda vin, ev, out: out)
    monkeypatch.setattr("app.visual_overlay.overlay_images_on_video", lambda vin, ev, out: out)

    # Patch highlight extraction to return a funny highlight
    monkeypatch.setattr("app.highlight.extract_highlights", lambda txt: [{"start": 0.5, "end": 2.5, "label": "funny", "caption": "Momen lucu!"}])

    # Patch telegram sender to avoid network
    monkeypatch.setattr("app.telegram.send_short_notification", lambda *a, **k: None)

    # Run the pipeline (should use the dummy input)
    res = process.handle_new_video("https://example.com/watch?v=test", max_duration=5)

    # Assert processed marker file exists
    assert os.path.exists(os.path.join(TMP_DIR, "processed.txt"))
    # Result should contain short path
    assert "short" in res and res["short"]
    # Subtitles file should exist
    assert os.path.exists(os.path.join(TMP_DIR, "subtitles.srt"))
    # Transcript file should be present
    assert res.get("transcript_file") is not None
