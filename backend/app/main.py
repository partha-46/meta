from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import the existing inference runner so we can reuse run_episode
try:
    # inference.py lives at project root and exports run_episode
    import inference
except Exception:
    inference = None

app = FastAPI(title="LifeLine AI API", version="1.0.0")

# Configure logging for startup visibility
logger = logging.getLogger("lifeline.backend")
logging.basicConfig(level=logging.INFO)


class BenchmarkRequest(BaseModel):
    agent: str = "rules"  # 'rules' or 'llm'
    difficulty: str = "all"  # easy|medium|hard|all


@app.on_event("startup")
def startup_event() -> None:
    logger.info("LifeLine AI API started successfully")


@app.get("/")
async def home():
    return {
        "status": "live",
        "project": "LifeLine AI",
        "message": "Meta Hackathon deployment is running successfully",
        "endpoints": ["/health", "/run-benchmark"],
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "project": "LifeLine AI"}


@app.post("/run-benchmark")
def run_benchmark(req: BenchmarkRequest) -> Dict[str, Any]:
    """Run the existing inference benchmark and return structured JSON results.

    This re-uses the `run_episode` function from `inference.py` so the benchmark
    logic remains in one place and is usable both as CLI and via the HTTP API.
    """

    if inference is None:
        raise HTTPException(status_code=500, detail="inference module not available")

    agent = req.agent.lower()
    if agent not in ("rules", "llm"):
        raise HTTPException(status_code=400, detail="agent must be 'rules' or 'llm'")

    difficulty = req.difficulty.lower()
    if difficulty not in ("easy", "medium", "hard", "all"):
        raise HTTPException(status_code=400, detail="difficulty must be easy|medium|hard|all")

    # Prepare OpenAI client when requested
    client: Optional[Any] = None
    if agent == "llm":
        try:
            from openai import OpenAI as OpenAIClient  # type: ignore
        except Exception as exc:  # pragma: no cover - import/runtime error
            raise HTTPException(status_code=500, detail=f"OpenAI client not available: {exc}")

        api_key = os.getenv("OPENAI_API_KEY", "EMPTY")
        hf_token = os.getenv("HF_TOKEN", "")
        if hf_token and api_key == "EMPTY":
            api_key = hf_token

        try:
            client = OpenAIClient(api_key=api_key, base_url=os.getenv("API_BASE_URL", "https://api.openai.com/v1"))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to initialize OpenAI client: {exc}")

    # Determine difficulties list
    difficulties: List[str]
    if difficulty == "all":
        difficulties = inference.ALL_DIFFICULTIES
    else:
        difficulties = [difficulty]

    results = []
    for diff in difficulties:
        # Each run returns structured dicts as defined by inference.run_episode
        try:
            res = inference.run_episode(client, diff, agent)
        except Exception as exc:
            # Bubble up error details while keeping API stable
            raise HTTPException(status_code=500, detail=f"Benchmark run failed: {exc}")
        results.append(res)

    avg_score = sum(r["score"] for r in results) / len(results) if results else 0.0

    return {"average_score": avg_score, "results": results}
