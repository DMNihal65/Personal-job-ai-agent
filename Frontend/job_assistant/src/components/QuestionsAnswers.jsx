import React, { useState, useEffect, useRef } from 'react';
import LoadingIndicator from './LoadingIndicator';
import ErrorMessage from './ErrorMessage';

const QuestionsAnswers = ({ 
  onQuestionSubmit, 
  isLoading, 
  error, 
  matchData, 
  suggestedQuestions, 
  questionAnswer 
}) => {
  const [question, setQuestion] = useState('');
  const [activeQuestion, setActiveQuestion] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const chatEndRef = useRef(null);
  
  // Scroll to bottom of chat when new messages are added
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatHistory]);
  
  // Update chat history when a new answer is received
  useEffect(() => {
    if (questionAnswer && activeQuestion) {
      // Check if this question-answer pair is already in the history
      const exists = chatHistory.some(item => 
        item.question === activeQuestion && item.answer === questionAnswer.answer
      );
      
      if (!exists) {
        setChatHistory(prev => [...prev, {
          question: activeQuestion,
          answer: questionAnswer.answer,
          timestamp: new Date().toISOString()
        }]);
      }
    }
  }, [questionAnswer, activeQuestion]);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (question.trim()) {
      setActiveQuestion(question);
      onQuestionSubmit(question);
    }
  };
  
  const handleSuggestedQuestion = (q) => {
    setQuestion(q);
    setActiveQuestion(q);
    onQuestionSubmit(q);
  };
  
  const handleClearChat = () => {
    setChatHistory([]);
    setActiveQuestion(null);
    setQuestion('');
  };
  
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Interview Questions</h2>
      
      {matchData && (
        <div className="mb-6 p-5 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-100">
          <h3 className="font-semibold text-lg text-blue-800 mb-3">Match Results</h3>
          
          <div className="mb-4">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-gray-700">Overall Match</span>
              <span className="text-sm font-medium text-gray-700">{matchData.overall_match?.percentage || 'N/A'}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className={`h-2.5 rounded-full ${
                  (matchData.overall_match?.percentage || 0) >= 80 ? 'bg-green-600' :
                  (matchData.overall_match?.percentage || 0) >= 60 ? 'bg-blue-600' :
                  (matchData.overall_match?.percentage || 0) >= 40 ? 'bg-yellow-500' : 'bg-red-600'
                }`}
                style={{ width: `${matchData.overall_match?.percentage || 0}%` }}
              ></div>
            </div>
          </div>
          
          <p className="text-sm mb-4">{matchData.overall_match?.assessment || ''}</p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white p-3 rounded-md shadow-sm">
              <h4 className="font-medium text-green-700 mb-2 flex items-center">
                <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Matching Skills
              </h4>
              <ul className="space-y-1">
                {Array.isArray(matchData.skill_match?.matching_skills) 
                  ? matchData.skill_match.matching_skills.slice(0, 5).map((skill, index) => (
                      <li key={index} className="text-sm flex items-start">
                        <span className="inline-block w-2 h-2 rounded-full bg-green-500 mt-1.5 mr-2"></span>
                        {typeof skill === 'string' ? skill : skill.skill || JSON.stringify(skill)}
                      </li>
                    ))
                  : <li className="text-sm text-gray-500">No matching skills found</li>
                }
              </ul>
            </div>
            
            <div className="bg-white p-3 rounded-md shadow-sm">
              <h4 className="font-medium text-yellow-700 mb-2 flex items-center">
                <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                </svg>
                Missing Skills
              </h4>
              <ul className="space-y-1">
                {Array.isArray(matchData.skill_match?.missing_skills)
                  ? matchData.skill_match.missing_skills.slice(0, 5).map((skill, index) => (
                      <li key={index} className="text-sm flex items-start">
                        <span className="inline-block w-2 h-2 rounded-full bg-yellow-500 mt-1.5 mr-2"></span>
                        {typeof skill === 'string' ? skill : skill.skill || JSON.stringify(skill)}
                      </li>
                    ))
                  : <li className="text-sm text-gray-500">No missing skills found</li>
                }
              </ul>
            </div>
          </div>
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1">
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 h-full">
            <h3 className="font-semibold text-gray-800 mb-3 flex items-center">
              <svg className="w-5 h-5 mr-2 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
              </svg>
              Suggested Questions
            </h3>
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {suggestedQuestions.length > 0 ? (
                suggestedQuestions.map((q, index) => (
                  <button
                    key={index}
                    className={`block w-full text-left p-3 rounded-md transition-colors text-sm ${
                      activeQuestion === q 
                        ? 'bg-blue-100 text-blue-800 border border-blue-200' 
                        : 'bg-white hover:bg-gray-100 border border-gray-200'
                    }`}
                    onClick={() => handleSuggestedQuestion(q)}
                    disabled={isLoading}
                  >
                    <div className="flex items-start">
                      <span className="inline-flex items-center justify-center flex-shrink-0 w-5 h-5 mr-2 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                        {index + 1}
                      </span>
                      <span>{q}</span>
                    </div>
                  </button>
                ))
              ) : (
                <div className="text-center p-4 bg-white rounded-md">
                  <p className="text-gray-500 text-sm">No suggested questions available</p>
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className="md:col-span-2">
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 mb-4">
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-semibold text-gray-800 flex items-center">
                <svg className="w-5 h-5 mr-2 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zM7 8H5v2h2V8zm2 0h2v2H9V8zm6 0h-2v2h2V8z" clipRule="evenodd" />
                </svg>
                Chat History
              </h3>
              {chatHistory.length > 0 && (
                <button 
                  className="text-xs text-gray-500 hover:text-gray-700 flex items-center"
                  onClick={handleClearChat}
                >
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Clear Chat
                </button>
              )}
            </div>
            
            <div className="bg-white rounded-lg border border-gray-200 p-3 h-[300px] overflow-y-auto mb-3">
              {chatHistory.length > 0 ? (
                <div className="space-y-4">
                  {chatHistory.map((chat, index) => (
                    <div key={index}>
                      <div className="flex justify-end mb-2">
                        <div className="bg-blue-100 text-blue-800 rounded-lg py-2 px-3 max-w-[80%]">
                          <div className="flex justify-between items-start">
                            <p className="text-sm">{chat.question}</p>
                            <span className="text-xs text-blue-600 ml-2 whitespace-nowrap">
                              {formatTimestamp(chat.timestamp)}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex mb-2">
                        <div className="bg-gray-100 rounded-lg py-2 px-3 max-w-[80%]">
                          <p className="text-sm whitespace-pre-line">{chat.answer}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                  <div ref={chatEndRef} />
                </div>
              ) : (
                <div className="h-full flex items-center justify-center">
                  <p className="text-gray-400 text-sm">No chat history yet. Ask a question to get started.</p>
                </div>
              )}
            </div>
            
            <form onSubmit={handleSubmit}>
              <div className="flex">
                <textarea
                  className="flex-grow p-3 border border-gray-300 rounded-l-md focus:ring-blue-500 focus:border-blue-500 resize-none"
                  rows="2"
                  placeholder="Type your question here..."
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  disabled={isLoading}
                ></textarea>
                <button
                  type="submit"
                  className="px-4 bg-blue-600 text-white rounded-r-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                  disabled={isLoading || !question.trim()}
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </form>
          </div>
          
          {isLoading && <LoadingIndicator message="Generating answer..." />}
          <ErrorMessage message={error} />
          
          {questionAnswer && activeQuestion && !chatHistory.some(chat => chat.question === activeQuestion) && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-md">
              <div className="flex items-start mb-3">
                <div className="flex-shrink-0 bg-green-100 rounded-full p-1">
                  <svg className="h-5 w-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1V9a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <h3 className="ml-2 text-lg font-medium text-green-800">Latest Answer</h3>
              </div>
              
              <div className="bg-white p-4 rounded-md shadow-sm">
                <p className="text-gray-800 whitespace-pre-line">{questionAnswer.answer}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default QuestionsAnswers; 