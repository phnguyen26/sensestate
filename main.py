from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from qdrant_client import QdrantClient
from openai import OpenAI
from routers import api
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sensestate.vercel.app", "http://localhost:8000"],   ##
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router)  


app.mount("/", StaticFiles(directory="frontend", html=True), name="ui")






