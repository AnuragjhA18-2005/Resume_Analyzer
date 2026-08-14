import json

from core.config import GROQ_MODEL_CANDIDATES
from models import JobDescription, MatchResult, Resume
from services.prompts import get_job_extraction_prompts, get_matcher_prompt, get_parser_prompts
from services.llm import complete_json


def _parse_json_payload(payload: str) -> dict:
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model returned invalid JSON: {exc}") from exc


def get_job_details(job_description_text: str) -> JobDescription:
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


def parse_resume(resume_text: str) -> Resume:
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


def final_score(job: JobDescription, resume: Resume) -> MatchResult:
    """Matches a parsed resume against a job description, computing a compatibility score."""
    match_schema = MatchResult.model_json_schema()
    prompt_text = get_matcher_prompt(
        job.model_dump_json(indent=2),
        resume.model_dump_json(indent=2),
        match_schema
    )

    content = complete_json(
        [
            {"role": "user", "content": prompt_text}
        ],
        model_candidates=GROQ_MODEL_CANDIDATES,
    )
    data = _parse_json_payload(content)
    return MatchResult(**data)
