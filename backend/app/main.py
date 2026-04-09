from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Any, Dict

app = FastAPI()

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
    return {
        "status": "active",
        "task": "easy"
    }
