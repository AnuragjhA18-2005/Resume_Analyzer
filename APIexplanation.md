# Resume Parser FastAPI Architecture

## 1. What This Project Does

This project analyzes resumes against a job description and returns a match score with structured details from the LLM.

In the original terminal version, the workflow was:

1. Load one hardcoded job description.
2. Read every resume from the local `resumes/` folder.
3. Extract raw text from each PDF/DOCX.
4. Parse the resume into structured JSON.
5. Score the resume against the job description.
6. Print the top and bottom candidate in the terminal.

The FastAPI version keeps the same core logic, but turns it into an HTTP API so a frontend like React can upload files and receive JSON responses.

---

## 2. High-Level Architecture

The app now follows a simple layered structure:

- `api/` handles HTTP routes.
- `services/` contains business logic and orchestration.
- `schemas/` defines the API response models.
- `core/` stores app-wide configuration and environment settings.
- Root modules like `parser.py`, `extractors.py`, and `models.py` contain the reusable logic that powers the analysis.

Think of the flow like this:

`Swagger / React frontend -> API route -> service layer -> parser/extractor logic -> Groq model -> response`

This separation makes the project easier to maintain and makes it ready for a frontend.

---

## 3. Request Lifecycle

When a client calls `POST /api/analyze`:

1. The frontend sends:
   - `job_description_text`
   - one or more resume files
2. `api/routes/analyze.py` receives the multipart form request.
3. `services/analyzer.py` validates the files and job description.
4. `parser.get_job_details()` converts the free-text job description into structured JSON.
5. For each resume:
   - `extractors.read_resume()` extracts raw text from PDF or DOCX bytes
   - `parser.parse_resume()` turns the text into a structured `Resume`
   - `parser.final_score()` compares the resume to the job and produces a `MatchResult`
6. The service aggregates the results, picks the top and bottom candidate by score, and returns the final response.

Important: the current response is intentionally trimmed. It returns the `MatchResult` for each processed candidate instead of the full parsed resume object, to keep the payload small.

---

## 4. Folder and File Guide

### `main.py`

This is the FastAPI entrypoint.

What it does:

- Creates the `FastAPI` app.
- Adds CORS middleware so a React frontend can call the API.
- Registers the `/api` router.
- Exposes `/health` for basic server checks.
- Overrides the generated OpenAPI schema so Swagger UI shows a file picker for uploads.

Why the OpenAPI override exists:

- FastAPI generated `files` as an `array<string>` shape in Swagger.
- Swagger UI does not render that as a proper file upload control.
- The custom `openapi()` function rewrites `files` to `type: array` with `items: { type: string, format: binary }`.
- That is the schema Swagger understands as a file upload field.

### `api/routes/analyze.py`

This file defines the HTTP endpoint for analysis.

Code responsibilities:

- Creates an `APIRouter` with the prefix `/analyze`.
- Declares `POST /api/analyze`.
- Accepts:
  - `job_description_text` as form text
  - `files` as uploaded files
- Delegates all work to `services.analyzer.analyze_resumes()`.

Why `Form(...)` and `File(...)` are used:

- `job_description_text` is submitted as form data.
- `files` is submitted as multipart file upload data.
- This is the correct format for Swagger UI and browser-based uploads.

### `services/analyzer.py`

This is the orchestration layer.

It contains three main pieces:

#### `_process_single_resume(file, job_description)`

- Checks the MIME type.
- Reads the upload bytes.
- Extracts text using `extractors.read_resume()`.
- Parses the resume using `parser.parse_resume()`.
- Scores it using `parser.final_score()`.
- Returns a `MatchResult` if processing succeeds, or `None` if the file fails at any stage.

#### `_select_ranked_candidates(results)`

- Looks at the successful `MatchResult` objects.
- Selects the highest score as `top_candidate`.
- Selects the lowest score as `bottom_candidate`.

#### `analyze_resumes(job_description_text, files)`

- Validates the request.
- Converts the job description text into a structured job profile using `get_job_details()`.
- Processes each uploaded resume.
- Builds the response object with:
  - `job_description_text`
  - `job_description`
  - `summary`
  - `results`
  - `top_candidate`
  - `bottom_candidate`

Why `asyncio.to_thread()` is used:

- PDF parsing, DOCX parsing, and external model calls are blocking operations.
- `asyncio.to_thread()` keeps the FastAPI event loop responsive while those blocking tasks run in a worker thread.

### `services/prompts.py`

This file contains the prompt-building functions used by the Groq model.

Functions:

#### `get_job_extraction_prompts(job_description_text, schema_dict)`

- Builds the system and user prompts for job description extraction.
- Tells the model how to convert raw job text into the `JobDescription` schema.

#### `get_matcher_prompt(job_json, resume_json, match_schema_dict)`

- Builds the prompt that compares a job description with a resume.
- Asks the model to produce a `MatchResult` with:
  - score
  - matching skills
  - missing skills
  - experience check
  - verdict

#### `get_parser_prompts(resume_text, resume_schema_dict)`

- Builds the prompt that converts raw resume text into a structured `Resume`.
- Tells the model how to infer experience, skills, education, and projects.

Important difference from the terminal version:

- The old `prompts.py` had a hardcoded sample job description constant.
- The FastAPI version uses the job description text sent by the client.
- That makes the API reusable for different roles and not tied to one fixed JD.

### `schemas/resume.py`

This file defines the API response shape.

Classes:

#### `ResumeAnalysisSummary`

Contains batch counts:

- `total_files`
- `processed_files`
- `failed_files`

#### `ResumeAnalysisResponse`

This is the final API response returned to the frontend.

It contains:

- `job_description_text`
- `job_description`
- `summary`
- `results`
- `top_candidate`
- `bottom_candidate`

Current payload design:

- `results` is a list of `MatchResult` objects only.
- That keeps the response small and avoids repeating parsed resume data for every candidate.

### `core/config.py`

This is the application configuration layer.

It loads environment variables and defines shared runtime values:

- `GROQ_API_KEY`
- `GROQ_MODEL`
- `APP_NAME`
- `APP_VERSION`
- `DEFAULT_CORS_ORIGINS`
- `ALLOWED_UPLOAD_TYPES`
- `client`
- `model`

Why this file exists:

- The app should not hardcode secrets or deployment-specific values.
- Environment-based config makes the app easier to deploy locally, in staging, or in production.

The `client` object here is the Groq API client used by `parser.py`.

### `extractors.py`

This file extracts text from resumes.

Functions:

#### `read_pdf(pdf_source)`

- Uses PyMuPDF to extract text from PDF files.
- Cleans up excessive newlines.

#### `read_docx(docx_source)`

- Uses `python-docx` to read DOCX files.
- Preserves the order of paragraphs and tables.
- Extracts table content row by row.

#### `read_resume(file_source, file_name=None)`

- Detects the file type from the filename.
- Routes to `read_pdf()` or `read_docx()`.
- Supports both local paths and in-memory upload bytes.

What changed from the terminal version:

- The terminal version only needed filesystem paths from `resumes/`.
- The FastAPI version also supports uploaded file bytes because files arrive from the request body, not the disk.

### `parser.py`

This file is the LLM interface layer.

Functions:

#### `_parse_json_payload(payload)`

- Safely parses the model response string into Python JSON.
- Raises a helpful error if the model returns invalid JSON.

#### `get_job_details(job_description_text)`

- Sends the job description text to the Groq model.
- Returns a structured `JobDescription`.

#### `parse_resume(resume_text)`

- Sends raw resume text to the Groq model.
- Returns a structured `Resume`.

#### `final_score(job, resume)`

- Sends the structured job and resume to the model.
- Returns a structured `MatchResult`.

How it worked in the terminal version:

- `get_job_details()` always used the hardcoded sample job in `prompts.py`.
- The FastAPI version accepts job description text from the request instead.

### `models.py`

This file defines the Pydantic data structures used throughout the project.

Classes:

#### `JobDescription`

Represents the extracted job posting fields:

- `role`
- `required_skills`
- `preferred_skills`
- `minimum_experience`
- `responsibilities`

#### `Experience`

Represents one work-history entry in a resume.

#### `Education`

Represents one education entry.

#### `Resume`

Represents the parsed resume:

- name
- email
- phone
- total experience
- skills
- experience list
- education list
- projects
- certifications

#### `MatchDetails`

Represents the reasoning behind the match:

- candidate name
- matching skills
- missing skills
- whether experience requirement is met
- short verdict

#### `MatchResult`

Represents the final scoring output:

- `score`
- `details`

Legacy note:

- `jobDescription = JobDescription` is a compatibility alias from the terminal version.
- The current FastAPI flow uses `JobDescription` directly.

### `api/__init__.py`, `api/routes/__init__.py`, `core/__init__.py`, `schemas/__init__.py`, `services/__init__.py`

These files are package markers.

They make the directories importable Python packages.

They do not contain runtime logic.

### `pyproject.toml`

This is the project manifest.

It declares:

- project name
- Python version requirement
- dependencies like:
  - `fastapi`
  - `groq`
  - `pydantic`
  - `pymupdf`
  - `python-docx`
  - `python-dotenv`
  - `python-multipart`
  - `uvicorn`

Why `python-multipart` matters:

- FastAPI needs it to parse `multipart/form-data` requests.
- Without it, file upload routes cannot work correctly.

Why `uvicorn` matters:

- Uvicorn is the ASGI server used to run the FastAPI app.

### `uv.lock`

This is the dependency lock file.

It pins exact package versions so installations are reproducible.

### `resumes/`

This folder contains sample resume files from the original terminal workflow.

In the FastAPI version, this folder is not part of the API path.

It can still be useful for local testing or reference data, but the API no longer depends on it.

### `FastAPI_Migration_Plan.md`

This is the design record for the FastAPI refactor.

It explains the architecture decisions that were made during the migration.

---

## 5. How the FastAPI Version Maps to the Original Terminal Version

### Original terminal `main.py`

The terminal app:

- loaded a fixed job description
- iterated over files in `resumes/`
- processed each file one by one
- printed the top and bottom candidate to the console

### New FastAPI flow

The FastAPI app:

- receives the job description from the client
- receives uploaded files from the request
- processes the resumes in the service layer
- returns JSON instead of printing to terminal

### Original terminal `config.py`

The old file:

- loaded `.env`
- created the Groq client
- hardcoded the model name

The new architecture moved that logic into `core/config.py` so configuration is central and reusable.

### Original terminal `prompts.py`

The old file:

- contained the prompt templates
- also held a hardcoded job description sample

The new architecture keeps only the prompt builders and removes the fixed job sample.

### Original terminal `extractors.py`

The old file:

- read PDF and DOCX files from disk paths only

The new file:

- still supports disk paths
- also supports in-memory uploaded files from FastAPI

### Original terminal `parser.py`

The old file:

- called Groq to extract job, resume, and score data
- used the fixed job description from `prompts.py`

The new file:

- does the same model calls
- but now the job description is user-provided per request

### Original terminal `models.py`

The models were already the backbone of the project.

Those same Pydantic models continue to define the data contract in the API version.

---

## 6. Why the Architecture Is Better Now

- The API is reusable for any job description, not just one hardcoded JD.
- The frontend can upload files directly.
- The response is structured JSON, which is ideal for React.
- Business logic is isolated from routing logic.
- Prompt generation is isolated from parsing logic.
- File extraction is now compatible with both local files and uploaded bytes.
- The OpenAPI schema has been adjusted so Swagger UI shows a file picker correctly.

---

## 7. Practical Mental Model for Beginners

If you are new to FastAPI, remember this simple rule:

- `main.py` starts the app.
- `api/routes/` receives HTTP requests.
- `services/` does the real work.
- `schemas/` defines the shape of data going in and out.
- `core/` stores config and secrets.
- `parser.py`, `extractors.py`, and `models.py` are the engine underneath the API.

If you understand those five ideas, you understand the project.

