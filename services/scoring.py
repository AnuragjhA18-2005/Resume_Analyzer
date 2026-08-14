from __future__ import annotations

import re
from functools import lru_cache

from models import JobDescription, MatchDetails, MatchResult, Resume


def _normalize_text(value: str) -> str:
    value = value.lower()
    value = value.replace("/", " ").replace("-", " ")
    value = re.sub(r"[^a-z0-9+#.\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


_ALIAS_GROUPS: dict[str, set[str]] = {
    "restful api design": {
        "restful api design",
        "rest api",
        "rest api design",
        "rest",
        "api",
        "apis",
        "fastapi",
        "flask",
        "django",
        "express",
        "spring boot",
        "nestjs",
    },
    "git version control": {
        "git version control",
        "version control",
        "git",
        "github",
        "gitlab",
        "bitbucket",
    },
    "microservices architecture": {
        "microservices architecture",
        "docker",
        "kubernetes",
        "grpc",
        "rabbitmq",
        "kafka",
    },
    "cs fundamentals data structures and algorithms": {
        "cs fundamentals data structures and algorithms",
        "data structures",
        "algorithms",
        "dsa",
    },
    "system design object oriented analysis and design": {
        "system design object oriented analysis and design",
        "object oriented programming",
        "object oriented analysis and design",
        "oop",
    },
}

_SKILL_TO_CANONICAL: dict[str, str] = {}
for canonical, aliases in _ALIAS_GROUPS.items():
    for alias in aliases:
        _SKILL_TO_CANONICAL[alias] = canonical


def _canonical_skill(value: str) -> str:
    normalized = _normalize_text(value)
    return _SKILL_TO_CANONICAL.get(normalized, normalized)


def _unique_skills(skills: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for skill in skills:
        cleaned = skill.strip()
        if not cleaned:
            continue
        canonical = _canonical_skill(cleaned)
        if canonical in seen:
            continue
        seen.add(canonical)
        ordered.append(cleaned)
    return ordered


def _resume_signal_keys(resume: Resume) -> set[str]:
    signals: list[str] = []
    signals.extend(resume.skills)
    signals.extend(skill for experience in resume.experience for skill in experience.skills_used)
    signals.extend(resume.projects)
    signals.extend(resume.certifications)
    signals.extend(
        field
        for education in resume.education
        for field in (education.degree, education.institution)
        if field
    )
    return {_canonical_skill(signal) for signal in signals if signal.strip()}


def _skill_is_present(job_skill: str, resume_skill_keys: set[str]) -> bool:
    canonical = _canonical_skill(job_skill)
    if canonical in resume_skill_keys:
        return True

    normalized_job_skill = _normalize_text(job_skill)
    return any(normalized_job_skill in key or key in normalized_job_skill for key in resume_skill_keys)


def _match_skills(job_skills: list[str], resume_skill_keys: set[str]) -> tuple[list[str], list[str]]:
    matching_skills: list[str] = []
    missing_skills: list[str] = []

    for skill in _unique_skills(job_skills):
        if _skill_is_present(skill, resume_skill_keys):
            matching_skills.append(skill)
        else:
            missing_skills.append(skill)

    return matching_skills, missing_skills


def _dedupe_skills_by_canonical(existing_skills: list[str], new_skills: list[str]) -> list[str]:
    seen = {_canonical_skill(skill) for skill in existing_skills}
    deduped = list(existing_skills)

    for skill in new_skills:
        canonical = _canonical_skill(skill)
        if canonical in seen:
            continue
        seen.add(canonical)
        deduped.append(skill)

    return deduped


def _skill_score(job: JobDescription, matching_required: list[str], matching_preferred: list[str]) -> float:
    required_total = len(_unique_skills(job.required_skills))
    preferred_total = len(_unique_skills(job.preferred_skills))

    if required_total:
        required_ratio = len(matching_required) / required_total
        preferred_bonus = 0.0
        if preferred_total:
            preferred_bonus = 0.15 * (len(matching_preferred) / preferred_total)
        return min(100.0, round((required_ratio * 85.0) + (preferred_bonus * 100.0), 1))

    if preferred_total:
        return round((len(matching_preferred) / preferred_total) * 100.0, 1)

    return 100.0


def _experience_score(job: JobDescription, resume: Resume) -> tuple[bool, float]:
    total_years = resume.total_experience_years or 0.0
    required_years = job.minimum_experience

    if required_years is None or required_years <= 0:
        return True, 100.0

    meets_requirement = total_years >= required_years
    score = min(total_years / required_years, 1.0) * 100.0
    return meets_requirement, round(score, 1)


def _education_project_score(resume: Resume) -> float:
    score = 0.0
    if resume.education:
        score += 50.0
    if resume.projects:
        score += 50.0
    return min(score, 100.0)


def _verdict(score: float, job: JobDescription, details: MatchDetails) -> str:
    if score >= 85:
        prefix = "Strong fit."
    elif score >= 70:
        prefix = "Good fit with manageable gaps."
    elif score >= 50:
        prefix = "Moderate fit with several gaps."
    else:
        prefix = "Weak fit for this role."

    parts: list[str] = [prefix]

    if details.matching_skills:
        parts.append(f"Matched skills: {', '.join(details.matching_skills[:6])}.")

    if details.missing_skills:
        parts.append(f"Missing skills: {', '.join(details.missing_skills[:6])}.")
    else:
        parts.append("No required skill gaps detected.")

    if job.minimum_experience is None or job.minimum_experience <= 0:
        parts.append("No minimum experience requirement was specified.")
    elif details.experience_requirement_met:
        parts.append(f"Meets the {job.minimum_experience:g}-year experience requirement.")
    else:
        parts.append(f"Does not meet the {job.minimum_experience:g}-year experience requirement.")

    return " ".join(parts)


@lru_cache(maxsize=512)
def _final_score_cached(job_json: str, resume_json: str) -> MatchResult:
    job = JobDescription.model_validate_json(job_json)
    resume = Resume.model_validate_json(resume_json)

    resume_skill_keys = _resume_signal_keys(resume)
    matching_required, missing_required = _match_skills(job.required_skills, resume_skill_keys)
    matching_preferred, _ = _match_skills(job.preferred_skills, resume_skill_keys)
    matching_skills = _dedupe_skills_by_canonical(matching_required, matching_preferred)

    experience_requirement_met, experience_score = _experience_score(job, resume)
    skill_score = _skill_score(job, matching_required, matching_preferred)
    education_project_score = _education_project_score(resume)
    final_score = round(
        (skill_score * 0.5) + (experience_score * 0.3) + (education_project_score * 0.2),
        1,
    )

    details = MatchDetails(
        candidate_name=resume.name,
        email=resume.email,
        matching_skills=matching_skills,
        missing_skills=missing_required,
        experience_requirement_met=experience_requirement_met,
        verdict="",
    )
    details = details.model_copy(update={"verdict": _verdict(final_score, job, details)})
    return MatchResult(score=final_score, details=details)


def score_match(job: JobDescription, resume: Resume) -> MatchResult:
    return _final_score_cached(job.model_dump_json(), resume.model_dump_json()).model_copy(deep=True)
