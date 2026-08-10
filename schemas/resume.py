from __future__ import annotations

from pydantic import BaseModel, Field

from models import JobDescription, MatchResult


class ResumeAnalysisSummary(BaseModel):
    total_files: int = Field(..., ge=0)
    processed_files: int = Field(..., ge=0)
    failed_files: int = Field(..., ge=0)


class ResumeAnalysisResponse(BaseModel):
    job_description_text: str = Field(..., description="Original job description text submitted by the frontend")
    job_description: JobDescription = Field(..., description="Structured job description extracted from the text")
    summary: ResumeAnalysisSummary = Field(..., description="Batch-level counts")
    results: list[MatchResult] = Field(default_factory=list, description="Match results for processed candidates")
    top_candidate: MatchResult | None = Field(
        default=None,
        description="Highest scoring candidate in the batch",
    )
    bottom_candidate: MatchResult | None = Field(
        default=None,
        description="Lowest scoring candidate in the batch",
    )
