import React, { useState } from 'react';
import LoadingIndicator from './LoadingIndicator';
import ErrorMessage from './ErrorMessage';

const ResumeUpload = ({ onUpload, isLoading, error, resumeData, onUsePersonal }) => {
  const [dragActive, setDragActive] = useState(false);
  
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };
  
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf') {
        onUpload(file);
      }
    }
  };
  
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onUpload(e.target.files[0]);
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
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-md transition-all">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Upload Your Resume</h2>
      <p className="mb-6 text-gray-600">Start by uploading your resume (PDF format only)</p>
      
      {resumeData ? (
        <div className="mb-6 p-4 bg-blue-50 rounded-md border border-blue-100">
          <h3 className="font-semibold text-blue-800 mb-2">Resume Processed Successfully</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
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
            {resumeData.personal_info?.location && (
              <div>
                <p className="text-sm text-gray-600">Location:</p>
                <p className="font-medium">{resumeData.personal_info.location}</p>
              </div>
            )}
            {resumeData.personal_info?.phone && (
              <div>
                <p className="text-sm text-gray-600">Phone:</p>
                <p className="font-medium">{resumeData.personal_info.phone}</p>
              </div>
            )}
          </div>
          
          <div className="mb-4">
            <p className="text-sm text-gray-600 font-medium">Technical Skills:</p>
            {renderSkills(resumeData.skills?.technical)}
          </div>
          
          {resumeData.experience && resumeData.experience.length > 0 && (
            <div className="mb-4">
              <p className="text-sm text-gray-600 font-medium">Latest Experience:</p>
              <p className="font-medium">{resumeData.experience[0].title || 'N/A'} at {resumeData.experience[0].company || 'N/A'}</p>
              <p className="text-sm text-gray-500">{resumeData.experience[0].duration || 'N/A'}</p>
            </div>
          )}
          
          {resumeData.education && resumeData.education.length > 0 && (
            <div className="mb-4">
              <p className="text-sm text-gray-600 font-medium">Education:</p>
              <p className="font-medium">{resumeData.education[0].degree || 'N/A'}</p>
              <p className="text-sm text-gray-500">{resumeData.education[0].institution || 'N/A'} ({resumeData.education[0].graduation_date || 'N/A'})</p>
            </div>
          )}
          
          {resumeData.professional_snapshot && (
            <div className="mt-4 pt-3 border-t border-blue-200">
              <p className="text-sm text-gray-600 font-medium">Professional Summary:</p>
              <p className="text-sm">{resumeData.professional_snapshot}</p>
            </div>
          )}
          
          {resumeData.ats_score && (
            <div className="mt-4 pt-3 border-t border-blue-200">
              <p className="text-sm text-gray-600 font-medium">ATS Score:</p>
              <div className="grid grid-cols-2 gap-2 mt-1">
                <div>
                  <p className="text-xs text-gray-500">Overall:</p>
                  <p className="text-sm font-medium">{resumeData.ats_score.overall || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Formatting:</p>
                  <p className="text-sm font-medium">{resumeData.ats_score.formatting || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Keyword Optimization:</p>
                  <p className="text-sm font-medium">{resumeData.ats_score.keyword_optimization || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Content Quality:</p>
                  <p className="text-sm font-medium">{resumeData.ats_score.content_quality || 'N/A'}</p>
                </div>
              </div>
            </div>
          )}
          
          <div className="mt-4 flex justify-end">
            <button 
              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
              onClick={() => window.location.reload()}
            >
              Upload Another Resume
            </button>
          </div>
        </div>
      ) : (
        <div>
          <div 
            className={`border-2 border-dashed rounded-lg p-8 mb-4 text-center transition-colors ${
              dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <svg className="w-12 h-12 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            
            <p className="mb-2 text-sm text-gray-500">
              <span className="font-semibold">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-gray-500">PDF only (MAX. 10MB)</p>
            
            <input
              type="file"
              accept=".pdf"
              className="hidden"
              id="resume-upload"
              onChange={handleFileChange}
              disabled={isLoading}
            />
            
            <label 
              htmlFor="resume-upload" 
              className="mt-4 inline-block px-6 py-2.5 bg-blue-600 text-white font-medium text-xs leading-tight uppercase rounded shadow-md hover:bg-blue-700 hover:shadow-lg focus:bg-blue-700 focus:shadow-lg focus:outline-none focus:ring-0 active:bg-blue-800 active:shadow-lg transition duration-150 ease-in-out cursor-pointer disabled:opacity-50"
            >
              Select PDF
            </label>
          </div>
          
          <div className="text-center">
            <p className="mb-2 text-sm text-gray-600">- OR -</p>
            <button
              onClick={onUsePersonal}
              disabled={isLoading}
              className="px-6 py-2.5 bg-green-600 text-white font-medium text-xs leading-tight uppercase rounded shadow-md hover:bg-green-700 hover:shadow-lg focus:bg-green-700 focus:shadow-lg focus:outline-none focus:ring-0 active:bg-green-800 active:shadow-lg transition duration-150 ease-in-out disabled:opacity-50"
            >
              Use Personal Resume
            </button>
            <p className="mt-2 text-xs text-gray-500">
              Use your previously saved resume information
            </p>
          </div>
        </div>
      )}
      
      {isLoading && <LoadingIndicator message="Processing your resume..." />}
      <ErrorMessage message={error} />
      
      {!resumeData && (
        <div className="mt-6 text-sm text-gray-500">
          <p className="flex items-center">
            <svg className="w-4 h-4 mr-2 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Your resume will be analyzed to extract skills and experience
          </p>
          <p className="flex items-center mt-2">
            <svg className="w-4 h-4 mr-2 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            We'll help you match your skills with job requirements
          </p>
        </div>
      )}
    </div>
  );
};

export default ResumeUpload; 