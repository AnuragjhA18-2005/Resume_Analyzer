import json
from functools import lru_cache

from core.config import GROQ_MODEL_CANDIDATES
from models import JobDescription, MatchResult, Resume
from services.prompts import get_job_extraction_prompts, get_parser_prompts
from services.llm import complete_json
from services.scoring import score_match


def _parse_json_payload(payload: str) -> dict:
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model returned invalid JSON: {exc}") from exc


@lru_cache(maxsize=128)
def _get_job_details_cached(job_description_text: str, model_candidates: tuple[str, ...]) -> JobDescription:
    """Parses and extracts structured data from the job description template."""
    schema_dict = JobDescription.model_json_schema()
    system_p, user_p = get_job_extraction_prompts(job_description_text, schema_dict)

    content = complete_json(
        [
            {"role": "system", "content": system_p},
            {"role": "user", "content": user_p},
        ],
        model_candidates=model_candidates,
    )
    data = _parse_json_payload(content)
    return JobDescription(**data)


def get_job_details(job_description_text: str) -> JobDescription:
    return _get_job_details_cached(job_description_text, GROQ_MODEL_CANDIDATES).model_copy(deep=True)


@lru_cache(maxsize=256)
def _parse_resume_cached(resume_text: str, model_candidates: tuple[str, ...]) -> Resume:
    """Parses raw resume text into a structured Pydantic Resume model."""
    schema_dict = Resume.model_json_schema()
    system_p, user_p = get_parser_prompts(resume_text, schema_dict)

    content = complete_json(
        [
            {"role": "system", "content": system_p},
            {"role": "user", "content": user_p},
        ],
        model_candidates=model_candidates,
    )
    data = _parse_json_payload(content)
    return Resume(**data)


def parse_resume(resume_text: str) -> Resume:
    return _parse_resume_cached(resume_text, GROQ_MODEL_CANDIDATES).model_copy(deep=True)


def final_score(job: JobDescription, resume: Resume) -> MatchResult:
    """Matches a parsed resume against a job description, computing a compatibility score."""
    return score_match(job, resume)
