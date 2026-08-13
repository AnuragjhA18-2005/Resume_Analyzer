export interface MatchDetails {
  candidate_name: string | null;
  email: string | null;
  matching_skills: string[];
  missing_skills: string[];
  experience_requirement_met: boolean;
  verdict: string;
}

export interface MatchResult {
  score: number;
  details: MatchDetails;
}

export interface ResumeAnalysisResponse {
  job_description_text: string;
  job_description: {
    role: string;
    required_skills: string[];
    preferred_skills: string[];
    minimum_experience: number | null;
    responsibilities: string[];
  };
  summary: {
    total_files: number;
    processed_files: number;
    failed_files: number;
  };
  results: MatchResult[];
  top_candidate: MatchResult | null;
  bottom_candidate: MatchResult | null;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

export async function analyzeResumes(jobDescriptionText: string, files: File[]) {
  const formData = new FormData();
  formData.append('job_description_text', jobDescriptionText);

  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail = payload?.detail ?? `Request failed with status ${response.status}`;
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }

  return (await response.json()) as ResumeAnalysisResponse;
}
