import pytest
from stdapi.extractors.base import MediaResponse, StreamInfo
from stdapi.extractors.registry import find_extractor
from stdapi import StdEngine


def test_media_response_best_streams():
    streams = [
        StreamInfo(url="https://stream.mp4/low", format="mp4", quality="480p", has_audio=True, has_video=True),
        StreamInfo(url="https://stream.mp4/high", format="mp4", quality="1080p", has_audio=True, has_video=True),
        StreamInfo(url="https://stream.mp3/audio", format="mp3", quality="320k", has_audio=True, has_video=False),
    ]
    resp = MediaResponse(
        extractor="YouTube",
        id="abc12345",
        title="Test Song",
        url="https://youtube.com/watch?v=abc12345",
        duration=180,
        streams=streams
    )

    assert resp.best_video_url == "https://stream.mp4/high"
    assert resp.best_audio_url == "https://stream.mp3/audio"
    d = resp.to_dict()
    assert d["title"] == "Test Song"
    assert len(d["streams"]) == 3


def test_find_extractor():
    yt_ext = find_extractor("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert yt_ext is not None
    assert yt_ext.NAME == "YouTube"

    ig_ext = find_extractor("https://www.instagram.com/reel/Cxxxxxx/")
    assert ig_ext is not None
    assert ig_ext.NAME == "Instagram"

    tt_ext = find_extractor("https://www.tiktok.com/@user/video/123456789")
    assert tt_ext is not None
    assert tt_ext.NAME == "TikTok"

    uni_ext = find_extractor("https://vimeo.com/12345678")
    assert uni_ext is not None
    assert uni_ext.NAME == "Universal"
