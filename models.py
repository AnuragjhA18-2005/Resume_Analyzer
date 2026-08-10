from pydantic import BaseModel, Field


class JobDescription(BaseModel):
    role: str = Field(..., description="Job role of the hired candidate")
    required_skills: list[str] = Field(
        default_factory=list,
        description="Mandatory or required technical or soft skills",
    )
    preferred_skills: list[str] = Field(
        default_factory=list,
        description="Preferred qualifications or skills",
    )
    minimum_experience: float | None = Field(
        default=None,
        description="Minimum experience in years required, or null if not specified",
    )
    responsibilities: list[str] = Field(
        default_factory=list,
        description="Core responsibilities and duties",
    )

class Experience(BaseModel):
    company: str | None = Field(None, description="Company name")
    role: str | None = Field(None, description="Job title")
    duration_months: int | None = Field(None, description="Estimated duration in months, or calculated from start/end dates")
    description: str | None = Field(None, description="Description of achievements and responsibilities")
    skills_used: list[str] = Field(default_factory=list, description="List of technologies/skills specifically used in this role")

class Education(BaseModel):
    institution: str | None = Field(None, description="Name of university or school")
    degree: str | None = Field(None, description="Degree name (e.g., BS Computer Science)")
    graduation_year: int | None = Field(None, description="Year of graduation")

class Resume(BaseModel):
    name: str | None = Field(None,description='Name of The Candidate')
    email: str | None = Field(None,description='Email of The Candidate')
    phone: str | None = Field(None,description='Phone Number of the Candidate')
    total_experience_years: float | None = Field(
        default=None,
        description="Experience of the Candidate in years",
    )
    skills: list[str] = Field(
        default_factory=list,
        description="General skills listed or extracted from the resume",
    )
    experience: list[Experience] = Field(default_factory=list, description="Work and internship history")
    education: list[Education] = Field(default_factory=list, description="Educational qualifications")
    projects: list[str] = Field(default_factory=list, description="Key projects completed")
    certifications: list[str] = Field(default_factory=list, description="Professional certifications")

class MatchDetails(BaseModel):
    candidate_name: str | None = Field(None, description="Name of the candidate")
    matching_skills: list[str] = Field(default_factory=list, description="Skills matching the job description")
    missing_skills: list[str] = Field(default_factory=list, description="Important skills missing from the candidate's profile")
    experience_requirement_met: bool = Field(description="True if candidate's experience is sufficient, else False")
    verdict: str = Field(description="A concise summary of the candidate's fit")

class MatchResult(BaseModel):
    score: float = Field(description="Overall match percentage from 0.0 to 100.0 based on criteria fit")
    details: MatchDetails = Field(description="Structured details of the candidate evaluation")


jobDescription = JobDescription
