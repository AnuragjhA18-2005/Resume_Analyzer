import json

from core.config import client, model
from models import JobDescription, MatchResult, Resume
from services.prompts import get_job_extraction_prompts, get_matcher_prompt, get_parser_prompts


def _parse_json_payload(payload: str) -> dict:
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model returned invalid JSON: {exc}") from exc


def get_job_details(job_description_text: str) -> JobDescription:
    """Parses and extracts structured data from the job description template."""
    schema_dict = JobDescription.model_json_schema()
    system_p, user_p = get_job_extraction_prompts(job_description_text, schema_dict)
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_p},
            {"role": "user", "content": user_p}
        ],
        response_format={"type": "json_object"}
    )
    data = _parse_json_payload(response.choices[0].message.content)
    return JobDescription(**data)

def parse_resume(resume_text: str) -> Resume:
    """Parses raw resume text into a structured Pydantic Resume model."""
    schema_dict = Resume.model_json_schema()
    system_p, user_p = get_parser_prompts(resume_text, schema_dict)
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_p},
            {"role": "user", "content": user_p}
        ],
        response_format={"type": "json_object"}
    )
    data = _parse_json_payload(response.choices[0].message.content)
    return Resume(**data)


def final_score(job: JobDescription, resume: Resume) -> MatchResult:
    """Matches a parsed resume against a job description, computing a compatibility score."""
    match_schema = MatchResult.model_json_schema()
    prompt_text = get_matcher_prompt(
        job.model_dump_json(indent=2),
        resume.model_dump_json(indent=2),
        match_schema
    )
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt_text}
        ],
        response_format={"type": "json_object"}
    )
    data = _parse_json_payload(response.choices[0].message.content)
    return MatchResult(**data)
