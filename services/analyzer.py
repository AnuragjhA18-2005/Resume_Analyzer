from __future__ import annotations

import asyncio

from fastapi import HTTPException, UploadFile

from extractors import read_resume
from parser import final_score, get_job_details, parse_resume
from models import MatchResult
from schemas.resume import ResumeAnalysisResponse, ResumeAnalysisSummary

from core.config import ALLOWED_UPLOAD_TYPES


async def _process_single_resume(file: UploadFile, job_description) -> MatchResult | None:
    filename = file.filename or "uploaded_resume"
    content_type = (file.content_type or "").lower()

    if content_type not in ALLOWED_UPLOAD_TYPES:
        return None

    file_bytes = await file.read()
    if not file_bytes:
        return None

    try:
        resume_text = await asyncio.to_thread(read_resume, file_bytes, filename)
        if not resume_text.strip():
            return None

        parsed_resume = await asyncio.to_thread(parse_resume, resume_text)
    except Exception:
        return None

    try:
        match_result = await asyncio.to_thread(final_score, job_description, parsed_resume)
    except Exception:
        return None

    return match_result


def _select_ranked_candidates(results: list[MatchResult]) -> tuple[MatchResult | None, MatchResult | None]:
    scored_results = [result for result in results if result.score is not None]
    if not scored_results:
        return None, None

    top_candidate = max(scored_results, key=lambda result: result.score)
    bottom_candidate = min(scored_results, key=lambda result: result.score)
    return top_candidate, bottom_candidate


async def analyze_resumes(job_description_text: str, files: list[UploadFile]) -> ResumeAnalysisResponse:
    normalized_job_description = job_description_text.strip()
    if not normalized_job_description:
        raise HTTPException(status_code=400, detail="job_description_text cannot be empty.")

    if not files:
        raise HTTPException(status_code=400, detail="At least one resume file must be uploaded.")

    job_description = await asyncio.to_thread(get_job_details, normalized_job_description)

    results: list[MatchResult] = []
    for file in files:
        match_result = await _process_single_resume(file, job_description)
        if match_result is not None:
            results.append(match_result)

    summary = ResumeAnalysisSummary(
        total_files=len(files),
        processed_files=len(results),
        failed_files=max(len(files) - len(results), 0),
    )
    top_candidate, bottom_candidate = _select_ranked_candidates(results)

    return ResumeAnalysisResponse(
        job_description_text=normalized_job_description,
        job_description=job_description,
        summary=summary,
        results=results,
        top_candidate=top_candidate,
        bottom_candidate=bottom_candidate,
    )
