from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import sys
import os
import logging
from typing import Any, Dict, List, Optional

# Ensure project root is in path for environment and models
sys.path.append(os.getcwd())

from environment import MediRouteEnv
from models import Action

app = FastAPI(title="LifeLine AI API", version="1.0.0")

# Global environment instance
env = MediRouteEnv()

# Configure logging
logger = logging.getLogger("lifeline.backend")
logging.basicConfig(level=logging.INFO)

# ── Validator-specific Models ──────────────────────────────────────────────

class ObservationSchema(BaseModel):
    symptoms: str
    severity: str
    step_count: int

class StepResponse(BaseModel):
    observation: ObservationSchema
    reward: float
    done: bool
    info: Dict[str, Any]

# Import the existing inference runner so we can reuse run_episode
try:
    import inference
except Exception:
    inference = None

app = FastAPI(title="LifeLine AI API", version="1.0.0")

# Global environment instance for the OpenEnv validator
env = MediRouteEnv()

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


# ── OpenEnv Endpoints ──────────────────────────────────────────────────────

@app.post("/reset")
async def reset(payload: Dict[str, Any] = Body(default={})):
    """Reset the environment to a fresh state for validation."""
    logger.info(f"OpenEnv: Received /reset request with payload: {payload}")
    # Reset internal env
    obs = env.reset(difficulty="easy")
    
    # Map internal observation to validator's expected schema
    return StepResponse(
        observation=ObservationSchema(
            symptoms=obs.symptoms,
            severity="unknown", # Phase 1 initial state requirement
            step_count=0
        ),
        reward=0.0,
        done=False,
        info={}
    )


@app.get("/state")
async def state():
    """Return the current snapshot status."""
    return {
        "status": "active",
        "task": "easy"
    }


@app.post("/step")
async def step(payload: Dict[str, Any] = Body(default={})):
    """Advance the environment using the validator's action dictionary."""
    logger.info(f"OpenEnv: Received /step request with payload: {payload}")
    
    try:
        # Construct internal Action model from dict
        internal_action = Action(
            action_type=payload.get("action_type", "analyze_symptoms"),
            target=payload.get("target")
        )
        result = env.step(internal_action)
        
        # Map back to validator's schema
        severity_label = "low"
        if result.observation.severity_score >= 0.7: severity_label = "high"
        elif result.observation.severity_score >= 0.4: severity_label = "moderate"

        return StepResponse(
            observation=ObservationSchema(
                symptoms=result.observation.symptoms,
                severity=severity_label,
                step_count=result.info.get("step", 1)
            ),
            reward=result.reward,
            done=result.done,
            info=result.info
        )
    except Exception as e:
        logger.error(f"OpenEnv step failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
