from pydantic import BaseModel
from typing import List

class SemSearchItem(BaseModel):
    score: float
    num: str

class SemSearchResponse(BaseModel):
    results: List[SemSearchItem]
