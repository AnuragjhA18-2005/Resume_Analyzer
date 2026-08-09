import json
from config import client, model
from models import jobDescription, Resume, MatchResult
from prompts import get_job_extraction_prompts, get_matcher_prompt, get_parser_prompts

def get_job_details() -> jobDescription:
    """Parses and extracts structured data from the job description template."""
    schema_dict = jobDescription.model_json_schema()
    system_p, user_p = get_job_extraction_prompts(schema_dict)
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_p},
            {"role": "user", "content": user_p}
        ],
        response_format={"type": "json_object"}
    )
    data = json.loads(response.choices[0].message.content)
    return jobDescription(**data)

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
    data = json.loads(response.choices[0].message.content)
    return Resume(**data)

def final_score(job: jobDescription, resume: Resume) -> MatchResult:
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
    data = json.loads(response.choices[0].message.content)
    return MatchResult(**data)
