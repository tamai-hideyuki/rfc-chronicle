from fastapi import FastAPI, HTTPException
from rfc_chronicle.fetch_rfc import client
from rfc_chronicle.search import search_metadata, semsearch

app = FastAPI()


@app.get("/api/metadata")
async def get_metadata():
    """
    全 RFC メタデータを取得
    """
    try:
        # save=False にしてキャッシュのみ取得
        return client.fetch_metadata(save=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search")
async def api_search(q: str):
    """
    キーワードベースのメタデータ検索
    """
    try:
        return {"results": search_metadata(q)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/semsearch")
async def api_semsearch(q: str, topk: int = 10):
    """
    FAISS を使ったセマンティック検索
    """
    try:
        return {"results": semsearch(q, topk)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
