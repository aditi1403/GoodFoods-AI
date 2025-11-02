from fastapi import FastAPI, Depends
from .db import get_db, engine
from . import models, crud
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uvicorn

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="GoodFoods API")

class SearchReq(BaseModel):
    city: str = None
    cuisine: str = None
    limit: int = 6

@app.post("/search")
def search(req: SearchReq, db: Session = Depends(get_db)):
    results = crud.list_restaurants(db, city=req.city, cuisine=req.cuisine, limit=req.limit)
    return [{"id": r.id, "name": r.name, "city": r.city, "cuisine": r.cuisine} for r in results]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
