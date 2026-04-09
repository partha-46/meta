"""Backend package for LifeLine AI HTTP API.

This package provides a small FastAPI wrapper that exposes the existing
benchmarking/inference logic via HTTP so the container remains running on
Hugging Face Spaces (sdk: docker).
"""

__all__ = ["app"]
