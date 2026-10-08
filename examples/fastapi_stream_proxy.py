"""
FastAPI High-Speed Media Streaming Microservice
Streams high-definition video chunks directly to clients or web players
with zero temporary disk usage.
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from stdapi import media, tools, search

app = FastAPI(
    title="StdAPI Streaming Microservice",
    description="High-throughput proxy streaming media to web clients without buffering on disk."
)


@app.get("/stream")
async def stream_video(url: str = Query(..., description="Target media URL")):
    """Streams video chunks directly through FastAPI."""
    try:
        async def chunk_generator():
            async for chunk in media.stream(url, chunk_size=65536):
                yield chunk

        return StreamingResponse(
            chunk_generator(),
            media_type="video/mp4",
            headers={"Content-Disposition": 'inline; filename="video.mp4"'}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/search/youtube")
async def youtube_search(q: str = Query(..., description="Search query")):
    """Zero-key YouTube discovery for web frontends."""
    return await search.youtube(q, limit=10)


@app.get("/tools/qr")
async def qr_code(text: str = Query(..., description="Text or link")):
    """Generates QR code PNG bytes directly."""
    buf = await tools.qr_buffer(text)
    return StreamingResponse(buf, media_type="image/png")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
