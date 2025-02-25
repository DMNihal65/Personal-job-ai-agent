# Job Application Assistant

An AI-powered tool to help job seekers prepare for applications and interviews by analyzing job descriptions and resumes, then providing tailored answers to common interview questions.

## Project Overview

The Job Application Assistant is a full-stack application that helps job seekers optimize their application process by:

- Analyzing resumes and extracting key information
- Scraping and analyzing job descriptions
- Matching skills between resumes and job requirements
- Generating personalized answers to interview questions
- Providing application strategies and resume enhancement suggestions

The application consists of two main components:
- **Backend**: A FastAPI-based API that handles resume parsing, job description scraping, and AI-powered analysis
- **Frontend**: A React-based web interface that provides a user-friendly way to interact with the backend services

## Features

- **Comprehensive Resume Analysis**: Upload your resume (PDF) and get a detailed analysis of your skills, experience, qualifications, and ATS optimization score
- **In-depth Job Description Analysis**: Enter a job posting URL to extract and analyze the job requirements, company information, and role details
- **Advanced Skill Matching**: Get a detailed comparison between your resume and the job requirements with match percentage and specific insights
- **ATS Optimization**: Identify important keywords and skills required for the job and how to optimize your application
- **Personalized Interview Preparation**: Get tailored answers to common interview questions based on your resume and the job description
- **Application Strategy**: Receive suggestions for cover letter focus points, skills to emphasize, and experiences to highlight
- **Resume Enhancement**: Get specific suggestions to improve your resume for the target job

## Tech Stack

### Backend
- Python 3.8+
- FastAPI
- Google Gemini AI
- Selenium for web scraping
- PyPDF2 for PDF parsing
- LangChain for AI orchestration

### Frontend
- React 19
- Vite
- TailwindCSS
- Modern JavaScript (ES6+)

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+ and npm
- Chrome browser (for web scraping)
- Google Gemini API key

### Backend Setup

1. Navigate to the Backend directory:
```bash
cd Backend
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Set your Google Gemini API key:
   - Open `job_application_agent.py`
   - Find the line with `GOOGLE_API_KEY = "your-api-key-here"`
   - Replace `"your-api-key-here"` with your actual Google Gemini API key

5. Run the backend server:
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`. You can access the API documentation at `http://localhost:8000/docs`.

### Frontend Setup

1. Navigate to the Frontend/job_assistant directory:
```bash
cd Frontend/job_assistant
```

2. Install the required dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend application will be available at `http://localhost:5173`.

## Usage

1. **Start both the backend and frontend servers** as described in the setup instructions
2. **Open your browser** and navigate to `http://localhost:5173`
3. **Upload your resume**: Click on the upload button and select your resume PDF file
4. **Enter job posting URL**: Provide the URL of the job posting you're interested in
5. **Review skill match analysis**: See how well your skills match the job requirements
6. **Ask questions**: Type interview questions or select from suggested questions to get personalized answers

## API Endpoints

The backend provides the following API endpoints:

- `POST /resume`: Upload and analyze a resume
- `GET /resume/{session_id}`: Retrieve resume analysis results
- `POST /job`: Submit a job URL for analysis
- `GET /job/{session_id}`: Retrieve job analysis results
- `POST /match`: Match resume skills with job requirements
- `GET /match/{session_id}`: Retrieve skill matching results
- `POST /question`: Submit a question for AI-generated answer
- `GET /questions/{session_id}`: Get suggested questions based on resume and job
- `DELETE /session/{session_id}`: Delete a session and its associated data
- `POST /save_personal_resume`: Save resume data for future use
- `GET /personal_resume`: Retrieve saved resume data

## Example Questions

- "Why am I suitable for this role?"
- "Why do I want to join this company?"
- "How do my skills align with the company's goals?"
- "What relevant experience do I have for this position?"
- "What makes me stand out from other candidates?"
- "How would I handle [specific challenge mentioned in job description]?"
- "What is my approach to [specific responsibility in the role]?"

## How It Works

1. **Resume Analysis**: The application uses Google's Gemini Pro model to extract and analyze information from your resume, including personal details, skills, experience, education, and more.
2. **Job Description Analysis**: The application scrapes the job posting URL and uses Gemini Pro to analyze the job requirements, company information, and role details.
3. **Skill Matching**: The application compares your resume with the job description to identify matching skills, missing skills, and transferable skills.
4. **Question Answering**: When you ask a question, the application uses the resume and job analysis to generate a personalized, human-like response.

## Testing

Run the backend test suite to verify the application works correctly:

```bash
cd Backend
python test_job_application_agent.py
python test_api.py
```

## Notes

- The application uses Google's Gemini Pro model for analysis and question answering
- All processing is done locally on your machine
- Your resume and job information are not stored permanently unless you explicitly save them
- The quality of the analysis depends on the clarity and completeness of your resume and the job description

## License

This project is licensed under the MIT License - see the LICENSE file for details. 