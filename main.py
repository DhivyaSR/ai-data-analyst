# main.py
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import agent

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

class Query(BaseModel):
    message: str

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.post("/ask")
def ask(query: Query):
    answer, data = agent.run_agent(query.message)
    return {"answer": answer, "data": data}
