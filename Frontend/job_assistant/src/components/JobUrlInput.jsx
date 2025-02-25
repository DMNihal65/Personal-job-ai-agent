import React, { useState } from 'react';
import LoadingIndicator from './LoadingIndicator';
import ErrorMessage from './ErrorMessage';

const JobUrlInput = ({ onSubmit, isLoading, error, resumeData, jobData }) => {
  const [jobUrl, setJobUrl] = useState('');
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (jobUrl.trim()) {
      onSubmit(jobUrl);
    }
  };

  // Function to render skills with proper handling of null/undefined values
  const renderSkills = (skills) => {
    if (!skills || !Array.isArray(skills) || skills.length === 0) {
      return <span className="text-gray-500">No skills found</span>;
    }

    return (
      <div className="flex flex-wrap gap-1 mt-1">
        {skills.slice(0, 8).map((skill, index) => (
          <span key={index} className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
            {skill}
          </span>
        ))}
        {skills.length > 8 && (
          <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">
            +{skills.length - 8} more
          </span>
        )}
      </div>
    );
  };

  // Function to render list items with proper handling of null/undefined values
  const renderList = (items) => {
    if (!items || !Array.isArray(items) || items.length === 0) {
      return <span className="text-gray-500">None specified</span>;
    }

    return (
      <ul className="list-disc list-inside space-y-1">
        {items.map((item, index) => (
          <li key={index} className="text-sm">{item}</li>
        ))}
      </ul>
    );
  };
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Enter Job Posting URL</h2>
      <p className="mb-6 text-gray-600">Paste the URL of the job posting you're interested in</p>
      
      {resumeData && (
        <div className="mb-6 p-4 bg-blue-50 rounded-md border border-blue-100">
          <h3 className="font-semibold text-blue-800 mb-2">Resume Processed Successfully</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div>
              <p className="text-sm text-gray-600">Name:</p>
              <p className="font-medium">{resumeData.personal_info?.name || 'N/A'}</p>
            </div>
            {resumeData.personal_info?.email && (
              <div>
                <p className="text-sm text-gray-600">Email:</p>
                <p className="font-medium">{resumeData.personal_info.email}</p>
              </div>
            )}
          </div>
          
          <div className="mt-3">
            <p className="text-sm text-gray-600">Skills:</p>
            {renderSkills(resumeData.skills?.technical)}
          </div>
        </div>
      )}

      {jobData ? (
        <div className="mb-6 p-4 bg-green-50 rounded-md border border-green-100">
          <h3 className="font-semibold text-green-800 mb-3">Job Posting Processed</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
            <div>
              <p className="text-sm text-gray-600">Company:</p>
              <p className="font-medium">{jobData.company_name || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Position:</p>
              <p className="font-medium">{jobData.job_title || 'N/A'}</p>
            </div>
            {jobData.job_location && (
              <div>
                <p className="text-sm text-gray-600">Location:</p>
                <p className="font-medium">{jobData.job_location}</p>
              </div>
            )}
            {jobData.required_experience && (
              <div>
                <p className="text-sm text-gray-600">Experience Required:</p>
                <p className="font-medium">{jobData.required_experience}</p>
              </div>
            )}
          </div>
          
          <div className="mb-4">
            <p className="text-sm text-gray-600 font-medium">Technical Skills Required:</p>
            {renderSkills(jobData.technical_skills)}
          </div>
          
          <div className="mb-4">
            <p className="text-sm text-gray-600 font-medium">Soft Skills Required:</p>
            {renderSkills(jobData.soft_skills)}
          </div>
          
          {jobData.education_requirements && jobData.education_requirements.length > 0 && (
            <div className="mb-4">
              <p className="text-sm text-gray-600 font-medium">Education Requirements:</p>
              {renderList(jobData.education_requirements)}
            </div>
          )}
          
          {jobData.responsibilities && jobData.responsibilities.length > 0 && (
            <div className="mb-4">
              <p className="text-sm text-gray-600 font-medium">Key Responsibilities:</p>
              {renderList(jobData.responsibilities)}
            </div>
          )}
          
          {jobData.executive_summary && (
            <div className="mt-4 pt-3 border-t border-green-200">
              <p className="text-sm text-gray-600 font-medium">Job Summary:</p>
              <p className="text-sm">{jobData.executive_summary}</p>
            </div>
          )}
          
          {jobData.application_advice && (
            <div className="mt-4 pt-3 border-t border-green-200">
              <p className="text-sm text-gray-600 font-medium">Application Advice:</p>
              <p className="text-sm">{jobData.application_advice}</p>
            </div>
          )}
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="job-url" className="block text-sm font-medium text-gray-700 mb-1">
              Job URL
            </label>
            <div className="mt-1 relative rounded-md shadow-sm">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
                </svg>
              </div>
              <input
                type="url"
                id="job-url"
                className="focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 pr-12 py-3 sm:text-sm border-gray-300 rounded-md"
                placeholder="https://example.com/job-posting"
                value={jobUrl}
                onChange={(e) => setJobUrl(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <p className="mt-1 text-xs text-gray-500">
              Enter the full URL of the job posting (e.g., LinkedIn, Indeed, company website)
            </p>
          </div>
          
          <button
            type="submit"
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isLoading || !jobUrl.trim()}
          >
            {isLoading ? 'Processing...' : 'Analyze Job Posting'}
          </button>
        </form>
      )}
      
      {isLoading && <LoadingIndicator message="Processing job posting..." />}
      <ErrorMessage message={error} />
      
      {!jobData && (
        <div className="mt-6 text-sm text-gray-500">
          <p className="flex items-center">
            <svg className="w-4 h-4 mr-2 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1V9a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            We'll extract key requirements and skills from the job posting
          </p>
        </div>
      )}
    </div>
  );
};

export default JobUrlInput; 