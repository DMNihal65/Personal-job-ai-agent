import os
import io
import json
import logging
import tempfile
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
import uvicorn
import uuid
import time

# Import our job application agent
from job_application_agent import JobApplicationAgent, EnhancedJobScraper, ResumeParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Job Application Assistant API",
    description="API for analyzing job descriptions and resumes, and providing tailored responses to job application queries",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Get API key from environment variable or use default for development
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyCkb4a_yq_Iviefm_FJHQr40ukm7BqlLww")

# Store active job application agents
active_sessions = {}

# Path for storing personal resume data
PERSONAL_RESUME_PATH = "personal_resume_data.json"

# Function to save personal resume data
def save_personal_resume_data(resume_data: dict):
    try:
        with open(PERSONAL_RESUME_PATH, 'w') as f:
            json.dump(resume_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving personal resume data: {e}")
        return False

# Function to load personal resume data
def load_personal_resume_data():
    try:
        if os.path.exists(PERSONAL_RESUME_PATH):
            with open(PERSONAL_RESUME_PATH, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"Error loading personal resume data: {e}")
        return None

# Pydantic models for request/response validation
class JobUrlRequest(BaseModel):
    url: HttpUrl
    session_id: Optional[str] = None

class ResumeAnalysisResponse(BaseModel):
    session_id: str
    personal_info: Dict
    skills: Dict
    experience: List
    education: List
    summary: Optional[str] = None
    professional_snapshot: Optional[str] = None
    technical_expertise_summary: Optional[str] = None
    ats_score: Optional[Dict] = None

class JobAnalysisResponse(BaseModel):
    session_id: str
    company_name: str
    job_title: str
    job_location: Optional[str] = None
    technical_skills: List[str]
    soft_skills: List[str]
    required_experience: Optional[str] = None
    education_requirements: List[str]
    responsibilities: List[str]
    executive_summary: Optional[str] = None
    key_qualifications_summary: Optional[str] = None
    application_advice: Optional[str] = None

class SkillMatchRequest(BaseModel):
    session_id: str

class SkillMatchResponse(BaseModel):
    session_id: str
    overall_match: Dict
    skill_match: Dict
    experience_match: Optional[Dict] = None
    education_match: Optional[Dict] = None
    strengths_for_role: Optional[List] = None
    improvement_areas: Optional[List] = None
    application_strategy: Optional[Dict] = None
    summary: str

class QuestionRequest(BaseModel):
    session_id: str
    question: str

class QuestionResponse(BaseModel):
    session_id: str
    question: str
    answer: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

class SavePersonalResumeRequest(BaseModel):
    session_id: str

# Helper function to generate a unique session ID
def generate_session_id() -> str:
    return str(uuid.uuid4())

# Helper function to get agent by session ID
def get_agent(session_id: str) -> JobApplicationAgent:
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return active_sessions[session_id]

# Endpoint to process a resume
@app.post("/resume", response_model=ResumeAnalysisResponse)
async def process_resume(
    background_tasks: BackgroundTasks,
    resume_file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    try:
        # Generate a new session ID if not provided
        if not session_id:
            session_id = generate_session_id()
        
        # Create a new agent if session doesn't exist
        if session_id not in active_sessions:
            active_sessions[session_id] = JobApplicationAgent(GEMINI_API_KEY)
        
        agent = active_sessions[session_id]
        
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(await resume_file.read())
            temp_file_path = temp_file.name
        
        # Process the resume in the background
        def process_resume_task():
            try:
                with open(temp_file_path, 'rb') as f:
                    agent.process_resume(f)
                # Clean up the temporary file
                os.unlink(temp_file_path)
            except Exception as e:
                logger.error(f"Error processing resume: {str(e)}")
        
        # Start background processing
        background_tasks.add_task(process_resume_task)
        
        # Return initial response while processing continues in background
        return {
            "session_id": session_id,
            "personal_info": {"name": "Processing...", "email": "", "phone": "", "location": ""},
            "skills": {"technical": ["Processing..."], "soft": [], "languages": [], "tools": []},
            "experience": [{"title": "Processing...", "company": "", "duration": "", "description": ""}],
            "education": [{"degree": "Processing...", "institution": "", "year": ""}],
            "summary": "Your resume is being processed. Please check back in a few moments."
        }
    
    except Exception as e:
        logger.error(f"Error in process_resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to get resume analysis results
@app.get("/resume/{session_id}", response_model=ResumeAnalysisResponse)
async def get_resume_analysis(session_id: str):
    try:
        agent = get_agent(session_id)
        
        if not agent.resume_analysis:
            return JSONResponse(
                status_code=202,
                content={"session_id": session_id, "message": "Resume is still being processed"}
            )
        
        # Return the resume analysis
        return {
            "session_id": session_id,
            "personal_info": agent.resume_analysis.get("personal_info", {}),
            "skills": agent.resume_analysis.get("skills", {}),
            "experience": agent.resume_analysis.get("experience", []),
            "education": agent.resume_analysis.get("education", []),
            "summary": agent.resume_analysis.get("summary", ""),
            "professional_snapshot": agent.resume_analysis.get("professional_snapshot", ""),
            "technical_expertise_summary": agent.resume_analysis.get("technical_expertise_summary", ""),
            "ats_score": agent.resume_analysis.get("ats_score", {})
        }
    
    except Exception as e:
        logger.error(f"Error in get_resume_analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to process a job URL
@app.post("/job", response_model=JobAnalysisResponse)
async def process_job(background_tasks: BackgroundTasks, job_request: JobUrlRequest):
    try:
        # Generate a new session ID if not provided
        session_id = job_request.session_id or generate_session_id()
        
        # Create a new agent if session doesn't exist
        if session_id not in active_sessions:
            active_sessions[session_id] = JobApplicationAgent(GEMINI_API_KEY)
        
        agent = active_sessions[session_id]
        
        # Process the job URL in the background
        def process_job_task():
            try:
                agent.process_job_url(str(job_request.url))
            except Exception as e:
                logger.error(f"Error processing job URL: {str(e)}")
        
        # Start background processing
        background_tasks.add_task(process_job_task)
        
        # Return initial response while processing continues in background
        return {
            "session_id": session_id,
            "company_name": "Processing...",
            "job_title": "Processing...",
            "technical_skills": ["Processing..."],
            "soft_skills": [],
            "education_requirements": [],
            "responsibilities": [],
            "executive_summary": "Your job posting is being processed. Please check back in a few moments."
        }
    
    except Exception as e:
        logger.error(f"Error in process_job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to get job analysis results
@app.get("/job/{session_id}", response_model=JobAnalysisResponse)
async def get_job_analysis(session_id: str):
    try:
        agent = get_agent(session_id)
        
        if not agent.job_analysis:
            return JSONResponse(
                status_code=202,
                content={"session_id": session_id, "message": "Job is still being processed"}
            )
        
        # Return the job analysis
        return {
            "session_id": session_id,
            "company_name": agent.job_analysis.get("company_name", ""),
            "job_title": agent.job_analysis.get("job_title", ""),
            "job_location": agent.job_analysis.get("job_location", ""),
            "technical_skills": agent.job_analysis.get("technical_skills", []),
            "soft_skills": agent.job_analysis.get("soft_skills", []),
            "required_experience": agent.job_analysis.get("required_experience", ""),
            "education_requirements": agent.job_analysis.get("education_requirements", []),
            "responsibilities": agent.job_analysis.get("responsibilities", []),
            "executive_summary": agent.job_analysis.get("executive_summary", ""),
            "key_qualifications_summary": agent.job_analysis.get("key_qualifications_summary", ""),
            "application_advice": agent.job_analysis.get("application_advice", "")
        }
    
    except Exception as e:
        logger.error(f"Error in get_job_analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to perform skill matching
@app.post("/match", response_model=SkillMatchResponse)
async def match_skills(background_tasks: BackgroundTasks, match_request: SkillMatchRequest):
    try:
        agent = get_agent(match_request.session_id)
        
        # Check if both resume and job have been processed
        if not agent.resume_analysis:
            raise HTTPException(status_code=400, detail="Resume must be processed before matching skills")
        
        if not agent.job_analysis:
            raise HTTPException(status_code=400, detail="Job must be processed before matching skills")
        
        # Perform skill matching in the background
        def match_skills_task():
            try:
                if not agent.skill_match_analysis:
                    agent.match_skills_with_job()
            except Exception as e:
                logger.error(f"Error matching skills: {str(e)}")
        
        # Start background processing
        background_tasks.add_task(match_skills_task)
        
        # Return initial response while processing continues in background
        return {
            "session_id": match_request.session_id,
            "overall_match": {"percentage": 0, "assessment": "Processing...", "recommendation": ""},
            "skill_match": {"matching_skills": [], "missing_skills": []},
            "summary": "Skill matching is being processed. Please check back in a few moments."
        }
    
    except Exception as e:
        logger.error(f"Error in match_skills: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to get skill match results
@app.get("/match/{session_id}", response_model=SkillMatchResponse)
async def get_skill_match(session_id: str):
    try:
        agent = get_agent(session_id)
        
        if not agent.skill_match_analysis:
            return JSONResponse(
                status_code=202,
                content={"session_id": session_id, "message": "Skill matching is still being processed"}
            )
        
        # Get the skill match summary
        summary = agent.get_skill_match_summary()
        
        # Return the skill match analysis
        return {
            "session_id": session_id,
            "overall_match": agent.skill_match_analysis.get("overall_match", {}),
            "skill_match": agent.skill_match_analysis.get("skill_match", {}),
            "experience_match": agent.skill_match_analysis.get("experience_match", {}),
            "education_match": agent.skill_match_analysis.get("education_match", {}),
            "strengths_for_role": agent.skill_match_analysis.get("strengths_for_role", []),
            "improvement_areas": agent.skill_match_analysis.get("improvement_areas", []),
            "application_strategy": agent.skill_match_analysis.get("application_strategy", {}),
            "summary": summary
        }
    
    except Exception as e:
        logger.error(f"Error in get_skill_match: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to answer a question
@app.post("/question", response_model=QuestionResponse)
async def answer_question(question_request: QuestionRequest):
    try:
        agent = get_agent(question_request.session_id)
        
        # Check if both resume and job have been processed
        if not agent.resume_analysis:
            raise HTTPException(status_code=400, detail="Resume must be processed before answering questions")
        
        if not agent.job_analysis:
            raise HTTPException(status_code=400, detail="Job must be processed before answering questions")
        
        # Answer the question
        answer = agent.answer_question(question_request.question)
        
        # Return the answer
        return {
            "session_id": question_request.session_id,
            "question": question_request.question,
            "answer": answer
        }
    
    except Exception as e:
        logger.error(f"Error in answer_question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to get suggested questions
@app.get("/questions/{session_id}")
async def get_suggested_questions(session_id: str):
    try:
        agent = get_agent(session_id)
        
        # Check if skill matching has been performed
        if not agent.skill_match_analysis:
            if agent.resume_analysis and agent.job_analysis:
                # Perform skill matching if not done yet
                agent.match_skills_with_job()
            else:
                raise HTTPException(status_code=400, detail="Resume and job must be processed before getting suggested questions")
        
        # Get potential questions from the skill match analysis
        potential_questions = []
        if agent.skill_match_analysis.get('application_strategy', {}).get('potential_questions'):
            potential_questions = [q.get('question') for q in agent.skill_match_analysis['application_strategy']['potential_questions'] if q.get('question')]
        
        # If no potential questions found, use default questions
        if not potential_questions:
            job_title = agent.job_analysis.get("job_title", "this role")
            company_name = agent.job_analysis.get("company_name", "this company")
            
            potential_questions = [
                f"Why am I suitable for the {job_title} position?",
                f"Why do I want to join {company_name}?",
                f"How do my skills align with {company_name}'s goals?",
                f"What relevant experience do I have for the {job_title} position?",
                f"What makes me stand out from other candidates for this {job_title} role?"
            ]
        
        # Return the suggested questions
        return {
            "session_id": session_id,
            "questions": potential_questions[:10]
        }
    
    except Exception as e:
        logger.error(f"Error in get_suggested_questions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to clean up a session
@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    try:
        if session_id in active_sessions:
            del active_sessions[session_id]
            return {"message": f"Session {session_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    except Exception as e:
        logger.error(f"Error in delete_session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint for API health check
@app.get("/")
async def root():
    return {
        "status": "online",
        "api_version": "1.0.0",
        "message": "Job Application Assistant API is running"
    }

@app.post("/save_personal_resume")
async def save_personal_resume(request: SavePersonalResumeRequest):
    """Save the processed resume data as personal data for quick access"""
    session_id = request.session_id
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    agent = active_sessions[session_id]
    if not agent.resume_analysis:
        raise HTTPException(status_code=400, detail="Resume not processed yet")
    
    # Use resume_analysis directly instead of get_resume_data method
    resume_data = agent.resume_analysis
    if not resume_data:
        raise HTTPException(status_code=400, detail="No resume data available")
    
    # Add session_id to the resume data
    resume_data["session_id"] = session_id
    
    # Save the resume data to file
    if save_personal_resume_data(resume_data):
        return {"status": "success", "message": "Personal resume data saved successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save personal resume data")

@app.get("/personal_resume")
async def get_personal_resume():
    """Get the saved personal resume data"""
    resume_data = load_personal_resume_data()
    if not resume_data:
        raise HTTPException(status_code=404, detail="No personal resume data found")
    
    # Create a new session with a new ID
    new_session_id = str(uuid.uuid4())
    active_sessions[new_session_id] = JobApplicationAgent(GEMINI_API_KEY)
    
    # Update the agent with the resume data
    agent = active_sessions[new_session_id]
    agent.resume_analysis = resume_data
    
    # Update the session_id in the response
    resume_data["session_id"] = new_session_id
    
    return resume_data

# Run the FastAPI app with uvicorn
if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 