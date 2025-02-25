import requests
import json
import os
import time
from typing import Dict, Any

# API base URL - change if needed
BASE_URL = "http://localhost:8000"

def test_api_health():
    """Test the API health endpoint"""
    response = requests.get(f"{BASE_URL}/")
    print(f"API Health Check: {response.status_code}")
    print(response.json())
    return response.status_code == 200

def test_resume_upload(resume_path: str):
    """Test the resume upload endpoint"""
    if not os.path.exists(resume_path):
        print(f"Error: Resume file not found at {resume_path}")
        return None
    
    with open(resume_path, 'rb') as f:
        files = {'resume_file': f}
        response = requests.post(f"{BASE_URL}/resume", files=files)
    
    print(f"Resume Upload: {response.status_code}")
    if response.status_code == 200:
        session_id = response.json().get('session_id')
        print(f"Session ID: {session_id}")
        return session_id
    else:
        print(response.text)
        return None

def test_job_url_processing(session_id: str, job_url: str):
    """Test the job URL processing endpoint"""
    data = {
        "url": job_url,
        "session_id": session_id
    }
    
    response = requests.post(f"{BASE_URL}/job", json=data)
    
    print(f"Job URL Processing: {response.status_code}")
    if response.status_code == 200:
        return True
    else:
        print(response.text)
        return False

def test_skill_matching(session_id: str):
    """Test the skill matching endpoint"""
    data = {
        "session_id": session_id
    }
    
    response = requests.post(f"{BASE_URL}/match", json=data)
    
    print(f"Skill Matching Request: {response.status_code}")
    if response.status_code == 200:
        return True
    else:
        print(response.text)
        return False

def get_resume_analysis(session_id: str):
    """Get the resume analysis results"""
    response = requests.get(f"{BASE_URL}/resume/{session_id}")
    
    print(f"Resume Analysis: {response.status_code}")
    if response.status_code == 200:
        return response.json()
    else:
        print(response.text)
        return None

def get_job_analysis(session_id: str):
    """Get the job analysis results"""
    response = requests.get(f"{BASE_URL}/job/{session_id}")
    
    print(f"Job Analysis: {response.status_code}")
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 202:
        print("Job is still being processed...")
        return None
    else:
        print(response.text)
        return None

def get_skill_match(session_id: str):
    """Get the skill match results"""
    response = requests.get(f"{BASE_URL}/match/{session_id}")
    
    print(f"Skill Match: {response.status_code}")
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 202:
        print("Skill matching is still being processed...")
        return None
    else:
        print(response.text)
        return None

def test_question_answering(session_id: str, question: str):
    """Test the question answering endpoint"""
    data = {
        "session_id": session_id,
        "question": question
    }
    
    response = requests.post(f"{BASE_URL}/question", json=data)
    
    print(f"Question Answering: {response.status_code}")
    if response.status_code == 200:
        answer = response.json().get('answer')
        print(f"Question: {question}")
        print(f"Answer: {answer}")
        return answer
    else:
        print(response.text)
        return None

def get_suggested_questions(session_id: str):
    """Get suggested interview questions"""
    response = requests.get(f"{BASE_URL}/questions/{session_id}")
    
    print(f"Suggested Questions: {response.status_code}")
    if response.status_code == 200:
        questions = response.json().get('questions', [])
        print("Suggested Questions:")
        for i, q in enumerate(questions, 1):
            print(f"{i}. {q}")
        return questions
    else:
        print(response.text)
        return None

def run_full_test(resume_path: str, job_url: str):
    """Run a full test of the API workflow"""
    # Check API health
    if not test_api_health():
        print("API health check failed. Make sure the API is running.")
        return
    
    # Upload resume
    session_id = test_resume_upload(resume_path)
    if not session_id:
        print("Resume upload failed.")
        return
    
    # Process job URL
    if not test_job_url_processing(session_id, job_url):
        print("Job URL processing failed.")
        return
    
    # Wait for processing to complete
    print("\nWaiting for job and resume processing to complete...")
    job_analysis = None
    resume_analysis = None
    
    for _ in range(10):  # Try for up to 10 times
        time.sleep(3)  # Wait 3 seconds between checks
        
        if not resume_analysis:
            resume_analysis = get_resume_analysis(session_id)
        
        if not job_analysis:
            job_analysis = get_job_analysis(session_id)
        
        if resume_analysis and job_analysis:
            break
    
    if not resume_analysis or not job_analysis:
        print("Timed out waiting for processing to complete.")
        return
    
    # Request skill matching
    if not test_skill_matching(session_id):
        print("Skill matching request failed.")
        return
    
    # Wait for skill matching to complete
    print("\nWaiting for skill matching to complete...")
    skill_match = None
    
    for _ in range(10):  # Try for up to 10 times
        time.sleep(3)  # Wait 3 seconds between checks
        skill_match = get_skill_match(session_id)
        if skill_match:
            break
    
    if not skill_match:
        print("Timed out waiting for skill matching to complete.")
        return
    
    # Print overall match percentage
    overall_match = skill_match.get('overall_match', {})
    print(f"\nOverall Match: {overall_match.get('percentage')}%")
    print(f"Assessment: {overall_match.get('assessment')}")
    
    # Get suggested questions
    questions = get_suggested_questions(session_id)
    
    if questions:
        # Test question answering with the first suggested question
        test_question_answering(session_id, questions[0])
    
    print("\nFull test completed successfully!")

if __name__ == "__main__":
    # Replace with your actual resume path and job URL
    resume_path = input("Enter the path to your resume PDF: ")
    job_url = input("Enter a job posting URL: ")
    
    run_full_test(resume_path, job_url) 