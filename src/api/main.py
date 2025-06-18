from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from rfc_chronicle.fetch_rfc import fetch_metadata
from rfc_chronicle.search import search_metadata
from rfc_chronicle.pin import pin_rfc, list_pins

app = FastAPI()

# ブラウザ側起点なので必要に応じて CORS 許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/metadata")
def api_metadata():
    try:
        return fetch_metadata()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search")
def api_search(q: str):
    try:
        return search_metadata(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pin/{rfc_num}")
def api_pin(rfc_num: int):
    try:
        pin_rfc(rfc_num)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pins")
def api_list_pins():
    return list_pins()
