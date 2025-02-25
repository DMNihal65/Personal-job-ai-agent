import React from 'react';
import LoadingIndicator from './LoadingIndicator';
import ErrorMessage from './ErrorMessage';

const SkillMatch = ({ onMatch, isLoading, error, jobData, resumeData }) => {
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

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Match Your Skills</h2>
      <p className="mb-6 text-gray-600">Compare your resume with the job requirements</p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {resumeData && (
          <div className="p-4 bg-blue-50 rounded-md border border-blue-100">
            <h3 className="font-semibold text-blue-800 mb-3">Your Profile</h3>
            
            <div className="mb-3">
              <p className="text-sm text-gray-600">Name:</p>
              <p className="font-medium">{resumeData.personal_info?.name || 'N/A'}</p>
            </div>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600 font-medium">Your Skills:</p>
              {renderSkills(resumeData.skills?.technical)}
            </div>
            
            {resumeData.experience && resumeData.experience.length > 0 && (
              <div className="mb-3">
                <p className="text-sm text-gray-600 font-medium">Latest Experience:</p>
                <p className="font-medium">{resumeData.experience[0].title || 'N/A'} at {resumeData.experience[0].company || 'N/A'}</p>
                <p className="text-sm text-gray-500">{resumeData.experience[0].duration || 'N/A'}</p>
              </div>
            )}
          </div>
        )}
        
        {jobData && (
          <div className="p-4 bg-green-50 rounded-md border border-green-100">
            <h3 className="font-semibold text-green-800 mb-3">Job Details</h3>
            
            <div className="mb-3">
              <p className="text-sm text-gray-600">Company:</p>
              <p className="font-medium">{jobData.company_name || 'N/A'}</p>
            </div>
            
            <div className="mb-3">
              <p className="text-sm text-gray-600">Position:</p>
              <p className="font-medium">{jobData.job_title || 'N/A'}</p>
            </div>
            
            {jobData.job_location && (
              <div className="mb-3">
                <p className="text-sm text-gray-600">Location:</p>
                <p className="font-medium">{jobData.job_location}</p>
              </div>
            )}
            
            <div className="mb-4">
              <p className="text-sm text-gray-600 font-medium">Required Skills:</p>
              {renderSkills(jobData.technical_skills)}
            </div>
          </div>
        )}
      </div>
      
      <div className="text-center mb-6">
        <button
          className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={onMatch}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Analyzing Match...
            </>
          ) : (
            <>
              <svg className="mr-2 h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13a1 1 0 102 0V9.414l1.293 1.293a1 1 0 001.414-1.414z" clipRule="evenodd" />
              </svg>
              Match My Skills
            </>
          )}
        </button>
      </div>
      
      {isLoading && <LoadingIndicator message="Analyzing your skills match..." />}
      <ErrorMessage message={error} />
      
      <div className="bg-yellow-50 border border-yellow-100 rounded-md p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1V9a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800">What happens next?</h3>
            <div className="mt-2 text-sm text-yellow-700">
              <p>
                We'll analyze your resume against the job requirements to:
              </p>
              <ul className="list-disc pl-5 mt-1 space-y-1">
                <li>Identify matching skills</li>
                <li>Highlight missing skills</li>
                <li>Calculate your overall match percentage</li>
                <li>Suggest interview questions</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SkillMatch; 