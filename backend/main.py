from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from backend.agents.orchestrator import AgenticCodeReviewOrchestrator
from backend.utils.github_client import GitHubPRClient

app = FastAPI(
    title="Agentic Code Reviewer API",
    description="Multi-Step Agentic AI Code Reviewer with Context Chunking, Retry Recovery & False-Alarm Suppression",
    version="1.0.0",
)

orchestrator = AgenticCodeReviewOrchestrator()

class DiffReviewRequest(BaseModel):
    diff_text: str = Field(..., description="Unified git diff or code snippet to review")
    max_chunk_chars: int = Field(default=3500, ge=500, le=20000)
    confidence_threshold: float = Field(default=0.78, ge=0.1, le=0.99)

class GitHubPRReviewRequest(BaseModel):
    repo_full_name: str = Field(..., example="pallets/flask")
    pr_number: int = Field(..., example=1)
    github_token: Optional[str] = Field(default="")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Agentic Code Reviewer"}

@app.post("/api/v1/review-diff")
def review_diff(payload: DiffReviewRequest):
    if not payload.diff_text.strip():
        raise HTTPException(status_code=400, detail="Diff text cannot be empty.")
    custom_orchestrator = AgenticCodeReviewOrchestrator(
        max_chars_per_chunk=payload.max_chunk_chars,
        confidence_threshold=payload.confidence_threshold,
    )
    return custom_orchestrator.run_review(payload.diff_text)

@app.post("/api/v1/review-github-pr")
def review_github_pr(payload: GitHubPRReviewRequest):
    try:
        client = GitHubPRClient(token=payload.github_token or "")
        pr_data = client.fetch_pr_diff(payload.repo_full_name, payload.pr_number)
        result = orchestrator.run_review(pr_data["diff_text"])
        result["github_metadata"] = {
            "repo": payload.repo_full_name,
            "pr_number": payload.pr_number,
        }
        return result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch or review GitHub PR: {exc}")
