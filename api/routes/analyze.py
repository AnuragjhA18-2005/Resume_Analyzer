from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile

from schemas.resume import ResumeAnalysisResponse
from services.analyzer import analyze_resumes

router = APIRouter(prefix="/analyze", tags=["analysis"])


@router.post("", response_model=ResumeAnalysisResponse)
async def upload_resumes(
    job_description_text: Annotated[str, Form(...)],
    files: Annotated[list[UploadFile], File(...)],
):
    return await analyze_resumes(job_description_text=job_description_text, files=files)

