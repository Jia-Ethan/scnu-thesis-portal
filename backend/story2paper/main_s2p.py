"""
Story2Paper — FastAPI Backend Entry Point
"""

import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.story2paper.story2paper.pipeline.orchestrator import get_pipeline, PipelineState
from backend.story2paper.story2paper.api.evaluate.route import router as evaluate_router
from backend.story2paper.story2paper import paper_store

# CORS origins — comma-separated env var for multi-origin production
_cors_raw = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
CORS_ORIGINS = [origin.strip() for origin in _cors_raw.split(",") if origin.strip()]


# ─── Lifespan ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: warm up pipeline (import all agents)
    get_pipeline()
    print("[Story2Paper] Pipeline ready")
    yield
    print("[Story2Paper] Shutdown")


# ─── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Story2Paper API",
    description="Multi-Agent Academic Paper Generation",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # configured via CORS_ORIGINS env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request/Response Models ──────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    research_prompt: str
    title_hint: str | None = None


class GenerateResponse(BaseModel):
    paper_id: str
    status: str = "queued"


class PaperStatus(BaseModel):
    paper_id: str
    status: str
    current_agent: str | None = None
    progress: str | None = None


class GenerateResultResponse(BaseModel):
    paper_id: str
    outline: dict | None = None
    section_drafts: list[dict] = Field(default_factory=list)
    contract: dict | None = None
    final_output: str | None = None
    status: str


# ─── WebSocket Manager ────────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, paper_id: str, ws: WebSocket):
        await ws.accept()
        self.active[paper_id] = ws

    def disconnect(self, paper_id: str):
        self.active.pop(paper_id, None)

    async def send(self, paper_id: str, data: dict):
        ws = self.active.get(paper_id)
        if ws:
            await ws.send_json(data)


manager = ConnectionManager()


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"message": "Story2Paper API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    paper_id = str(uuid.uuid4())[:8]

    # Kick off async pipeline (fire and forget — WebSocket streams results)
    asyncio.create_task(_run_pipeline(paper_id, req.research_prompt))

    return GenerateResponse(paper_id=paper_id, status="running")


@app.get("/papers/{paper_id}", response_model=PaperStatus)
async def get_status(paper_id: str):
    state = paper_store.load(paper_id)
    if not state:
        raise HTTPException(404, "Paper not found")
    return PaperStatus(
        paper_id=paper_id,
        status="running" if state.get("final_output") is None else "done",
        current_agent=state.get("current_agent"),
        progress=f"section {state.get('current_section_index', 0)}/{len(state.get('outline', {}).get('sections', [1]))}",
    )


@app.get("/generate/result/{paper_id}", response_model=GenerateResultResponse)
async def get_result(paper_id: str):
    """Return full pipeline result for consumption by scnu-thesis-portal."""
    state = paper_store.load(paper_id)
    if not state:
        raise HTTPException(404, "Paper not found")
    return GenerateResultResponse(
        paper_id=paper_id,
        outline=state.get("outline"),
        section_drafts=state.get("section_drafts", []),
        contract=state.get("contract"),
        final_output=state.get("final_output"),
        status="done" if state.get("final_output") else "running",
    )


app.include_router(evaluate_router)


@app.websocket("/ws/{paper_id}")
async def websocket(ws: WebSocket, paper_id: str):
    await manager.connect(paper_id, ws)
    try:
        while True:
            # Keep connection alive; events pushed from pipeline
            data = await ws.receive_text()
            # Client can send ping; we just echo or ignore
            if data == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(paper_id)


# ─── Internals ────────────────────────────────────────────────────────────────


async def _run_pipeline(paper_id: str, research_prompt: str):
    """Execute pipeline and stream events via WebSocket"""
    pipeline = get_pipeline()

    initial_state: PipelineState = {
        "paper_id": paper_id,
        "research_prompt": research_prompt,
        "outline": None,
        "contract": None,
        "section_drafts": [],
        "current_section_index": 0,
        "audit_results": [],
        "pass_audit": False,
        "revision_round": 0,
        "writing_complete": False,
        "refinement_complete": False,
        "current_agent": "architect",
        "final_output": None,
    }

    paper_store.save(paper_id, initial_state)

    async for event in pipeline.astream(initial_state):
        # event: {"node_name": {"state_key": value, ...}}
        node_name = list(event.keys())[0]
        state = event[node_name]

        # Persist latest state
        paper_store.save(paper_id, state)

        # Stream to WebSocket
        await manager.send(paper_id, {
            "event": node_name,
            "current_agent": state.get("current_agent"),
            "section_index": state.get("current_section_index"),
            "audit_pass": state.get("pass_audit"),
            "revision_round": state.get("revision_round"),
        })

    # Final output assembled
    state["final_output"] = _assemble_final(state)
    paper_store.save(paper_id, state)
    await manager.send(paper_id, {"event": "done", "final_output": True})


def _assemble_final(state: dict) -> str:
    """Merge section drafts into a single markdown paper"""
    sections = state.get("section_drafts", [])
    outline = state.get("outline", {})
    title = outline.get("title", "Untitled Paper")

    lines = [f"# {title}\n"]
    for draft in sections:
        lines.append(f"\n## {draft['title']}\n")
        lines.append(draft["content"])
    return "".join(lines)
