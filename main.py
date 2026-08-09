import json
import time
from pathlib import Path
from extractors import read_resume
from parser import get_job_details, parse_resume, final_score

def main():
    print("Initializing Job Description extraction...")
    job = get_job_details()
    
    resume_folder = Path('resumes')
    all_results = []
    
    if not resume_folder.exists():
        print(f"Directory '{resume_folder}' not found. Please create it and add resumes.")
        return
        
    for file_path in resume_folder.iterdir():
        if file_path.suffix.lower() not in ['.pdf', '.docx']:
            continue
            
        print(f"\nProcessing candidate: {file_path.name}")
        try:
            resume_text = read_resume(file_path)
            parsed_resume = parse_resume(resume_text)
            
            # API Rate Limit mitigation delay
            time.sleep(5)
            
            result = final_score(job, parsed_resume)
            print(f"Completed match scoring. Score: {result.score}%")
            
            # Delay before next resume loop
            time.sleep(5)
            
            all_results.append({
                'name': parsed_resume.name or file_path.stem,
                'score': result.score,
                'details': result.details.model_dump()
            })
        except Exception as e:
            print(f"Failed to process {file_path.name}: {e}")
            
    # Sort results in descending order of compatibility score
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    if all_results:
        top = all_results[0]
        bottom = all_results[-1]
        
        print("\n" + "="*50)
        print("TOP CANDIDATE DETAIL")
        print("="*50)
        print(f"Name: {top['name']}")
        print(f"Match Score: {top['score']}%")
        print("Details:")
        print(json.dumps(top['details'], indent=4))
        
        print("\n" + "="*50)
        print("BOTTOM CANDIDATE DETAIL")
        print("="*50)
        print(f"Name: {bottom['name']}")
        print(f"Match Score: {bottom['score']}%")
        print("Details:")
        print(json.dumps(bottom['details'], indent=4))
        print("="*50)
    else:
        print("\nNo resumes were successfully processed.")

if __name__ == "__main__":
    main()
