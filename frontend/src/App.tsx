import React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import './App.css';
import InteractiveNebulaShader from './components/ui/InteractiveNebulaShader';
import { analyzeResumes, type MatchResult, type ResumeAnalysisResponse } from './lib/api';

function EyeIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <path d="M2.1 12s3.6-7 9.9-7 9.9 7 9.9 7-3.6 7-9.9 7-9.9-7-9.9-7Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function App() {
  const [jobDesc, setJobDesc] = React.useState('');
  const [files, setFiles] = React.useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<ResumeAnalysisResponse | null>(null);
  const [expandedCards, setExpandedCards] = React.useState({ top: false, bottom: false });
  const [showAllCandidates, setShowAllCandidates] = React.useState(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setFiles(Array.from(event.target.files));
    }
  };

  const handleFormSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await analyzeResumes(jobDesc, files);
      setResult(response);
      setExpandedCards({ top: false, bottom: false });
      setShowAllCandidates(false);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : 'Failed to analyze resumes');
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderCompactCard = (
    label: string,
    candidate: MatchResult | null,
    isExpanded: boolean,
    onToggle: () => void,
  ) => {
    if (!candidate) {
      return (
        <div className="result-card result-card-empty">
          <p className="result-label">{label}</p>
          <h4>No scored candidate available</h4>
          <p className="result-muted">Upload valid resumes to see this section populate.</p>
        </div>
      );
    }

    return (
      <div className="result-card compact-card">
        <div className="compact-card-header">
          <p className="result-label">{label}</p>
          <h4 className="compact-name">{candidate.details.candidate_name || 'Unnamed Candidate'}</h4>
          <p className="compact-email">
            <span>Email:</span> {candidate.details.email || 'No email extracted'}
          </p>
          <p className="compact-verdict">{candidate.details.verdict}</p>

          <button type="button" className="analysis-toggle" onClick={onToggle} aria-expanded={isExpanded}>
            <EyeIcon />
            <span>{isExpanded ? 'Hide Detailed Analysis' : 'View Detailed Analysis'}</span>
          </button>
        </div>

        <AnimatePresence initial={false}>
          {isExpanded && (
            <motion.div
              key="expanded-analysis"
              className="compact-expanded"
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.35, ease: 'easeInOut' }}
            >
              <div className="compact-expanded-inner">
                <div className="expanded-row">
                  <span>Score</span>
                  <p>{candidate.score.toFixed(1)}%</p>
                </div>
                <div className="expanded-row">
                  <span>Matching Skills</span>
                  <p>{candidate.details.matching_skills.length > 0 ? candidate.details.matching_skills.join(', ') : 'None listed'}</p>
                </div>
                <div className="expanded-row">
                  <span>Missing Skills</span>
                  <p>{candidate.details.missing_skills.length > 0 ? candidate.details.missing_skills.join(', ') : 'None listed'}</p>
                </div>
                <div className="expanded-row">
                  <span>Experience Check</span>
                  <p>{candidate.details.experience_requirement_met ? 'Met' : 'Not met'}</p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  };

  return (
    <div className="app-container">
      <InteractiveNebulaShader />
      <section className="value-prop">
        <div className="container">
          <motion.div
            className="value-prop-header"
            initial={{ opacity: 0, y: -40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 1.5, ease: 'easeOut' }}
          >
            <div className="mb-4 text-3xl md:text-5xl font-black uppercase tracking-wider text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.4)] flex items-center justify-center">
              <span>RESUME</span>
              <span className="text-gray-500 ml-1 font-light drop-shadow-none">AI</span>
            </div>
          </motion.div>

          <div className="value-prop-inner">
            <motion.div
              className="value-prop-animation-container"
              initial={{ opacity: 0, x: -60 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 1.5, delay: 0.3, ease: 'easeOut' }}
            >
              <video
                src="/images/output.webm"
                autoPlay
                loop
                muted
                playsInline
                className="value-prop-animation"
              />
            </motion.div>

            <motion.div
              className="value-prop-visual"
              initial={{ opacity: 0, x: 60 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 1.5, delay: 0.5, ease: 'easeOut' }}
            >
              <div className="job-desc-form-card">
                <h3>Enter Job Requirements</h3>
                <form onSubmit={handleFormSubmit}>
                  <div className="form-group">
                    <label htmlFor="job-desc">Job Description</label>
                    <textarea
                      id="job-desc"
                      placeholder="Paste the full job description here..."
                      value={jobDesc}
                      onChange={(e) => setJobDesc(e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="resumes">Upload Resumes</label>
                    <div className="file-upload-zone">
                      <input
                        type="file"
                        id="resumes"
                        multiple
                        accept=".pdf,.docx"
                        onChange={handleFileChange}
                        className="file-input"
                        required
                      />
                      <div className="upload-placeholder">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" />
                        </svg>
                        <span>
                          {files.length > 0 ? `${files.length} file(s) selected` : 'Drag & drop or click to upload resumes'}
                        </span>
                      </div>
                    </div>

                    {files.length > 0 && (
                      <div className="selected-files">
                        {files.map((file) => (
                          <span key={file.name}>{file.name}</span>
                        ))}
                      </div>
                    )}
                  </div>

                  <button type="submit" className="btn btn-primary btn-block flex items-center justify-center gap-2 h-12" disabled={isSubmitting}>
                    {isSubmitting ? (
                      <>
                        <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Analyzing...
                      </>
                    ) : 'Start Candidate Screening'}
                  </button>
                </form>

                {error && (
                  <motion.div 
                    initial={{ opacity: 0, y: -10 }} 
                    animate={{ opacity: 1, y: 0 }} 
                    className="mt-4 p-3 bg-red-900/30 border border-red-500/50 rounded-lg text-red-200 text-sm text-center"
                  >
                    {error}
                  </motion.div>
                )}

                <p className="mt-4 text-xs text-gray-400 text-center font-light leading-relaxed">
                  Efficiently screen hundreds of candidates. No more tedious manual reviews. Find top matches instantly.
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {result && (
        <section className="results-section">
          <div className="container">
            <motion.div
              className="results-header"
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <h2>Analysis Results</h2>
              <p>
                Processed {result.summary.processed_files} of {result.summary.total_files} uploaded files.
              </p>
            </motion.div>

            <div className="results-summary-grid">
              <div className="summary-card">
                <span>Total Files</span>
                <strong>{result.summary.total_files}</strong>
              </div>
              <div className="summary-card">
                <span>Processed</span>
                <strong>{result.summary.processed_files}</strong>
              </div>
              <div className="summary-card">
                <span>Failed</span>
                <strong>{result.summary.failed_files}</strong>
              </div>
              <div className="summary-card">
                <span>Job Role</span>
                <strong>{result.job_description.role}</strong>
              </div>
            </div>

            <div className="top-bottom-grid">
              {renderCompactCard('Top Candidate', result.top_candidate, expandedCards.top, () =>
                setExpandedCards((current) => ({ ...current, top: !current.top })),
              )}
              {renderCompactCard('Bottom Candidate', result.bottom_candidate, expandedCards.bottom, () =>
                setExpandedCards((current) => ({ ...current, bottom: !current.bottom })),
              )}
            </div>

            <div className="all-candidates-cta">
              <button
                type="button"
                className="analysis-toggle all-candidates-toggle"
                onClick={() => setShowAllCandidates((current) => !current)}
                aria-expanded={showAllCandidates}
              >
                <span>{showAllCandidates ? 'Hide all candidates' : 'All candidates'}</span>
              </button>
            </div>

            <AnimatePresence initial={false}>
              {showAllCandidates && (
                <motion.div
                  className="results-list"
                  initial={{ opacity: 0, y: 24 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 24 }}
                  transition={{ duration: 0.35, ease: 'easeInOut' }}
                >
                  <h3>All Scored Candidates</h3>
                  {result.results.length === 0 ? (
                    <div className="result-card result-card-empty">
                      <h4>No successful resume analyses</h4>
                      <p className="result-muted">Try uploading valid PDF or DOCX resumes.</p>
                    </div>
                  ) : (
                    <div className="results-list-grid">
                      {result.results.map((candidate, index) => (
                        <div className="result-card compact" key={`${candidate.details.candidate_name ?? 'candidate'}-${index}`}>
                          <div className="result-card-top">
                        <div>
                          <p className="result-label">Candidate {index + 1}</p>
                          <h4>{candidate.details.candidate_name || 'Unnamed Candidate'}</h4>
                          <p className="compact-email">
                            <span>Email:</span> {candidate.details.email || 'No email extracted'}
                          </p>
                        </div>
                            <div className="score-pill">{candidate.score.toFixed(1)}%</div>
                          </div>
                          <p className="verdict">{candidate.details.verdict}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </section>
      )}
    </div>
  );
}

export default App;
