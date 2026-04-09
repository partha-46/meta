from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Any, Dict
import logging

app = FastAPI(title="LifeLine AI API")

# Configure logging
logger = logging.getLogger("lifeline.backend")
logging.basicConfig(level=logging.INFO)

class Observation(BaseModel):
    symptoms: str
    severity: str
    step_count: int

class StepResponse(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: Dict[str, Any]

@app.post("/reset")
async def reset(payload: dict = Body(default={})):
    logger.info(f"OpenEnv: Received /reset request with payload: {payload}")
    return StepResponse(
        observation=Observation(
            symptoms="Patient reports fever and sore throat",
            severity="unknown",
            step_count=0
        ),
        reward=0.0,
        done=False,
        info={}
    )

@app.post("/step")
async def step(payload: dict = Body(default={})):
    logger.info(f"OpenEnv: Received /step request with payload: {payload}")
    return StepResponse(
        observation=Observation(
            symptoms="updated symptoms",
            severity="low",
            step_count=1
        ),
        reward=0.3,
        done=False,
        info={}
    )

@app.get("/state")
async def state():
    logger.info("OpenEnv: Received /state request")
    return {
        "status": "active",
        "task": "easy"
    }

@app.get("/health")
async def health():
    return {"status": "ok"}
