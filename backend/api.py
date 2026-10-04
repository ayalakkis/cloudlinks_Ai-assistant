import os
import shutil

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from assistant import Assistant
from db import init_db
from ingest import ingest_file

init_db()
assistant = Assistant()

app = FastAPI(title="Cloudlinks Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

DOCUMENTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "documents")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[str]


class UploadResponse(BaseModel):
    file_name: str
    chunks_stored: int


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    tool_calls: list[str] = []
    reply = assistant.send(request.message, on_tool_call=tool_calls.append)
    return ChatResponse(reply=reply, tool_calls=tool_calls)


@app.post("/upload", response_model=UploadResponse)
def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only .pdf and .txt files are supported.")

    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    save_path = os.path.join(DOCUMENTS_DIR, file.filename)
    with open(save_path, "wb") as saved_file:
        shutil.copyfileobj(file.file, saved_file)

    chunks_stored = ingest_file(save_path)
    return UploadResponse(file_name=file.filename, chunks_stored=chunks_stored)
