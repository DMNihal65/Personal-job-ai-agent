import React from 'react';

const StepIndicator = ({ steps, currentStep }) => {
  return (
    <div className="mb-8">
      <div className="flex justify-center">
        <div className="flex items-center w-full max-w-3xl">
          {steps.map((step, index) => (
            <div key={step} className="flex items-center flex-1">
              <div className="flex flex-col items-center">
                <div 
                  className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors duration-300 ${
                    currentStep === step 
                      ? 'bg-blue-600 text-white shadow-lg' 
                      : index < steps.indexOf(currentStep)
                        ? 'bg-green-500 text-white'
                        : 'bg-gray-200 text-gray-600'
                  }`}
                >
                  {index + 1}
                </div>
                <div 
                  className={`text-sm mt-2 font-medium transition-colors duration-300 ${
                    currentStep === step 
                      ? 'text-blue-600' 
                      : index < steps.indexOf(currentStep)
                        ? 'text-green-500'
                        : 'text-gray-500'
                  }`}
                >
                  {step.charAt(0).toUpperCase() + step.slice(1)}
                </div>
              </div>
              
              {index < steps.length - 1 && (
                <div 
                  className={`flex-1 h-1 mx-2 transition-colors duration-300 ${
                    index < steps.indexOf(currentStep)
                      ? 'bg-green-500'
                      : 'bg-gray-200'
                  }`}
                ></div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default StepIndicator; 