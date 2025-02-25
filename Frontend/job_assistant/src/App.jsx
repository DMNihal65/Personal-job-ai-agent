import { useState, useEffect } from 'react'
import './App.css'
import ResumeUpload from './components/ResumeUpload'
import JobUrlInput from './components/JobUrlInput'
import SkillMatch from './components/SkillMatch'
import QuestionsAnswers from './components/QuestionsAnswers'
import StepIndicator from './components/StepIndicator'
import ErrorMessage from './components/ErrorMessage'
import LoadingIndicator from './components/LoadingIndicator'

function App() {
  // Main application states
  const [sessionId, setSessionId] = useState(null);
  const [currentStep, setCurrentStep] = useState('upload'); // upload, job, match, questions
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  
  // Data states
  const [resumeData, setResumeData] = useState(null);
  const [jobData, setJobData] = useState(null);
  const [matchData, setMatchData] = useState(null);
  const [suggestedQuestions, setSuggestedQuestions] = useState([]);
  const [questionAnswer, setQuestionAnswer] = useState(null);

  // API base URL
  const API_BASE_URL = 'http://localhost:8000';

  // Function to handle resume upload
  const handleResumeUpload = async (file) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('resume_file', file);
      if (sessionId) {
        formData.append('session_id', sessionId);
      }
      
      const response = await fetch(`${API_BASE_URL}/resume`, {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setSessionId(data.session_id);
        // Poll for resume analysis completion
        setIsPolling(true);
        pollResumeAnalysis(data.session_id);
      } else {
        setError(data.detail || 'Failed to upload resume');
        setIsLoading(false);
      }
    } catch (err) {
      setError('Error uploading resume: ' + err.message);
      setIsLoading(false);
    }
  };

  // Function to poll for resume analysis completion
  const pollResumeAnalysis = async (sid) => {
    try {
      const response = await fetch(`${API_BASE_URL}/resume/${sid}`);
      const data = await response.json();
      
      if (response.status === 202) {
        // Still processing, poll again after 2 seconds
        setTimeout(() => pollResumeAnalysis(sid), 2000);
      } else if (response.ok) {
        setResumeData(data);
        setCurrentStep('job');
        setIsPolling(false);
        setIsLoading(false);
      } else {
        setError(data.detail || 'Failed to get resume analysis');
        setIsPolling(false);
        setIsLoading(false);
      }
    } catch (err) {
      setError('Error getting resume analysis: ' + err.message);
      setIsPolling(false);
      setIsLoading(false);
    }
  };

  // Function to handle job URL submission
  const handleJobSubmit = async (url) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/job`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url,
          session_id: sessionId,
        }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        // Poll for job analysis completion
        setIsPolling(true);
        pollJobAnalysis(sessionId);
      } else {
        setError(data.detail || 'Failed to submit job URL');
        setIsLoading(false);
      }
    } catch (err) {
      setError('Error submitting job URL: ' + err.message);
      setIsLoading(false);
    }
  };

  // Function to poll for job analysis completion
  const pollJobAnalysis = async (sid) => {
    try {
      const response = await fetch(`${API_BASE_URL}/job/${sid}`);
      const data = await response.json();
      
      if (response.status === 202) {
        // Still processing, poll again after 2 seconds
        setTimeout(() => pollJobAnalysis(sid), 2000);
      } else if (response.ok) {
        setJobData(data);
        setCurrentStep('match');
        setIsPolling(false);
        setIsLoading(false);
      } else {
        setError(data.detail || 'Failed to get job analysis');
        setIsPolling(false);
        setIsLoading(false);
      }
    } catch (err) {
      setError('Error getting job analysis: ' + err.message);
      setIsPolling(false);
      setIsLoading(false);
    }
  };

  // Function to handle skill matching
  const handleMatchSkills = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/match`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
        }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        // Poll for skill match completion
        setIsPolling(true);
        pollSkillMatch(sessionId);
      } else {
        setError(data.detail || 'Failed to match skills');
        setIsLoading(false);
      }
    } catch (err) {
      setError('Error matching skills: ' + err.message);
      setIsLoading(false);
    }
  };

  // Function to poll for skill match completion
  const pollSkillMatch = async (sid) => {
    try {
      const response = await fetch(`${API_BASE_URL}/match/${sid}`);
      const data = await response.json();
      
      if (response.status === 202) {
        // Still processing, poll again after 2 seconds
        setTimeout(() => pollSkillMatch(sid), 2000);
      } else if (response.ok) {
        setMatchData(data);
        // Get suggested questions
        getSuggestedQuestions(sid);
        setCurrentStep('questions');
        setIsPolling(false);
        setIsLoading(false);
      } else {
        setError(data.detail || 'Failed to get skill match');
        setIsPolling(false);
        setIsLoading(false);
      }
    } catch (err) {
      setError('Error getting skill match: ' + err.message);
      setIsPolling(false);
      setIsLoading(false);
    }
  };

  // Function to get suggested questions
  const getSuggestedQuestions = async (sid) => {
    try {
      const response = await fetch(`${API_BASE_URL}/questions/${sid}`);
      
      if (response.ok) {
        const data = await response.json();
        setSuggestedQuestions(data.questions || []);
      }
    } catch (err) {
      console.error('Error getting suggested questions:', err);
    }
  };

  // Function to handle question submission
  const handleQuestionSubmit = async (question) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/question`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          question: question,
        }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setQuestionAnswer(data);
      } else {
        setError(data.detail || 'Failed to get answer');
      }
    } catch (err) {
      setError('Error getting answer: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Function to reset the application
  const handleReset = async () => {
    if (sessionId) {
      try {
        await fetch(`${API_BASE_URL}/session/${sessionId}`, {
          method: 'DELETE',
        });
      } catch (err) {
        console.error('Error deleting session:', err);
      }
    }
    
    setSessionId(null);
    setCurrentStep('upload');
    setIsLoading(false);
    setIsPolling(false);
    setError(null);
    setResumeData(null);
    setJobData(null);
    setMatchData(null);
    setSuggestedQuestions([]);
    setQuestionAnswer(null);
  };

  // Function to handle using personal resume
  const handleUsePersonal = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/personal_resume`);
      
      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);
        setResumeData(data);
        setCurrentStep('job');
        console.log('Successfully loaded personal resume with session ID:', data.session_id);
      } else {
        let errorMessage = 'No personal resume found. Please upload a resume first.';
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            errorMessage = errorData.detail;
          }
        } catch (e) {
          // If we can't parse the error response, use the default message
        }
        setError(errorMessage);
      }
    } catch (err) {
      console.error('Error retrieving personal resume:', err);
      setError('Error retrieving personal resume: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Function to save current resume as personal
  const handleSavePersonal = async () => {
    if (!sessionId || !resumeData) {
      setError('No resume data to save');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/save_personal_resume`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          session_id: sessionId 
        }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        // Show success message
        alert('Resume saved as personal successfully! You can now use "Use Personal Resume" option in the future.');
      } else {
        console.error('Error saving personal resume:', data);
        setError(data.detail || 'Failed to save personal resume');
      }
    } catch (err) {
      console.error('Error saving personal resume:', err);
      setError('Error saving personal resume: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Steps for the application
  const steps = ['upload', 'job', 'match', 'questions'];

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      {isPolling && <LoadingIndicator fullScreen={true} message={
        currentStep === 'upload' ? 'Processing your resume...' :
        currentStep === 'job' ? 'Analyzing job posting...' :
        currentStep === 'match' ? 'Matching your skills...' : 'Loading...'
      } />}
      
      <div className="container mx-auto px-4">
        <header className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-blue-800">Job Application Assistant</h1>
          <p className="text-gray-600 mt-2">Your AI-powered job application helper</p>
        </header>
        
        <StepIndicator steps={steps} currentStep={currentStep} />
        
        <main className="max-w-3xl mx-auto">
          {currentStep === 'upload' && (
            <ResumeUpload 
              onUpload={handleResumeUpload} 
              onUsePersonal={handleUsePersonal}
              isLoading={isLoading && !isPolling} 
              error={error} 
              resumeData={resumeData}
            />
          )}
          
          {currentStep === 'job' && (
            <div>
              <JobUrlInput 
                onSubmit={handleJobSubmit} 
                isLoading={isLoading && !isPolling} 
                error={error} 
                resumeData={resumeData}
                jobData={jobData}
              />
              {resumeData && (
                <div className="mt-4 text-center">
                  <button
                    onClick={handleSavePersonal}
                    className="text-sm text-blue-600 hover:text-blue-800 underline"
                    disabled={isLoading}
                  >
                    Save as Personal Resume
                  </button>
                </div>
              )}
            </div>
          )}
          
          {currentStep === 'match' && (
            <SkillMatch 
              onMatch={handleMatchSkills} 
              isLoading={isLoading && !isPolling} 
              error={error} 
              jobData={jobData}
              resumeData={resumeData}
            />
          )}
          
          {currentStep === 'questions' && (
            <QuestionsAnswers 
              onQuestionSubmit={handleQuestionSubmit} 
              isLoading={isLoading} 
              error={error} 
              matchData={matchData} 
              suggestedQuestions={suggestedQuestions} 
              questionAnswer={questionAnswer} 
            />
          )}
          
          <div className="mt-6 flex justify-between">
            <button
              className="text-gray-600 hover:text-gray-800 flex items-center"
              onClick={handleReset}
              disabled={isLoading || isPolling}
            >
              <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
              </svg>
              Start Over
            </button>
            
            {currentStep !== 'upload' && (
              <button
                className="text-blue-600 hover:text-blue-800 flex items-center"
                onClick={() => {
                  const currentIndex = steps.indexOf(currentStep);
                  if (currentIndex > 0) {
                    setCurrentStep(steps[currentIndex - 1]);
                  }
                }}
                disabled={isLoading || isPolling}
              >
                <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M9.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L7.414 9H15a1 1 0 110 2H7.414l2.293 2.293a1 1 0 010 1.414z" clipRule="evenodd" />
                </svg>
                Back
              </button>
            )}
          </div>
        </main>
        
        <footer className="mt-12 text-center text-sm text-gray-500">
          <p>© {new Date().getFullYear()} Job Application Assistant. All rights reserved.</p>
        </footer>
      </div>
    </div>
  );
}

export default App
