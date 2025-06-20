from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
import logging
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel
from rfc_chronicle.pin import pin_rfc, unpin_rfc, list_pins
from rfc_chronicle.fetch_rfc import client
from rfc_chronicle.search import search_metadata, semsearch
from rfc_chronicle.show import show_rfc_details
from rfc_chronicle.fulltext import search_fulltext

from api.schemas import SemSearchItem, SemSearchResponse

logger = logging.getLogger("uvicorn.error")

async def safe_run(func, *args, not_found: bool = False, **kwargs) -> Any:
    try:
        return await run_in_threadpool(func, *args, **kwargs)
    except Exception as exc:
        logger.error(f"Error running {func.__name__}: {exc}", exc_info=True)
        status = 404 if not_found else 500
        raise HTTPException(status_code=status, detail=str(exc))

class PinRequest(BaseModel):
    number: str

def create_app() -> FastAPI:
    app = FastAPI(
        title="RFC Chronicle API",
        description="HTTP インターフェイスで RFC Chronicle CLI の各種操作を公開",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── 既存ルート ─────────────────────────────────
    @app.get("/api/metadata", response_model=List[Dict[str, Any]])
    async def get_metadata(save: bool = False):
        return await safe_run(client.fetch_metadata, save)

    @app.get("/api/search", response_model=Dict[str, List[str]])
    async def api_search(q: str):
        return {"results": await safe_run(search_metadata, q)}

    @app.get("/api/semsearch", response_model=SemSearchResponse)
    async def api_semsearch(q: str, topk: int = 10):
        raw: List[Tuple[float, int]] = await safe_run(semsearch, q, topk)
        items = [ SemSearchItem(num=str(n), score=s) for s, n in raw ]
        return SemSearchResponse(results=items)

    @app.get("/api/show/{rfc_num}", response_model=Dict[str, Any])
    async def api_show(rfc_num: int):
        return await safe_run(show_rfc_details, rfc_num, not_found=True)

    @app.get("/api/fulltext", response_model=Dict[str, List[Dict[str, Any]]])
    async def api_fulltext(q: str, limit: int = 10):
        raw: List[Tuple[int, str]] = await safe_run(search_fulltext, q, limit=limit)
        return {"results": [{"number": n, "snippet": s} for n, s in raw]}

    # ─── ここからピン機能 ──────────────────────────────
    @app.get("/api/pins", response_model=List[str], summary="Get pinned RFC numbers")
    async def api_get_pins():
        return await safe_run(list_pins)

    @app.post("/api/pins", status_code=201, summary="Pin an RFC")
    async def api_pin(request: PinRequest):
        await safe_run(pin_rfc, request.number)
        return {"number": request.number}

    @app.delete("/api/pins/{number}", status_code=204, summary="Unpin an RFC")
    async def api_unpin(number: str):
        await safe_run(unpin_rfc, number)
        # 204 No Content

    return app

app = create_app()
