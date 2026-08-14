from __future__ import annotations

from core.config import JOB_DESCRIPTION_MAX_CHARS, RESUME_TEXT_MAX_CHARS


def _truncate_text(text: str, limit: int) -> str:
    normalized = text.strip()
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit].rstrip()}\n...[truncated]"


def get_job_extraction_prompts(job_description_text: str, schema_dict: dict) -> tuple[str, str]:
    del schema_dict

    system_prompt = """You extract job descriptions into compact JSON.

Return only a JSON object with these keys:
- role
- required_skills
- preferred_skills
- minimum_experience
- responsibilities

Rules:
- Use null for missing scalar values.
- Use empty arrays for missing list values.
- Do not invent facts.
- Output JSON only.
"""
    user_prompt = f"""Analyze this job description and extract the structured information:

<JOB_DESCRIPTION>
{_truncate_text(job_description_text, JOB_DESCRIPTION_MAX_CHARS)}
</JOB_DESCRIPTION>
"""
    return system_prompt, user_prompt


def get_matcher_prompt(job_json: str, resume_json: str, match_schema_dict: dict) -> str:
    del match_schema_dict

    return f"""Compare the candidate resume to the job description and return compact JSON.

Output keys:
- score
- details.candidate_name
- details.email
- details.matching_skills
- details.missing_skills
- details.experience_requirement_met
- details.verdict

Rules:
- Keep matching_skills and missing_skills mutually exclusive.
- Treat equivalent frameworks, abbreviations, and obvious synonyms as matches.
- JSON only.

INPUT DATA:

<JOB_DESCRIPTION>
{job_json}
</JOB_DESCRIPTION>

<CANDIDATE_RESUME>
{resume_json}
</CANDIDATE_RESUME>
"""


def get_parser_prompts(resume_text: str, resume_schema_dict: dict) -> tuple[str, str]:
    del resume_schema_dict

    system_prompt = """You parse resumes into compact JSON.

Return only a JSON object with these keys:
- name
- email
- phone
- total_experience_years
- skills
- experience
- education
- projects
- certifications

Rules:
- Use null for missing scalar values.
- Use empty arrays for missing list values.
- Do not invent facts.
- Output JSON only.
"""
    user_prompt = f"""Extract structured data from this resume text:

<RESUME_TEXT>
{_truncate_text(resume_text, RESUME_TEXT_MAX_CHARS)}
</RESUME_TEXT>
"""
    return system_prompt, user_prompt
