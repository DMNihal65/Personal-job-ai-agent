from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from collections import Counter
import re
import time
import json
import logging
import os
import tempfile
from typing import Dict, List, Tuple, Optional
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import PyPDF2
import io

# LangChain components
from langchain_google_genai import GoogleGenerativeAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import StructuredOutputParser, ResponseSchema

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedJobScraper:
    def __init__(self, gemini_api_key: str):
        self.setup_chrome_options()
        self.setup_llm(gemini_api_key)
        self.setup_output_parsers()
        
    def setup_chrome_options(self):
        """Configure Chrome options for reliable scraping"""
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless=new")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--enable-javascript")
        self.chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        self.chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
    def setup_llm(self, api_key: str):
        self.llm = GoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=api_key,
            temperature=0.2,
            max_output_tokens=2000
        )
        
    def setup_output_parsers(self):
        response_schemas = [
            ResponseSchema(name="technical_skills", type="List[str]", description="Technical skills required"),
            ResponseSchema(name="soft_skills", type="List[str]", description="Soft skills required"),
            ResponseSchema(name="certifications", type="List[str]", description="Required certifications"),
            ResponseSchema(name="experience", type="str", description="Years of experience required"),
            ResponseSchema(name="education", type="List[str]", description="Education requirements"),
            ResponseSchema(name="keywords", type="List[str]", description="Important keywords from the job description")
        ]
        self.output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        
    def scrape_website(self, url: str) -> str:
        """Scrape job description from URL with improved error handling"""
        try:
            logger.info(f"Starting to scrape URL: {url}")
            
            # Setup webdriver with automatic ChromeDriver management
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=self.chrome_options)
            
            try:
                driver.get(url)
                logger.info("Page loaded successfully")

                # Wait for body to be present
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Wait additional time for dynamic content
                time.sleep(3)
                
                # Get page source and parse with BeautifulSoup
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Try different methods to find job description
                job_description = ""
                
                # Method 1: Look for common job description containers
                selectors = [
                    "div[class*='job-description']",
                    "div[class*='description']",
                    "div[class*='details']",
                    "#job-description",
                    "[class*='posting']",
                    "article"
                ]
                
                for selector in selectors:
                    elements = soup.select(selector)
                    if elements:
                        job_description = max([elem.get_text(strip=True) for elem in elements], key=len)
                        if len(job_description) > 100:  # Minimum length check
                            break
                
                # Method 2: Find largest text block if no description found
                if not job_description:
                    text_blocks = [p.get_text(strip=True) for p in soup.find_all(['p', 'div', 'section'])]
                    if text_blocks:
                        job_description = max(text_blocks, key=len)
                
                if not job_description:
                    raise ValueError("Could not find job description content")
                
                # Clean the text
                job_description = re.sub(r'\s+', ' ', job_description).strip()
                logger.info(f"Successfully extracted job description ({len(job_description)} characters)")
                
                return job_description
                
            finally:
                driver.quit()
                
        except Exception as e:
            logger.error(f"Error scraping website: {str(e)}")
            raise ValueError(f"Failed to extract job content: {str(e)}")
    
    def analyze_job_description(self, text: str) -> Dict:
        """Analyze job description text"""
        try:
            prompt = PromptTemplate(
                template="""Analyze this job description and extract key information in EXACTLY this format:

                Job Description:
                {text}

                STRICT OUTPUT FORMAT (Return ONLY this JSON object):
                {{
                    "technical_skills": ["skill1", "skill2"],
                    "soft_skills": ["skill1", "skill2"],
                    "missing_keywords": [],
                    "existing_keywords": [],
                    "keyword_ranking": [["keyword1", 9], ["keyword2", 8]],
                    "required_experience": "X years",
                    "education_requirements": ["requirement1", "requirement2"],
                    "suggested_modifications": {{
                        "section_name": {{
                            "content": "LaTeX formatted content",
                            "location": "start|end"
                        }}
                    }}
                }}

                STRICT RULES:
                1. Return ONLY the JSON object, no other text
                2. ALL keys must be present in the response
                3. technical_skills: List of technical skills mentioned
                4. soft_skills: List of soft skills and competencies
                5. keyword_ranking: List of [keyword, importance_score] pairs, score from 1-10
                6. missing_keywords and existing_keywords must be arrays (can be empty)
                7. suggested_modifications must be a dictionary (can be empty)
                8. Do not include any explanatory text or markdown
                """,
                input_variables=["text"]
            )

            chain = LLMChain(llm=self.llm, prompt=prompt)
            result = chain.invoke({"text": text})
            
            # Clean and parse the response
            response_text = result['text'].strip()
            # Remove any markdown code block indicators
            response_text = response_text.replace('```json', '').replace('```', '')
            
            # Find the JSON object
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                response_text = response_text[start_idx:end_idx]
            
            # Parse and validate response
            response = json.loads(response_text)
            
            # Ensure all required keys exist
            required_keys = {
                "technical_skills",
                "soft_skills",
                "missing_keywords",
                "existing_keywords",
                "keyword_ranking",
                "required_experience",
                "education_requirements",
                "suggested_modifications"
            }
            
            # Initialize default structure
            default_structure = {
                "technical_skills": [],
                "soft_skills": [],
                "missing_keywords": [],
                "existing_keywords": [],
                "keyword_ranking": [],
                "required_experience": "Not specified",
                "education_requirements": [],
                "suggested_modifications": {}
            }
            
            # Merge response with default structure
            for key in required_keys:
                if key not in response:
                    response[key] = default_structure[key]
                    logger.warning(f"Missing key '{key}' in response, using default value")
            
            # Validate types
            list_keys = ["technical_skills", "soft_skills", "missing_keywords", 
                        "existing_keywords", "education_requirements"]
            for key in list_keys:
                if not isinstance(response[key], list):
                    response[key] = list(response[key]) if response[key] else []
            
            if not isinstance(response["keyword_ranking"], list):
                response["keyword_ranking"] = []
            
            if not isinstance(response["suggested_modifications"], dict):
                response["suggested_modifications"] = {}
            
            return response

        except Exception as e:
            logger.error(f"Error analyzing job description: {str(e)}")
            logger.error(f"Raw response: {result['text'] if 'result' in locals() else 'No response'}")
            # Return default structure on error
            return {
                "technical_skills": [],
                "soft_skills": [],
                "missing_keywords": [],
                "existing_keywords": [],
                "keyword_ranking": [],
                "required_experience": "Not specified",
                "education_requirements": [],
                "suggested_modifications": {}
            }

class ResumeParser:
    def __init__(self, gemini_api_key: str):
        """Initialize the resume parser with the Gemini API key"""
        self.setup_llm(gemini_api_key)
        
    def setup_llm(self, api_key: str):
        """Set up the language model for resume analysis"""
        self.llm = GoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=api_key,
            temperature=0.1,
            max_output_tokens=4000
        )
    
    def extract_text_from_pdf(self, pdf_file) -> str:
        """Extract text content from a PDF file"""
        try:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract text from each page
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
            
            # Clean the text
            text = re.sub(r'\s+', ' ', text).strip()
            logger.info(f"Successfully extracted text from PDF ({len(text)} characters)")
            
            return text
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    def analyze_resume(self, resume_text: str) -> Dict:
        """Analyze resume text and extract key information"""
        try:
            prompt = PromptTemplate(
                template="""Analyze this resume and extract key information in EXACTLY this format:

                Resume Text:
                {text}

                STRICT OUTPUT FORMAT (Return ONLY this JSON object):
                {{
                    "personal_info": {{
                        "name": "Full Name",
                        "email": "email@example.com",
                        "phone": "phone number",
                        "location": "City, State"
                    }},
                    "summary": "Professional summary",
                    "skills": {{
                        "technical": ["skill1", "skill2"],
                        "soft": ["skill1", "skill2"],
                        "languages": ["language1", "language2"],
                        "tools": ["tool1", "tool2"],
                        "frameworks": ["framework1", "framework2"],
                        "methodologies": ["methodology1", "methodology2"]
                    }},
                    "experience": [
                        {{
                            "title": "Job Title",
                            "company": "Company Name",
                            "duration": "Start Date - End Date",
                            "responsibilities": ["responsibility1", "responsibility2"],
                            "achievements": ["achievement1", "achievement2"],
                            "skills_used": ["skill1", "skill2"]
                        }}
                    ],
                    "education": [
                        {{
                            "degree": "Degree Name",
                            "institution": "Institution Name",
                            "graduation_date": "Graduation Date",
                            "gpa": "GPA if mentioned",
                            "relevant_coursework": ["course1", "course2"]
                        }}
                    ],
                    "certifications": ["certification1", "certification2"],
                    "projects": [
                        {{
                            "name": "Project Name",
                            "description": "Project Description",
                            "technologies": ["tech1", "tech2"],
                            "outcomes": ["outcome1", "outcome2"]
                        }}
                    ],
                    "keywords": ["keyword1", "keyword2"],
                    "strengths": ["strength1", "strength2"],
                    "achievements": ["achievement1", "achievement2"]
                }}

                STRICT RULES:
                1. Return ONLY the JSON object, no other text
                2. ALL keys must be present in the response
                3. Extract ALL skills mentioned in the resume and categorize them appropriately
                4. For experience, include ALL job positions with detailed responsibilities and achievements
                5. For education, include ALL degrees and institutions
                6. Extract ALL certifications mentioned
                7. Extract ALL projects mentioned with technologies used
                8. keywords should include important terms that represent the candidate's expertise
                9. strengths should highlight the candidate's core professional strengths
                10. achievements should list major career accomplishments
                11. Do not include any explanatory text or markdown
                """,
                input_variables=["text"]
            )

            chain = LLMChain(llm=self.llm, prompt=prompt)
            result = chain.invoke({"text": resume_text})
            
            # Clean and parse the response
            response_text = result['text'].strip()
            # Remove any markdown code block indicators
            response_text = response_text.replace('```json', '').replace('```', '')
            
            # Find the JSON object
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                response_text = response_text[start_idx:end_idx]
            
            # Parse and validate response
            response = json.loads(response_text)
            
            # Ensure all required keys exist
            required_keys = {
                "personal_info",
                "summary",
                "skills",
                "experience",
                "education",
                "certifications",
                "projects",
                "keywords",
                "strengths",
                "achievements"
            }
            
            # Initialize default structure
            default_structure = {
                "personal_info": {
                    "name": "",
                    "email": "",
                    "phone": "",
                    "location": ""
                },
                "summary": "",
                "skills": {
                    "technical": [],
                    "soft": [],
                    "languages": [],
                    "tools": [],
                    "frameworks": [],
                    "methodologies": []
                },
                "experience": [],
                "education": [],
                "certifications": [],
                "projects": [],
                "keywords": [],
                "strengths": [],
                "achievements": []
            }
            
            # Merge response with default structure
            for key in required_keys:
                if key not in response:
                    response[key] = default_structure[key]
                    logger.warning(f"Missing key '{key}' in response, using default value")
            
            # Ensure skills structure is complete
            if "skills" in response:
                skill_categories = ["technical", "soft", "languages", "tools", "frameworks", "methodologies"]
                for category in skill_categories:
                    if category not in response["skills"]:
                        response["skills"][category] = []
            
            return response

        except Exception as e:
            logger.error(f"Error analyzing resume: {str(e)}")
            logger.error(f"Raw response: {result['text'] if 'result' in locals() else 'No response'}")
            # Return default structure on error
            return {
                "personal_info": {
                    "name": "",
                    "email": "",
                    "phone": "",
                    "location": ""
                },
                "summary": "",
                "skills": {
                    "technical": [],
                    "soft": [],
                    "languages": [],
                    "tools": [],
                    "frameworks": [],
                    "methodologies": []
                },
                "experience": [],
                "education": [],
                "certifications": [],
                "projects": [],
                "keywords": [],
                "strengths": [],
                "achievements": []
            }

class JobApplicationAgent:
    def __init__(self, gemini_api_key: str):
        """Initialize the job application agent"""
        self.api_key = gemini_api_key
        self.job_scraper = EnhancedJobScraper(gemini_api_key)
        self.resume_parser = ResumeParser(gemini_api_key)
        self.setup_llm(gemini_api_key)
        
        # Store context
        self.job_description = None
        self.job_analysis = None
        self.resume_text = None
        self.resume_analysis = None
        self.skill_match_analysis = None
    
    def setup_llm(self, api_key: str):
        """Set up the language model for question answering"""
        self.llm = GoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=api_key,
            temperature=0.7,  # Higher temperature for more creative responses
            max_output_tokens=1000
        )
    
    def process_job_url(self, url: str) -> Dict:
        """Process a job posting URL and extract/analyze the job description"""
        try:
            # Scrape the job description
            self.job_description = self.job_scraper.scrape_website(url)
            
            # Analyze the job description
            self.job_analysis = self.job_scraper.analyze_job_description(self.job_description)
            
            # If resume is already processed, perform skill matching
            if self.resume_analysis:
                self.match_skills_with_job()
            
            return self.job_analysis
        
        except Exception as e:
            logger.error(f"Error processing job URL: {str(e)}")
            raise ValueError(f"Failed to process job URL: {str(e)}")
    
    def process_resume(self, resume_file) -> Dict:
        """Process a resume file and extract/analyze the content"""
        try:
            # Extract text from the resume
            self.resume_text = self.resume_parser.extract_text_from_pdf(resume_file)
            
            # Analyze the resume
            self.resume_analysis = self.resume_parser.analyze_resume(self.resume_text)
            
            # If job is already processed, perform skill matching
            if self.job_analysis:
                self.match_skills_with_job()
            
            return self.resume_analysis
        
        except Exception as e:
            logger.error(f"Error processing resume: {str(e)}")
            raise ValueError(f"Failed to process resume: {str(e)}")
    
    def match_skills_with_job(self) -> Dict:
        """Match resume skills with job requirements"""
        if not self.job_analysis or not self.resume_analysis:
            raise ValueError("Job description and resume must be processed before matching skills")
        
        try:
            prompt = PromptTemplate(
                template="""Analyze the candidate's resume and the job description to identify matches and gaps.

                Resume Information:
                {resume_info}
                
                Job Description:
                {job_description}
                
                Job Analysis:
                {job_analysis}
                
                STRICT OUTPUT FORMAT (Return ONLY this JSON object):
                {{
                    "matching_skills": [
                        {{
                            "skill": "skill name",
                            "resume_evidence": "where/how mentioned in resume",
                            "job_importance": "high/medium/low"
                        }}
                    ],
                    "missing_skills": [
                        {{
                            "skill": "skill name",
                            "importance": "high/medium/low",
                            "alternative_skills": ["skill1", "skill2"]
                        }}
                    ],
                    "skill_match_percentage": 85,
                    "strengths": [
                        {{
                            "strength": "strength description",
                            "relevance": "why this is relevant to the job"
                        }}
                    ],
                    "improvement_areas": [
                        {{
                            "area": "area to improve",
                            "suggestion": "how to address this"
                        }}
                    ],
                    "resume_enhancement_suggestions": [
                        {{
                            "section": "section name",
                            "suggestion": "what to add/modify",
                            "reason": "why this would help"
                        }}
                    ],
                    "interview_talking_points": [
                        {{
                            "topic": "topic to emphasize",
                            "key_points": ["point1", "point2"]
                        }}
                    ]
                }}

                STRICT RULES:
                1. Return ONLY the JSON object, no other text
                2. ALL keys must be present in the response
                3. Be specific and detailed in your analysis
                4. Provide actionable suggestions
                5. Do not include any explanatory text or markdown
                """,
                input_variables=["resume_info", "job_description", "job_analysis"]
            )

            # Format the resume info and job analysis as readable text
            resume_info = json.dumps(self.resume_analysis, indent=2)
            job_analysis = json.dumps(self.job_analysis, indent=2)
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            result = chain.invoke({
                "resume_info": resume_info,
                "job_description": self.job_description,
                "job_analysis": job_analysis
            })
            
            # Clean and parse the response
            response_text = result['text'].strip()
            # Remove any markdown code block indicators
            response_text = response_text.replace('```json', '').replace('```', '')
            
            # Find the JSON object
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                response_text = response_text[start_idx:end_idx]
            
            # Parse and validate response
            self.skill_match_analysis = json.loads(response_text)
            
            return self.skill_match_analysis
            
        except Exception as e:
            logger.error(f"Error matching skills with job: {str(e)}")
            logger.error(f"Raw response: {result['text'] if 'result' in locals() else 'No response'}")
            # Return default structure on error
            self.skill_match_analysis = {
                "matching_skills": [],
                "missing_skills": [],
                "skill_match_percentage": 0,
                "strengths": [],
                "improvement_areas": [],
                "resume_enhancement_suggestions": [],
                "interview_talking_points": []
            }
            return self.skill_match_analysis
    
    def answer_question(self, question: str) -> str:
        """Answer a job application question based on the resume and job description"""
        if not self.job_description or not self.resume_text:
            raise ValueError("Job description and resume must be processed before answering questions")
        
        try:
            prompt = PromptTemplate(
                template="""You are a helpful assistant helping a job applicant prepare for their interview. 
                You have access to their resume and the job description they're applying for.
                
                Resume Information:
                {resume_info}
                
                Job Description:
                {job_description}
                
                Job Analysis:
                {job_analysis}
                
                Skill Match Analysis:
                {skill_match_analysis}
                
                Question: {question}
                
                Please provide a concise, attention-grabbing answer that sounds natural and human-written.
                Keep your response brief (3-5 sentences) but make sure it directly answers the question.
                Use simple, plain English and avoid corporate jargon or overly formal language.
                Do not mention that you're an AI or that you're using any information provided.
                Write as if you are the job applicant speaking in first person.
                
                Your answer should:
                1. Be specific and tailored to both the resume and job description
                2. Highlight relevant skills and experiences
                3. Sound confident but not arrogant
                4. Be conversational and natural
                5. Avoid clichés and generic statements
                
                Your answer:
                """,
                input_variables=["resume_info", "job_description", "job_analysis", "skill_match_analysis", "question"]
            )

            # Format the resume info and job analysis as readable text
            resume_info = json.dumps(self.resume_analysis, indent=2)
            job_analysis = json.dumps(self.job_analysis, indent=2)
            skill_match_analysis = json.dumps(self.skill_match_analysis, indent=2) if self.skill_match_analysis else "{}"
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            result = chain.invoke({
                "resume_info": resume_info,
                "job_description": self.job_description,
                "job_analysis": job_analysis,
                "skill_match_analysis": skill_match_analysis,
                "question": question
            })
            
            return result['text'].strip()
        
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return f"I'm sorry, I couldn't generate an answer due to an error: {str(e)}"
    
    def get_skill_match_summary(self) -> str:
        """Get a summary of the skill match analysis"""
        if not self.skill_match_analysis:
            if self.job_analysis and self.resume_analysis:
                self.match_skills_with_job()
            else:
                raise ValueError("Job description and resume must be processed before getting skill match summary")
        
        try:
            match_percentage = self.skill_match_analysis.get("skill_match_percentage", 0)
            
            summary = f"\n===== Skill Match Summary =====\n"
            summary += f"Overall Match: {match_percentage}%\n\n"
            
            # Matching skills
            summary += "🟢 Matching Skills:\n"
            for skill in self.skill_match_analysis.get("matching_skills", [])[:5]:
                summary += f"  • {skill['skill']} (Importance: {skill['job_importance']})\n"
            
            # Missing skills
            summary += "\n🔴 Missing Skills:\n"
            for skill in self.skill_match_analysis.get("missing_skills", [])[:5]:
                summary += f"  • {skill['skill']} (Importance: {skill['importance']})\n"
                if skill.get("alternative_skills"):
                    summary += f"    Alternative skills: {', '.join(skill['alternative_skills'])}\n"
            
            # Strengths
            summary += "\n💪 Key Strengths:\n"
            for strength in self.skill_match_analysis.get("strengths", [])[:3]:
                summary += f"  • {strength['strength']}\n"
            
            # Improvement areas
            summary += "\n📈 Areas for Improvement:\n"
            for area in self.skill_match_analysis.get("improvement_areas", [])[:3]:
                summary += f"  • {area['area']}: {area['suggestion']}\n"
            
            # Resume enhancement
            summary += "\n📝 Resume Enhancement Suggestions:\n"
            for suggestion in self.skill_match_analysis.get("resume_enhancement_suggestions", [])[:3]:
                summary += f"  • {suggestion['section']}: {suggestion['suggestion']}\n"
            
            # Interview talking points
            summary += "\n🗣️ Key Interview Talking Points:\n"
            for point in self.skill_match_analysis.get("interview_talking_points", [])[:3]:
                summary += f"  • {point['topic']}:\n"
                for key_point in point.get("key_points", [])[:2]:
                    summary += f"    - {key_point}\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting skill match summary: {str(e)}")
            return "Could not generate skill match summary due to an error."

def main():
    GEMINI_API_KEY = "AIzaSyCkb4a_yq_Iviefm_FJHQr40ukm7BqlLww"
    
    print("\n" + "="*50)
    print(" "*15 + "Job Application Assistant")
    print("="*50)
    print("\nThis tool helps you prepare for job applications by analyzing job descriptions")
    print("and your resume, then helping you craft perfect answers to common questions.")
    
    agent = JobApplicationAgent(GEMINI_API_KEY)
    
    # Step 1: Process resume
    resume_processed = False
    while not resume_processed:
        print("\n" + "-"*50)
        print(" "*15 + "Step 1: Upload Your Resume")
        print("-"*50)
        resume_path = input("\nEnter the path to your resume PDF file: ").strip()
        
        try:
            with open(resume_path, 'rb') as resume_file:
                print("\n⏳ Processing your resume... Please wait...")
                resume_analysis = agent.process_resume(resume_file)
                
                print("\n✅ Resume processed successfully!")
                print(f"\n👤 Found information for: {resume_analysis['personal_info']['name']}")
                
                # Display technical skills
                print("\n🔧 Technical skills identified:")
                all_tech_skills = []
                for category in ['technical', 'languages', 'tools', 'frameworks']:
                    all_tech_skills.extend(resume_analysis['skills'].get(category, []))
                
                # Display up to 10 skills, 5 per line
                for i, skill in enumerate(all_tech_skills[:10]):
                    if i % 5 == 0:
                        print("  ", end="")
                    print(f"{skill}", end=", " if (i+1) % 5 != 0 and i != len(all_tech_skills[:10])-1 else "\n")
                
                if len(all_tech_skills) > 10:
                    print(f"  ...and {len(all_tech_skills) - 10} more")
                
                # Display experience summary
                print("\n💼 Experience summary:")
                for i, exp in enumerate(resume_analysis['experience'][:2]):
                    print(f"  • {exp['title']} at {exp['company']} ({exp['duration']})")
                
                if len(resume_analysis['experience']) > 2:
                    print(f"  ...and {len(resume_analysis['experience']) - 2} more positions")
                
                resume_processed = True
        
        except FileNotFoundError:
            print(f"\n❌ File not found: {resume_path}")
            print("Please check the file path and try again.")
        
        except Exception as e:
            print(f"\n❌ Error processing resume: {str(e)}")
            retry = input("Would you like to try again? (y/n): ").strip().lower()
            if retry != 'y':
                print("Exiting program.")
                return
    
    # Step 2: Process job description
    job_processed = False
    while not job_processed:
        print("\n" + "-"*50)
        print(" "*15 + "Step 2: Enter Job Posting URL")
        print("-"*50)
        job_url = input("\nEnter the job posting URL: ").strip()
        
        if not job_url.startswith(('http://', 'https://')):
            print("Invalid URL format. Please include http:// or https://")
            continue
        
        try:
            print("\n⏳ Scraping and analyzing job description... Please wait...")
            job_analysis = agent.process_job_url(job_url)
            
            print("\n✅ Job description processed successfully!")
            
            # Display technical skills required
            print("\n📚 Technical Skills Required:")
            if job_analysis.get('technical_skills'):
                for i, skill in enumerate(job_analysis['technical_skills'][:8]):
                    if i % 4 == 0:
                        print("  ", end="")
                    print(f"{skill}", end=", " if (i+1) % 4 != 0 and i != len(job_analysis['technical_skills'][:8])-1 else "\n")
                
                if len(job_analysis['technical_skills']) > 8:
                    print(f"  ...and {len(job_analysis['technical_skills']) - 8} more")
            else:
                print("  No specific technical skills mentioned")
            
            # Display soft skills required
            print("\n🤝 Soft Skills Required:")
            if job_analysis.get('soft_skills'):
                for i, skill in enumerate(job_analysis['soft_skills'][:6]):
                    if i % 3 == 0:
                        print("  ", end="")
                    print(f"{skill}", end=", " if (i+1) % 3 != 0 and i != len(job_analysis['soft_skills'][:6])-1 else "\n")
                
                if len(job_analysis['soft_skills']) > 6:
                    print(f"  ...and {len(job_analysis['soft_skills']) - 6} more")
            else:
                print("  No specific soft skills mentioned")
            
            # Display top keywords
            print("\n🎯 Top Keywords by Importance:")
            if job_analysis.get('keyword_ranking'):
                for keyword, score in job_analysis['keyword_ranking'][:5]:
                    print(f"  • {keyword}: {score}/10")
                
                if len(job_analysis['keyword_ranking']) > 5:
                    print(f"  ...and {len(job_analysis['keyword_ranking']) - 5} more")
            else:
                print("  No keyword rankings available")
            
            # Display experience required
            print(f"\n⏳ Experience Required: {job_analysis.get('required_experience', 'Not specified')}")
            
            # Display education requirements
            print("\n🎓 Education Requirements:")
            if job_analysis.get('education_requirements'):
                for req in job_analysis['education_requirements'][:3]:
                    print(f"  • {req}")
                
                if len(job_analysis['education_requirements']) > 3:
                    print(f"  ...and {len(job_analysis['education_requirements']) - 3} more")
            else:
                print("  No specific education requirements mentioned")
            
            job_processed = True
        
        except Exception as e:
            print(f"\n❌ Error processing job URL: {str(e)}")
            retry = input("Would you like to try again? (y/n): ").strip().lower()
            if retry != 'y':
                print("Exiting program.")
                return
    
    # Step 3: Show skill match analysis
    try:
        print("\n" + "-"*50)
        print(" "*15 + "Step 3: Skill Match Analysis")
        print("-"*50)
        
        print("\n⏳ Analyzing skill match between your resume and the job requirements...")
        if not agent.skill_match_analysis:
            agent.match_skills_with_job()
        
        skill_match_summary = agent.get_skill_match_summary()
        print(skill_match_summary)
        
    except Exception as e:
        print(f"\n❌ Error generating skill match analysis: {str(e)}")
    
    # Step 4: Answer questions
    print("\n" + "-"*50)
    print(" "*15 + "Step 4: Interview Question Assistance")
    print("-"*50)
    print("\nYou can now ask for help with common interview questions.")
    print("Type 'exit' to quit the program.")
    print("\nSuggested questions:")
    print("  • Why am I suitable for this role?")
    print("  • Why do I want to join this company?")
    print("  • How do my skills align with the company's goals?")
    print("  • What relevant experience do I have for this position?")
    print("  • What makes me stand out from other candidates?")
    
    while True:
        question = input("\nEnter your question (or 'exit' to quit): ").strip()
        
        if question.lower() == 'exit':
            print("\nThank you for using the Job Application Assistant. Good luck with your application!")
            break
        
        if not question:
            continue
        
        print("\n⏳ Generating answer... Please wait...")
        answer = agent.answer_question(question)
        
        print("\n🔹 Suggested Answer:")
        print(answer)
        
        print("\n" + "-"*50)
        print("Would you like to ask another question? (Type 'exit' to quit)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc() 