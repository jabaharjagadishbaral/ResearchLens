"""FastAPI wiring. UNTESTED: fastapi/pydantic/uvicorn are not installable in my sandbox.
All behaviour lives in app/services (tested); this file only maps HTTP <-> service calls."""
from __future__ import annotations

import os

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.core.config import Settings
from app.core.security import ServiceError
from app.db.repo import SQLiteRepository
from app.providers.remote import build_providers
from app.research.sources import ArxivSource
from app.services.auth import AuthService
from app.services.research_service import ResearchService
from app.verification.verifier import LexicalVerifier

settings = Settings.from_env()
emb, rer, llm = build_providers(settings)
store = None
if os.environ.get("QDRANT_URL"):   # production vector store; otherwise in-memory (rebuilt from the DB at startup)
    from app.retrieval.qdrant_store import QdrantVectorStore
    store = QdrantVectorStore(os.environ["QDRANT_URL"], os.environ.get("QDRANT_API_KEY"), emb.dim)
repo = SQLiteRepository(os.environ.get("DB_PATH", "researchmind.db"))
service = ResearchService(settings, emb, rer, llm, LexicalVerifier(), store=store, repo=repo)  # swap in an LLM/NLI verifier for production
auth = AuthService(os.environ["AUTH_SECRET"], repo)   # required; >=16 chars
service.sources = [ArxivSource()]
app = FastAPI(title="ResearchMind AI", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
                   allow_methods=["*"], allow_headers=["Authorization", "Content-Type"])
EVAL_PATH = os.environ.get("EVAL_RESULTS", "../evaluation/results/latest.json")

_STATUS = {"unauthorized": 401, "not_found": 404, "rate_limited": 429, "invalid_input": 422,
           "invalid_upload": 400, "ocr_required": 422, "unavailable": 503, "llm_unavailable": 502, "source_unavailable": 502}


@app.exception_handler(ServiceError)
async def service_error(_, exc: ServiceError):
    return JSONResponse({"error": {"code": exc.code, "message": exc.message}}, _STATUS.get(exc.code, 400))


def user(authorization: str = Header(default="")) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token.")
    return auth.authenticate(authorization[7:])


class Creds(BaseModel):
    email: str
    password: str


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class CompareReq(BaseModel):
    document_ids: list[str]


class ClaimsReq(BaseModel):
    claims: list[str]


class ReviewReq(BaseModel):
    title: str = "Literature Review"
    question: str


@app.get("/health")
def health():
    return {"status": "ok", "mock_mode": settings.mock_mode}


@app.post("/api/auth/register")
def register(c: Creds):
    return {"user_id": auth.register(c.email, c.password)}


@app.post("/api/auth/login")
def login(c: Creds):
    return {"access_token": auth.login(c.email, c.password), "token_type": "bearer"}


@app.post("/api/documents/upload")
async def upload(file: UploadFile = File(...), u: str = Depends(user)):
    data = await file.read(settings.max_upload_bytes + 1)
    return service.upload(u, file.filename or "", data)


@app.get("/api/documents")
def documents(u: str = Depends(user)):
    return service.list_documents(u)


@app.get("/api/documents/{doc_id}")
def document(doc_id: str, u: str = Depends(user)):
    return service.get_document(u, doc_id)


@app.get("/api/documents/{doc_id}/tables")
def tables(doc_id: str, u: str = Depends(user)):
    return service.tables(u, doc_id)


@app.post("/api/research/query")
def research_query(q: Question, u: str = Depends(user)):
    return service.query(u, q.question)


@app.post("/api/chat")
def chat(q: Question, u: str = Depends(user)):
    return service.query(u, q.question)


@app.post("/api/chat/stream")
def chat_stream(q: Question, u: str = Depends(user)):
    return StreamingResponse(service.chat_stream(u, q.question), media_type="text/event-stream")


@app.post("/api/papers/compare")
def compare(r: CompareReq, u: str = Depends(user)):
    return service.compare(u, r.document_ids)


@app.post("/api/claims/verify")
def verify(r: ClaimsReq, u: str = Depends(user)):
    return service.verify_claims(u, r.claims)


@app.get("/api/evidence/{chunk_id}")
def evidence(chunk_id: str, u: str = Depends(user)):
    return service.evidence(u, chunk_id)


@app.get("/api/knowledge-graph")
def graph(u: str = Depends(user)):
    return service.graph(u)


@app.post("/api/reports/literature-review")
def review(r: ReviewReq, u: str = Depends(user)):
    return service.literature_review(u, r.title, r.question)


@app.get("/api/dashboard")
def dashboard(u: str = Depends(user)):
    return service.dashboard(u)


class AnalyzeReq(BaseModel):
    document_id: str


class SearchReq(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int = 10


@app.post("/api/research/analyze")
def analyze(r: AnalyzeReq, u: str = Depends(user)):
    return service.analyze_document(u, r.document_id)


@app.post("/api/research/search")
def search(r: SearchReq, u: str = Depends(user)):
    return service.search_external(u, r.query, r.limit)


@app.get("/api/evaluation")
def evaluation(u: str = Depends(user)):
    return service.evaluation_report(EVAL_PATH)
