import json

JOB_DESCRIPTION_TEXT = """
Job Title: Software Development Engineer I (SDE-1) Intern
Department: Engineering / Software Development
Target Candidates: Undergraduate or Postgraduate Students (Computer Science & Related STEM Fields)
## Position Overview
The Software Development Engineer (SDE) I Intern will contribute to the design, development, and deployment of scalable, multi-tiered software solutions. Operating within an agile ecosystem, the intern will own a discrete project end-to-end, writing production-ready code that impacts large-scale distributed systems, cloud applications, or customer-facing platforms.
## Core Responsibilities

* Design, implement, test, and deploy software features for large-scale distributed computing environments.
* Write clean, stable, highly maintainable, and well-documented code.
* Define and analyze technical specifications, selecting optimal algorithms and data structures.
* Collaborate with mentors, tech leads, and product managers to clarify scope and resolve dependencies.
* Participate actively in technical design reviews, code reviews, and agile sprint ceremonies.

## Mandatory Technical & Academic Qualifications (Hard Filters)

* Education: Current enrollment in a Bachelor’s, Master’s, or Dual Degree program in Computer Science, Computer Engineering, or a highly quantitative STEM discipline.
* Programming Proficiency: Demonstrated technical capability in at least one object-oriented or general-purpose language (e.g., Java, C++, Python, Go, C#).
* CS Fundamentals: Academic or practical mastery of core Computer Science principles, including Data Structures (arrays, trees, graphs, hash tables) and Algorithms (sorting, searching, dynamic programming, complexity analysis/Big-O notation).
* System Design: Foundational understanding of object-oriented analysis and design (OOAD) and software design patterns.

## Preferred Qualifications (Value-Add Signals)

* Practical Experience: Previous technical internships, open-source contributions, or comprehensive capstone software projects.
* Infrastructure Knowledge: Exposure to cloud computing architectures (AWS ecosystem preferred), RESTful API design, or microservices architecture.
* Data Management: Working knowledge of relational databases (SQL) or NoSQL data stores.
* Development Tools: Familiarity with modern development workflows, including Git/version control, CI/CD pipelines, and automated testing frameworks (Unit/Integration testing).
* Problem-Solving Framework: Strong analytical skills with a proven aptitude for decomposing ambiguous, complex technical requirements into structured components.
"""

def get_job_extraction_prompts(schema_dict: dict) -> tuple[str, str]:
    system_prompt = f"""You are an expert HR assistant specializing in structured data extraction.

Your task is to analyze the provided Job Description and extract key structured fields into a clean JSON format.

Return ONLY a valid JSON object matching this schema:
{json.dumps(schema_dict, indent=2)}

Guidelines for Extraction:
- "role": Extract the official job title / role name.
- "required_skills": List mandatory/required technical or soft skills explicitly mentioned.
- "preferred_skills": List nice-to-have, optional, or value-add qualifications/skills.
- "minimum_experience": If a minimum number of years of experience is specified (e.g., "3+ years", "minimum 2 years"), extract it as a float. If no minimum experience is specified or implied, return null.
- "responsibilities": List the core duties, tasks, and responsibilities.

Critical Constraints:
1. Do NOT return the schema structure itself (e.g. do not output keys like 'properties', 'title', or 'type' at the top level).
2. Do NOT invent or extrapolate information. If a field is not mentioned, return null (for scalar values) or an empty list (for arrays).
3. Output ONLY valid, parseable JSON. Do not include markdown code block syntax (like ```json ... ```) in the raw response unless using standard JSON formats.
"""
    user_prompt = f"""Analyze the following job description and extract the structured information:

<JOB_DESCRIPTION>
{JOB_DESCRIPTION_TEXT}
</JOB_DESCRIPTION>
"""
    return system_prompt, user_prompt

def get_matcher_prompt(job_json: str, resume_json: str, match_schema_dict: dict) -> str:
    return f"""You are an expert HR recruiter and talent acquisition analyst.

Your task is to compare the candidate's resume with the job description and calculate a match score.

Compare the specifications and compute an overall score from 0.0 to 100.0 based on:
1. Skills Match (Weight: 50%): Ratio of matching skills vs required skills.
2. Experience Match (Weight: 30%): Does the candidate's experience level and history align with the job needs?
3. Education & Projects (Weight: 20%): Relevance of academic credentials and projects.

Return ONLY a valid JSON object matching this schema:
{json.dumps(match_schema_dict, indent=2)}

Critical Constraints & Guidelines:
1. MUTUAL EXCLUSIVITY: A skill or requirement cannot be listed in both "matching_skills" and "missing_skills". Every qualification is either present or missing.
2. CONCEPTUAL EQUIVALENCE & IMPLIED SKILLS:
   - Treat conceptual matches, frameworks, and abbreviations as identical.
   - If the candidate lists web framework APIs like "FastAPI", "Flask", "Django", "Express", "Spring Boot", "NestJS", "REST", or "APIs", then "RESTful API design" is MET and must NOT be listed in "missing_skills".
   - If the resume lists tools/platforms like "Git", "GitHub", "GitLab", "Bitbucket", then "Git/version control" is MET.
   - If the resume lists "Docker", "Kubernetes", "gRPC", or "RabbitMQ/Kafka", then "Microservices architecture" is MET.
   - If the resume lists "DSA", "Data Structures", or "Algorithms", then "CS Fundamentals: Data Structures and Algorithms" is MET.
   - If the resume lists "OOP" or "Object Oriented Programming", then "System Design: object-oriented analysis and design" is MET.
3. "candidate_name": The candidate's name extracted from the resume.
4. "matching_skills": Skills listed in the resume that correspond to either required or preferred skills in the job description.
5. "missing_skills": Critical required skills in the job description that are missing from the resume.
6. "experience_requirement_met": Compare total_experience_years of the resume against the job description's minimum_experience. Set to true if the candidate meets/exceeds it or if no minimum experience is required. Otherwise, set to false.
7. "verdict": A clear, professional summary justifying the score and suitability.

INPUT DATA:

<JOB_DESCRIPTION>
{job_json}
</JOB_DESCRIPTION>

<CANDIDATE_RESUME>
{resume_json}
</CANDIDATE_RESUME>
"""

def get_parser_prompts(resume_text: str, resume_schema_dict: dict) -> tuple[str, str]:
    system_prompt = f"""You are a professional, high-fidelity resume parsing system.

Analyze the raw text extracted from the candidate's resume and parse it into structured JSON.
Ensure you infer sections conceptually (e.g., 'Work History', 'Professional Experience', or 'Employment' should map to experience).

Return ONLY a valid JSON object matching this schema:
{json.dumps(resume_schema_dict, indent=2)}

Important Extraction Rules:
1. Do NOT invent or extrapolate information. If information is not in the text, return null or empty lists as appropriate.
2. "experience": Extract work history, including internships. Try to estimate "duration_months" based on start/end dates if explicitly stated (e.g., "June 2022 - Aug 2022" -> 3).
3. "skills_used" in each experience entry MUST be a list. If no skills are mentioned for a role, return an empty list `[]` instead of null.
4. "total_experience_years": Sum the duration of all professional experiences. Avoid double-counting overlapping timelines.
5. "skills": Extract all technical, domain, and soft skills listed across the entire resume.
6. "education": Parse each educational entry. Extract degree names, institutions, and graduation years carefully.

Ensure the output is valid JSON.
"""
    user_prompt = f"""Extract structured data from the following resume text:

<RESUME_TEXT>
{resume_text}
</RESUME_TEXT>
"""
    return system_prompt, user_prompt