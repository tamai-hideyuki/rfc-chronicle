from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from typing import Any, Dict, List, Tuple

from rfc_chronicle.fetch_rfc import client
from rfc_chronicle.search import search_metadata, semsearch
from rfc_chronicle.show import show_rfc_details
from rfc_chronicle.fulltext import search_fulltext

from api.schemas import SemSearchItem, SemSearchResponse

def create_app() -> FastAPI:
    """
    RFC Chronicle API - FastAPI アプリケーションファクトリ
    """
    app = FastAPI(
        title="RFC Chronicle API",
        description="HTTP インターフェイスで RFC Chronicle CLI の各種操作を公開",
        version="0.1.0",
    )

    # CORS 設定（開発中は全許可。本番では必要に応じて制限する）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    async def safe_run(func, *args, not_found: bool = False, **kwargs) -> Any:
        """
        ブロッキング関数をスレッドプールで実行し、
        例外時には HTTPException を発生させるラッパー
        """
        try:
            return await run_in_threadpool(func, *args, **kwargs)
        except Exception as exc:
            status = 404 if not_found else 500
            raise HTTPException(status_code=status, detail=str(exc))

    @app.get("/api/metadata", response_model=List[Dict[str, Any]])
    async def get_metadata(save: bool = False) -> List[Dict[str, Any]]:
        """
        全 RFC メタデータ取得（save=True でローカルにキャッシュ保存）
        """
        return await safe_run(client.fetch_metadata, save)

    @app.get("/api/search", response_model=Dict[str, List[str]])
    async def api_search(q: str) -> Dict[str, List[str]]:
        """
        キャッシュ済みメタデータをキーワード q でフィルタリング
        """
        return {"results": await safe_run(search_metadata, q)}

    @app.get("/api/semsearch", response_model=SemSearchResponse)
    async def api_semsearch(q: str, topk: int = 10) -> SemSearchResponse:
        raw_results: List[Tuple[float, str | int]] = await safe_run(semsearch, q, topk)

        # ここで文字列化
        items = [
            SemSearchItem(num=str(rfc_num), score=score)
            for score, rfc_num in raw_results
        ]
        return SemSearchResponse(results=items)



    @app.get("/api/show/{rfc_num}", response_model=Dict[str, Any])
    async def api_show(rfc_num: int) -> Dict[str, Any]:
        """
        指定した RFC 番号のヘッダー＋本文を取得
        (not_found=True で見つからなければ 404)
        """
        return await safe_run(show_rfc_details, rfc_num, not_found=True)

    @app.get(
        "/api/fulltext",
        response_model=Dict[str, List[Dict[str, Any]]],
        summary="全文検索"
    )
    async def api_fulltext(q: str, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """
        SQLite FTS5 を用いた全文検索。
        スニペット付きでマッチした上位 limit 件を返却
        """
        # search_fulltext は List[Tuple[int, str]] を返す想定
        results: List[Tuple[int, str]] = await safe_run(search_fulltext, q, limit=limit)
        return {
            "results": [
                {"number": num, "snippet": snippet}
                for num, snippet in results
            ]
        }

    return app


# FastAPI アプリケーションを生成
app = create_app()
