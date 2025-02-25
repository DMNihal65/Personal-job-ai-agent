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
        """Analyze job description text with enhanced detail"""
        try:
            # First pass: Extract basic information and company details
            initial_prompt = PromptTemplate(
                template="""Analyze this job description and extract key information in EXACTLY this format:

                Job Description:
                {text}

                STRICT OUTPUT FORMAT (Return ONLY this JSON object):
                {{
                    "company_name": "Company Name",
                    "job_title": "Job Title",
                    "job_location": "Location (remote/hybrid/onsite, city, country)",
                    "company_description": "Brief description of the company",
                    "job_summary": "Brief summary of the job role",
                    "department": "Department or team",
                    "reporting_to": "Position reports to",
                    "employment_type": "Full-time/Part-time/Contract",
                    "technical_skills": ["skill1", "skill2"],
                    "soft_skills": ["skill1", "skill2"],
                    "required_experience": "X years",
                    "education_requirements": ["requirement1", "requirement2"],
                    "certifications": ["certification1", "certification2"],
                    "responsibilities": ["responsibility1", "responsibility2"],
                    "benefits": ["benefit1", "benefit2"],
                    "salary_range": "Salary range if mentioned",
                    "application_deadline": "Deadline if mentioned"
                }}

                STRICT RULES:
                1. Return ONLY the JSON object, no other text
                2. ALL keys must be present in the response
                3. Extract as much detail as possible from the job description
                4. If information is not available, use empty string or empty array
                5. Do not include any explanatory text or markdown
                """,
                input_variables=["text"]
            )

            chain = LLMChain(llm=self.llm, prompt=initial_prompt)
            initial_result = chain.invoke({"text": text})
            
            # Clean and parse the response
            initial_response_text = initial_result['text'].strip()
            # Remove any markdown code block indicators
            initial_response_text = initial_response_text.replace('```json', '').replace('```', '')
            
            # Find the JSON object
            start_idx = initial_response_text.find('{')
            end_idx = initial_response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                initial_response_text = initial_response_text[start_idx:end_idx]
            
            # Parse initial response
            initial_response = json.loads(initial_response_text)
            
            # Second pass: Detailed analysis with keywords and ATS optimization
            detailed_prompt = PromptTemplate(
                template="""Perform a detailed analysis of this job description for ATS optimization.

                Job Description:
                {text}
                
                Initial Analysis:
                {initial_analysis}

                STRICT OUTPUT FORMAT (Return ONLY this JSON object):
                {{
                    "keyword_ranking": [["keyword1", 9], ["keyword2", 8]],
                    "missing_keywords": [],
                    "existing_keywords": [],
                    "industry_specific_terms": ["term1", "term2"],
                    "company_values": ["value1", "value2"],
                    "company_culture": "Description of company culture",
                    "growth_opportunities": "Description of growth opportunities",
                    "key_challenges": ["challenge1", "challenge2"],
                    "ideal_candidate_profile": "Description of ideal candidate",
                    "ats_optimization_tips": ["tip1", "tip2"],
                    "application_success_factors": ["factor1", "factor2"]
                }}

                STRICT RULES:
                1. Return ONLY the JSON object, no other text
                2. ALL keys must be present in the response
                3. keyword_ranking: List of [keyword, importance_score] pairs, score from 1-10, include at least 15 keywords
                4. missing_keywords: Common keywords in this industry that are missing from the job description
                5. existing_keywords: Important keywords that are already present in the job description
                6. Focus on providing detailed, actionable insights for job applicants
                7. Do not include any explanatory text or markdown
                """,
                input_variables=["text", "initial_analysis"]
            )

            # Format the initial analysis as readable text
            initial_analysis = json.dumps(initial_response, indent=2)
            
            chain = LLMChain(llm=self.llm, prompt=detailed_prompt)
            detailed_result = chain.invoke({
                "text": text,
                "initial_analysis": initial_analysis
            })
            
            # Clean and parse the response
            detailed_response_text = detailed_result['text'].strip()
            # Remove any markdown code block indicators
            detailed_response_text = detailed_response_text.replace('```json', '').replace('```', '')
            
            # Find the JSON object
            start_idx = detailed_response_text.find('{')
            end_idx = detailed_response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                detailed_response_text = detailed_response_text[start_idx:end_idx]
            
            # Parse detailed response
            detailed_response = json.loads(detailed_response_text)
            
            # Third pass: Generate a comprehensive summary
            summary_prompt = PromptTemplate(
                template="""Create a comprehensive summary of this job posting that would help a candidate understand the role and prepare for an application.

                Job Description:
                {text}
                
                Initial Analysis:
                {initial_analysis}
                
                Detailed Analysis:
                {detailed_analysis}

                STRICT OUTPUT FORMAT (Return ONLY this JSON object):
                {{
                    "executive_summary": "A concise 3-4 sentence overview of the position",
                    "key_qualifications_summary": "Summary of the most important qualifications",
                    "company_overview": "Brief overview of the company and its culture",
                    "role_importance": "Why this role is important to the company",
                    "success_metrics": "How success would be measured in this role",
                    "career_path": "Potential career progression from this role",
                    "interview_preparation_tips": ["tip1", "tip2"],
                    "application_advice": "Advice for applying to this specific role"
                }}

                STRICT RULES:
                1. Return ONLY the JSON object, no other text
                2. ALL keys must be present in the response
                3. Be specific, detailed, and actionable in your summaries
                4. Focus on helping the candidate understand the role deeply
                5. Do not include any explanatory text or markdown
                """,
                input_variables=["text", "initial_analysis", "detailed_analysis"]
            )

            # Format the detailed analysis as readable text
            detailed_analysis = json.dumps(detailed_response, indent=2)
            
            chain = LLMChain(llm=self.llm, prompt=summary_prompt)
            summary_result = chain.invoke({
                "text": text,
                "initial_analysis": initial_analysis,
                "detailed_analysis": detailed_analysis
            })
            
            # Clean and parse the response
            summary_response_text = summary_result['text'].strip()
            # Remove any markdown code block indicators
            summary_response_text = summary_response_text.replace('```json', '').replace('```', '')
            
            # Find the JSON object
            start_idx = summary_response_text.find('{')
            end_idx = summary_response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                summary_response_text = summary_response_text[start_idx:end_idx]
            
            # Parse summary response
            summary_response = json.loads(summary_response_text)
            
            # Combine all responses into a comprehensive analysis
            combined_response = {
                **initial_response,
                **detailed_response,
                **summary_response
            }
            
            return combined_response

        except Exception as e:
            logger.error(f"Error analyzing job description: {str(e)}")
            logger.error(f"Raw response: {initial_result['text'] if 'initial_result' in locals() else 'No response'}")
            # Return default structure on error
            return {
                "company_name": "",
                "job_title": "",
                "job_location": "",
                "company_description": "",
                "job_summary": "",
                "department": "",
                "reporting_to": "",
                "employment_type": "",
                "technical_skills": [],
                "soft_skills": [],
                "required_experience": "Not specified",
                "education_requirements": [],
                "certifications": [],
                "responsibilities": [],
                "benefits": [],
                "salary_range": "",
                "application_deadline": "",
                "keyword_ranking": [],
                "missing_keywords": [],
                "existing_keywords": [],
                "industry_specific_terms": [],
                "company_values": [],
                "company_culture": "",
                "growth_opportunities": "",
                "key_challenges": [],
                "ideal_candidate_profile": "",
                "ats_optimization_tips": [],
                "application_success_factors": [],
                "executive_summary": "",
                "key_qualifications_summary": "",
                "company_overview": "",
                "role_importance": "",
                "success_metrics": "",
                "career_path": "",
                "interview_preparation_tips": [],
                "application_advice": ""
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
        """Analyze resume text and extract key information with enhanced detail"""
        try:
            # First pass: Extract basic information and structure
            initial_prompt = PromptTemplate(
                template="""Analyze this resume and extract key information in EXACTLY this format:

                Resume Text:
                {text}

                STRICT OUTPUT FORMAT (Return ONLY this JSON object):
                {{
                    "personal_info": {{
                        "name": "Full Name",
                        "email": "email@example.com",
                        "phone": "phone number",
                        "location": "City, State",
                        "linkedin": "LinkedIn profile URL if present",
                        "portfolio": "Portfolio/website URL if present",
                        "github": "GitHub profile if present"
                    }},
                    "summary": "Professional summary",
                    "skills": {{
                        "technical": ["skill1", "skill2"],
                        "soft": ["skill1", "skill2"],
                        "languages": ["language1", "language2"],
                        "tools": ["tool1", "tool2"],
                        "frameworks": ["framework1", "framework2"],
                        "methodologies": ["methodology1", "methodology2"],
                        "domain_knowledge": ["domain1", "domain2"]
                    }},
                    "experience": [
                        {{
                            "title": "Job Title",
                            "company": "Company Name",
                            "location": "Job Location",
                            "duration": "Start Date - End Date",
                            "responsibilities": ["responsibility1", "responsibility2"],
                            "achievements": ["achievement1", "achievement2"],
                            "skills_used": ["skill1", "skill2"],
                            "technologies": ["technology1", "technology2"],
                            "impact": "Quantifiable impact if mentioned"
                        }}
                    ],
                    "education": [
                        {{
                            "degree": "Degree Name",
                            "institution": "Institution Name",
                            "location": "Institution Location",
                            "graduation_date": "Graduation Date",
                            "gpa": "GPA if mentioned",
                            "honors": ["honor1", "honor2"],
                            "relevant_coursework": ["course1", "course2"],
                            "activities": ["activity1", "activity2"]
                        }}
                    ],
                    "certifications": [
                        {{
                            "name": "Certification Name",
                            "issuer": "Issuing Organization",
                            "date": "Date Obtained",
                            "expiration": "Expiration Date if applicable"
                        }}
                    ],
                    "projects": [
                        {{
                            "name": "Project Name",
                            "description": "Project Description",
                            "role": "Role in the project",
                            "duration": "Project Duration",
                            "technologies": ["tech1", "tech2"],
                            "outcomes": ["outcome1", "outcome2"],
                            "url": "Project URL if available"
                        }}
                    ],
                    "publications": [
                        {{
                            "title": "Publication Title",
                            "publisher": "Publisher",
                            "date": "Publication Date",
                            "url": "URL if available"
                        }}
                    ],
                    "awards": [
                        {{
                            "title": "Award Title",
                            "issuer": "Issuing Organization",
                            "date": "Date Received",
                            "description": "Brief description"
                        }}
                    ],
                    "languages": [
                        {{
                            "language": "Language Name",
                            "proficiency": "Proficiency Level"
                        }}
                    ],
                    "volunteer_experience": [
                        {{
                            "organization": "Organization Name",
                            "role": "Role",
                            "duration": "Duration",
                            "description": "Brief description"
                        }}
                    ]
                }}

                STRICT RULES:
                1. Return ONLY the JSON object, no other text
                2. ALL keys must be present in the response
                3. Extract ALL information mentioned in the resume
                4. If a section is not present in the resume, include the key with an empty array or appropriate default value
                5. Do not include any explanatory text or markdown
                """,
                input_variables=["text"]
            )

            chain = LLMChain(llm=self.llm, prompt=initial_prompt)
            initial_result = chain.invoke({"text": resume_text})
            
            # Clean and parse the response
            initial_response_text = initial_result['text'].strip()
            # Remove any markdown code block indicators
            initial_response_text = initial_response_text.replace('```json', '').replace('```', '')
            
            # Find the JSON object
            start_idx = initial_response_text.find('{')
            end_idx = initial_response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                initial_response_text = initial_response_text[start_idx:end_idx]
            
            # Parse initial response
            initial_response = json.loads(initial_response_text)
            
            # Second pass: Detailed analysis for ATS optimization
            detailed_prompt = PromptTemplate(
                template="""Analyze this resume for ATS optimization and extract additional insights.

                Resume Text:
                {text}
                
                Initial Analysis:
                {initial_analysis}

                STRICT OUTPUT FORMAT (Return ONLY this JSON object):
                {{
                    "keywords": ["keyword1", "keyword2"],
                    "strengths": [
                        {{
                            "strength": "Strength description",
                            "evidence": "Evidence from resume"
                        }}
                    ],
                    "achievements": [
                        {{
                            "achievement": "Achievement description",
                            "impact": "Quantifiable impact"
                        }}
                    ],
                    "skill_proficiency": [
                        {{
                            "skill": "Skill name",
                            "level": "Beginner/Intermediate/Advanced/Expert",
                            "evidence": "Evidence from resume"
                        }}
                    ],
                    "experience_summary": {{
                        "total_years": "Total years of experience",
                        "industries": ["industry1", "industry2"],
                        "company_sizes": ["startup", "enterprise", "etc"],
                        "roles": ["role category 1", "role category 2"]
                    }},
                    "gaps": [
                        {{
                            "type": "skill/experience/education gap",
                            "description": "Description of the gap",
                            "recommendation": "How to address it"
                        }}
                    ],
                    "ats_score": {{
                        "formatting": "score out of 10",
                        "keyword_optimization": "score out of 10",
                        "content_quality": "score out of 10",
                        "overall": "score out of 10"
                    }},
                    "improvement_suggestions": [
                        {{
                            "section": "Section name",
                            "issue": "Issue description",
                            "suggestion": "Improvement suggestion"
                        }}
                    ]
                }}

                STRICT RULES:
                1. Return ONLY the JSON object, no other text
                2. ALL keys must be present in the response
                3. Be specific and detailed in your analysis
                4. Focus on ATS optimization and job application readiness
                5. Do not include any explanatory text or markdown
                """,
                input_variables=["text", "initial_analysis"]
            )

            # Format the initial analysis as readable text
            initial_analysis = json.dumps(initial_response, indent=2)
            
            chain = LLMChain(llm=self.llm, prompt=detailed_prompt)
            detailed_result = chain.invoke({
                "text": resume_text,
                "initial_analysis": initial_analysis
            })
            
            # Clean and parse the response
            detailed_response_text = detailed_result['text'].strip()
            # Remove any markdown code block indicators
            detailed_response_text = detailed_response_text.replace('```json', '').replace('```', '')
            
            # Find the JSON object
            start_idx = detailed_response_text.find('{')
            end_idx = detailed_response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                detailed_response_text = detailed_response_text[start_idx:end_idx]
            
            # Parse detailed response
            detailed_response = json.loads(detailed_response_text)
            
            # Third pass: Generate a comprehensive summary
            summary_prompt = PromptTemplate(
                template="""Create a comprehensive summary of this resume that highlights the candidate's strengths and potential.

                Resume Text:
                {text}
                
                Initial Analysis:
                {initial_analysis}
                
                Detailed Analysis:
                {detailed_analysis}

                STRICT OUTPUT FORMAT (Return ONLY this JSON object):
                {{
                    "professional_snapshot": "A concise 3-4 sentence overview of the candidate",
                    "unique_selling_points": ["point1", "point2"],
                    "career_narrative": "A brief narrative of the candidate's career progression",
                    "technical_expertise_summary": "Summary of technical expertise",
                    "soft_skills_summary": "Summary of soft skills and interpersonal abilities",
                    "achievement_highlights": "Highlights of key achievements",
                    "potential_roles": ["role1", "role2"],
                    "interview_talking_points": [
                        {{
                            "topic": "Topic to discuss",
                            "key_points": ["point1", "point2"]
                        }}
                    ]
                }}

                STRICT RULES:
                1. Return ONLY the JSON object, no other text
                2. ALL keys must be present in the response
                3. Be specific, detailed, and highlight the candidate's strengths
                4. Focus on what makes this candidate unique and valuable
                5. Do not include any explanatory text or markdown
                """,
                input_variables=["text", "initial_analysis", "detailed_analysis"]
            )

            # Format the detailed analysis as readable text
            detailed_analysis = json.dumps(detailed_response, indent=2)
            
            chain = LLMChain(llm=self.llm, prompt=summary_prompt)
            summary_result = chain.invoke({
                "text": resume_text,
                "initial_analysis": initial_analysis,
                "detailed_analysis": detailed_analysis
            })
            
            # Clean and parse the response
            summary_response_text = summary_result['text'].strip()
            # Remove any markdown code block indicators
            summary_response_text = summary_response_text.replace('```json', '').replace('```', '')
            
            # Find the JSON object
            start_idx = summary_response_text.find('{')
            end_idx = summary_response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                summary_response_text = summary_response_text[start_idx:end_idx]
            
            # Parse summary response
            summary_response = json.loads(summary_response_text)
            
            # Combine all responses into a comprehensive analysis
            combined_response = {
                **initial_response,
                **detailed_response,
                **summary_response
            }
            
            # Ensure skills structure is complete
            if "skills" in combined_response:
                skill_categories = ["technical", "soft", "languages", "tools", "frameworks", "methodologies", "domain_knowledge"]
                for category in skill_categories:
                    if category not in combined_response["skills"]:
                        combined_response["skills"][category] = []
            
            return combined_response

        except Exception as e:
            logger.error(f"Error analyzing resume: {str(e)}")
            logger.error(f"Raw response: {initial_result['text'] if 'initial_result' in locals() else 'No response'}")
            # Return default structure on error
            return {
                "personal_info": {
                    "name": "",
                    "email": "",
                    "phone": "",
                    "location": "",
                    "linkedin": "",
                    "portfolio": "",
                    "github": ""
                },
                "summary": "",
                "skills": {
                    "technical": [],
                    "soft": [],
                    "languages": [],
                    "tools": [],
                    "frameworks": [],
                    "methodologies": [],
                    "domain_knowledge": []
                },
                "experience": [],
                "education": [],
                "certifications": [],
                "projects": [],
                "publications": [],
                "awards": [],
                "languages": [],
                "volunteer_experience": [],
                "keywords": [],
                "strengths": [],
                "achievements": [],
                "skill_proficiency": [],
                "experience_summary": {
                    "total_years": "",
                    "industries": [],
                    "company_sizes": [],
                    "roles": []
                },
                "gaps": [],
                "ats_score": {
                    "formatting": "",
                    "keyword_optimization": "",
                    "content_quality": "",
                    "overall": ""
                },
                "improvement_suggestions": [],
                "professional_snapshot": "",
                "unique_selling_points": [],
                "career_narrative": "",
                "technical_expertise_summary": "",
                "soft_skills_summary": "",
                "achievement_highlights": "",
                "potential_roles": [],
                "interview_talking_points": []
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
            max_output_tokens=4000  # Increased from 1000 to handle larger responses
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
        """Match resume skills with job requirements with enhanced detail"""
        if not self.job_analysis or not self.resume_analysis:
            raise ValueError("Job description and resume must be processed before matching skills")
        
        try:
            # Set up a specific LLM for skill matching with higher token limits
            skill_match_llm = GoogleGenerativeAI(
                model="gemini-pro",
                google_api_key=self.api_key,
                temperature=0.2,  # Lower temperature for more consistent, factual responses
                max_output_tokens=8000  # Much higher limit for the complex skill matching task
            )
            
            prompt = PromptTemplate(
                template="""Perform a comprehensive analysis comparing the candidate's resume with the job description to identify matches, gaps, and provide strategic insights.

                Resume Information:
                {resume_info}
                
                Job Description:
                {job_description}
                
                Job Analysis:
                {job_analysis}
                
                STRICT OUTPUT FORMAT (Return ONLY this JSON object):
                {{
                    "overall_match": {{
                        "percentage": 85,
                        "assessment": "Brief assessment of overall match",
                        "recommendation": "Overall recommendation"
                    }},
                    "skill_match": {{
                        "matching_skills": [
                            {{
                                "skill": "skill name",
                                "resume_evidence": "where/how mentioned in resume",
                                "job_importance": "high/medium/low",
                                "proficiency_level": "beginner/intermediate/advanced/expert"
                            }}
                        ],
                        "missing_skills": [
                            {{
                                "skill": "skill name",
                                "importance": "high/medium/low",
                                "alternative_skills": ["skill1", "skill2"],
                                "acquisition_difficulty": "easy/moderate/difficult",
                                "acquisition_suggestion": "How to acquire this skill"
                            }}
                        ],
                        "transferable_skills": [
                            {{
                                "resume_skill": "skill in resume",
                                "job_skill": "related skill in job",
                                "transferability": "high/medium/low",
                                "explanation": "Why/how this skill is transferable"
                            }}
                        ]
                    }},
                    "experience_match": {{
                        "years_required": "Years required in job",
                        "years_candidate": "Years candidate has",
                        "match_assessment": "Assessment of experience match",
                        "relevant_experiences": [
                            {{
                                "job_requirement": "Specific requirement",
                                "candidate_experience": "Relevant experience from resume",
                                "match_level": "high/medium/low"
                            }}
                        ]
                    }},
                    "education_match": {{
                        "match_level": "high/medium/low",
                        "assessment": "Assessment of education match",
                        "gaps": ["gap1", "gap2"]
                    }},
                    "keyword_match": {{
                        "matching_keywords": [
                            {{
                                "keyword": "keyword",
                                "job_importance": "high/medium/low",
                                "resume_context": "How it appears in resume"
                            }}
                        ],
                        "missing_keywords": [
                            {{
                                "keyword": "keyword",
                                "importance": "high/medium/low",
                                "alternative_terms": ["term1", "term2"]
                            }}
                        ]
                    }},
                    "strengths_for_role": [
                        {{
                            "strength": "Candidate strength",
                            "relevance": "Why this is relevant to the job",
                            "evidence": "Evidence from resume",
                            "impact_potential": "Potential impact in this role"
                        }}
                    ],
                    "improvement_areas": [
                        {{
                            "area": "Area to improve",
                            "importance": "high/medium/low",
                            "suggestion": "How to address this",
                            "timeframe": "short-term/medium-term/long-term"
                        }}
                    ],
                    "resume_enhancement_suggestions": [
                        {{
                            "section": "Section name",
                            "suggestion": "What to add/modify",
                            "reason": "Why this would help",
                            "example": "Example of how to phrase it"
                        }}
                    ],
                    "application_strategy": {{
                        "cover_letter_focus_points": ["point1", "point2"],
                        "skills_to_emphasize": ["skill1", "skill2"],
                        "experiences_to_highlight": ["experience1", "experience2"],
                        "potential_questions": [
                            {{
                                "question": "Likely interview question",
                                "strategy": "How to approach answering",
                                "key_points": ["point1", "point2"]
                            }}
                        ]
                    }},
                    "cultural_fit": {{
                        "assessment": "Assessment of cultural fit",
                        "matching_values": ["value1", "value2"],
                        "potential_challenges": ["challenge1", "challenge2"]
                    }}
                }}

                STRICT RULES:
                1. Return ONLY the JSON object, no other text
                2. ALL keys must be present in the response
                3. Be extremely specific and detailed in your analysis
                4. Base all assessments on concrete evidence from both the resume and job description
                5. Provide actionable insights and practical suggestions
                6. Do not include any explanatory text or markdown
                """,
                input_variables=["resume_info", "job_description", "job_analysis"]
            )

            # Format the resume info and job analysis as readable text
            resume_info = json.dumps(self.resume_analysis, indent=2)
            job_analysis = json.dumps(self.job_analysis, indent=2)
            
            # Use the specialized LLM for skill matching
            chain = LLMChain(llm=skill_match_llm, prompt=prompt)
            
            print("\n⏳ Performing detailed skill matching analysis... This may take a minute...")
            
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
            else:
                logger.error("Could not find valid JSON in the response")
                logger.error(f"Raw response: {response_text}")
                raise ValueError("Invalid response format from LLM")
            
            # Parse and validate response
            try:
                self.skill_match_analysis = json.loads(response_text)
                logger.info("Successfully parsed skill match analysis")
                return self.skill_match_analysis
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}")
                logger.error(f"Response text: {response_text}")
                raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error matching skills with job: {str(e)}")
            if 'result' in locals():
                logger.error(f"Raw response: {result['text']}")
            
            # Return default structure on error
            self.skill_match_analysis = {
                "overall_match": {
                    "percentage": 0,
                    "assessment": "Error occurred during analysis. Please try again.",
                    "recommendation": "Check logs for details and try again."
                },
                "skill_match": {
                    "matching_skills": [],
                    "missing_skills": [],
                    "transferable_skills": []
                },
                "experience_match": {
                    "years_required": "",
                    "years_candidate": "",
                    "match_assessment": "",
                    "relevant_experiences": []
                },
                "education_match": {
                    "match_level": "",
                    "assessment": "",
                    "gaps": []
                },
                "keyword_match": {
                    "matching_keywords": [],
                    "missing_keywords": []
                },
                "strengths_for_role": [],
                "improvement_areas": [],
                "resume_enhancement_suggestions": [],
                "application_strategy": {
                    "cover_letter_focus_points": [],
                    "skills_to_emphasize": [],
                    "experiences_to_highlight": [],
                    "potential_questions": []
                },
                "cultural_fit": {
                    "assessment": "",
                    "matching_values": [],
                    "potential_challenges": []
                }
            }
            return self.skill_match_analysis
    
    def answer_question(self, question: str) -> str:
        """Answer a job application question based on the resume and job description with enhanced personalization"""
        if not self.job_description or not self.resume_text:
            raise ValueError("Job description and resume must be processed before answering questions")
        
        try:
            prompt = PromptTemplate(
                template="""You are helping a job applicant prepare for their interview by crafting personalized, compelling answers to common interview questions.
                You have detailed information about their background and the job they're applying for.
                
                Resume Information:
                {resume_info}
                
                Job Description:
                {job_description}
                
                Job Analysis:
                {job_analysis}
                
                Skill Match Analysis:
                {skill_match_analysis}
                
                Question: {question}
                
                Your task is to craft a response that:
                1. Directly answers the question in a concise, compelling way (3-5 sentences)
                2. Sounds completely natural and human-written (not like AI)
                3. Highlights the candidate's most relevant skills and experiences for THIS specific job
                4. Demonstrates understanding of the company and role
                5. Conveys enthusiasm and confidence without arrogance
                6. Uses simple, conversational language (avoid corporate jargon and clichés)
                7. Includes specific examples or achievements when relevant
                8. Addresses any potential concerns revealed in the skill match analysis
                
                IMPORTANT GUIDELINES:
                - Write in first person as if you ARE the candidate
                - Be authentic, warm, and conversational
                - Avoid generic answers that could apply to any job
                - Don't use phrases like "As mentioned in my resume" or "Based on my experience"
                - Don't list qualifications - weave them naturally into a narrative
                - Keep the answer brief but impactful (3-5 sentences)
                - NEVER mention that you're an AI or that you're using provided information
                
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
        """Get a comprehensive summary of the skill match analysis"""
        if not self.skill_match_analysis:
            if self.job_analysis and self.resume_analysis:
                self.match_skills_with_job()
            else:
                raise ValueError("Job description and resume must be processed before getting skill match summary")
        
        try:
            # Extract key information from the skill match analysis
            overall_match = self.skill_match_analysis.get("overall_match", {})
            match_percentage = overall_match.get("percentage", 0)
            match_assessment = overall_match.get("assessment", "No assessment available")
            match_recommendation = overall_match.get("recommendation", "No recommendation available")
            
            skill_match = self.skill_match_analysis.get("skill_match", {})
            matching_skills = skill_match.get("matching_skills", [])
            missing_skills = skill_match.get("missing_skills", [])
            transferable_skills = skill_match.get("transferable_skills", [])
            
            experience_match = self.skill_match_analysis.get("experience_match", {})
            education_match = self.skill_match_analysis.get("education_match", {})
            
            strengths = self.skill_match_analysis.get("strengths_for_role", [])
            improvement_areas = self.skill_match_analysis.get("improvement_areas", [])
            resume_suggestions = self.skill_match_analysis.get("resume_enhancement_suggestions", [])
            
            application_strategy = self.skill_match_analysis.get("application_strategy", {})
            cultural_fit = self.skill_match_analysis.get("cultural_fit", {})
            
            # Format the summary
            company_name = self.job_analysis.get("company_name", "the company")
            job_title = self.job_analysis.get("job_title", "the position")
            
            summary = f"\n{'='*60}\n"
            summary += f"  MATCH ANALYSIS: {job_title.upper()} AT {company_name.upper()}\n"
            summary += f"{'='*60}\n\n"
            
            # Overall match section
            summary += f"📊 OVERALL MATCH: {match_percentage}%\n"
            summary += f"{match_assessment}\n"
            summary += f"Recommendation: {match_recommendation}\n\n"
            
            # Skills section
            summary += f"🔍 SKILLS ANALYSIS\n{'-'*30}\n"
            
            # Matching skills
            summary += "🟢 Matching Skills:\n"
            if matching_skills:
                for skill in matching_skills[:5]:
                    skill_name = skill.get("skill", "")
                    importance = skill.get("job_importance", "").upper()
                    proficiency = skill.get("proficiency_level", "").title()
                    summary += f"  • {skill_name}"
                    if importance:
                        summary += f" (Importance: {importance}"
                        if proficiency:
                            summary += f", Your Level: {proficiency})"
                        else:
                            summary += ")"
                    summary += "\n"
                
                if len(matching_skills) > 5:
                    summary += f"    ...and {len(matching_skills) - 5} more matching skills\n"
            else:
                summary += "  No matching skills identified\n"
            
            # Missing skills
            summary += "\n🔴 Missing Skills:\n"
            if missing_skills:
                for skill in missing_skills[:5]:
                    skill_name = skill.get("skill", "")
                    importance = skill.get("importance", "").upper()
                    acquisition = skill.get("acquisition_difficulty", "").title()
                    summary += f"  • {skill_name}"
                    if importance:
                        summary += f" (Importance: {importance}"
                        if acquisition:
                            summary += f", Difficulty to Acquire: {acquisition})"
                        else:
                            summary += ")"
                    summary += "\n"
                    
                    if skill.get("alternative_skills"):
                        alternatives = ", ".join(skill.get("alternative_skills", []))
                        summary += f"    Your alternatives: {alternatives}\n"
                
                if len(missing_skills) > 5:
                    summary += f"    ...and {len(missing_skills) - 5} more missing skills\n"
            else:
                summary += "  No missing skills identified\n"
            
            # Transferable skills
            if transferable_skills:
                summary += "\n🔄 Transferable Skills:\n"
                for skill in transferable_skills[:3]:
                    resume_skill = skill.get("resume_skill", "")
                    job_skill = skill.get("job_skill", "")
                    transferability = skill.get("transferability", "").upper()
                    summary += f"  • {resume_skill} → {job_skill}"
                    if transferability:
                        summary += f" (Transferability: {transferability})"
                    summary += "\n"
                
                if len(transferable_skills) > 3:
                    summary += f"    ...and {len(transferable_skills) - 3} more transferable skills\n"
            
            # Experience and education
            summary += f"\n📈 EXPERIENCE & EDUCATION\n{'-'*30}\n"
            summary += f"Experience: {experience_match.get('match_assessment', 'No assessment available')}\n"
            summary += f"Education: {education_match.get('assessment', 'No assessment available')}\n"
            
            # Strengths and improvements
            summary += f"\n💪 KEY STRENGTHS FOR THIS ROLE\n{'-'*30}\n"
            if strengths:
                for strength in strengths[:3]:
                    strength_name = strength.get("strength", "")
                    relevance = strength.get("relevance", "")
                    summary += f"  • {strength_name}"
                    if relevance:
                        summary += f": {relevance}"
                    summary += "\n"
            else:
                summary += "  No specific strengths identified\n"
            
            summary += f"\n📝 AREAS FOR IMPROVEMENT\n{'-'*30}\n"
            if improvement_areas:
                for area in improvement_areas[:3]:
                    area_name = area.get("area", "")
                    importance = area.get("importance", "").upper()
                    suggestion = area.get("suggestion", "")
                    summary += f"  • {area_name}"
                    if importance:
                        summary += f" (Importance: {importance})"
                    summary += "\n"
                    if suggestion:
                        summary += f"    Suggestion: {suggestion}\n"
            else:
                summary += "  No specific improvement areas identified\n"
            
            # Resume enhancement
            if resume_suggestions:
                summary += f"\n📄 RESUME ENHANCEMENT SUGGESTIONS\n{'-'*30}\n"
                for suggestion in resume_suggestions[:3]:
                    section = suggestion.get("section", "")
                    suggestion_text = suggestion.get("suggestion", "")
                    reason = suggestion.get("reason", "")
                    summary += f"  • {section}: {suggestion_text}\n"
                    if reason:
                        summary += f"    Reason: {reason}\n"
            
            # Application strategy
            if application_strategy:
                summary += f"\n🎯 APPLICATION STRATEGY\n{'-'*30}\n"
                
                # Cover letter points
                cover_letter_points = application_strategy.get("cover_letter_focus_points", [])
                if cover_letter_points:
                    summary += "Cover Letter Focus Points:\n"
                    for point in cover_letter_points[:3]:
                        summary += f"  • {point}\n"
                
                # Skills to emphasize
                skills_to_emphasize = application_strategy.get("skills_to_emphasize", [])
                if skills_to_emphasize:
                    summary += "\nSkills to Emphasize:\n"
                    summary += f"  {', '.join(skills_to_emphasize[:5])}"
                    if len(skills_to_emphasize) > 5:
                        summary += f" and {len(skills_to_emphasize) - 5} more"
                    summary += "\n"
            
            # Cultural fit
            if cultural_fit:
                summary += f"\n🤝 CULTURAL FIT\n{'-'*30}\n"
                summary += f"{cultural_fit.get('assessment', 'No assessment available')}\n"
                
                matching_values = cultural_fit.get("matching_values", [])
                if matching_values:
                    summary += "\nMatching Values:\n"
                    summary += f"  {', '.join(matching_values[:5])}"
                    if len(matching_values) > 5:
                        summary += f" and {len(matching_values) - 5} more"
                    summary += "\n"
            
            # Potential interview questions
            potential_questions = application_strategy.get("potential_questions", []) if application_strategy else []
            if potential_questions:
                summary += f"\n❓ POTENTIAL INTERVIEW QUESTIONS\n{'-'*30}\n"
                for q in potential_questions[:3]:
                    question = q.get("question", "")
                    summary += f"  • {question}\n"
            
            summary += f"\n{'='*60}\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting skill match summary: {str(e)}")
            # Return a basic summary if there's an error
            return f"""
{'='*60}
  SKILL MATCH ANALYSIS ERROR
{'='*60}

⚠️ There was an error generating the detailed skill match summary: {str(e)}

Basic information:
- Overall match: {self.skill_match_analysis.get('overall_match', {}).get('percentage', 0)}%
- Matching skills: {len(self.skill_match_analysis.get('skill_match', {}).get('matching_skills', []))}
- Missing skills: {len(self.skill_match_analysis.get('skill_match', {}).get('missing_skills', []))}

Please check the logs for more details.
{'='*60}
"""

def main():
    GEMINI_API_KEY = "AIzaSyCkb4a_yq_Iviefm_FJHQr40ukm7BqlLww"
    
    print("\n" + "="*70)
    print(" "*20 + "JOB APPLICATION ASSISTANT")
    print("="*70)
    print("\nThis AI-powered tool helps you prepare for job applications by analyzing job descriptions")
    print("and your resume, then helping you craft perfect answers to common interview questions.")
    
    agent = JobApplicationAgent(GEMINI_API_KEY)
    
    # Step 1: Process resume
    resume_processed = False
    while not resume_processed:
        print("\n" + "="*70)
        print(" "*20 + "STEP 1: UPLOAD YOUR RESUME")
        print("="*70)
        resume_path = input("\nEnter the path to your resume PDF file: ").strip()
        
        try:
            with open(resume_path, 'rb') as resume_file:
                print("\n⏳ Processing your resume... Please wait...")
                print("   This may take a minute as we perform a comprehensive analysis...")
                resume_analysis = agent.process_resume(resume_file)
                
                print("\n✅ Resume processed successfully!")
                
                # Display personal info
                name = resume_analysis['personal_info']['name']
                print(f"\n👤 {name}'s Professional Profile")
                print("-"*50)
                
                # Display professional snapshot
                if resume_analysis.get('professional_snapshot'):
                    print(f"\n📊 Professional Snapshot:")
                    print(f"  {resume_analysis['professional_snapshot']}")
                
                # Display technical expertise summary
                if resume_analysis.get('technical_expertise_summary'):
                    print(f"\n💻 Technical Expertise:")
                    print(f"  {resume_analysis['technical_expertise_summary']}")
                
                # Display technical skills
                print("\n🔧 Key Technical Skills:")
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
                if resume_analysis.get('experience_summary', {}).get('total_years'):
                    print(f"\n⏱️ Experience: {resume_analysis['experience_summary']['total_years']} of professional experience")
                
                print("\n💼 Most Recent Positions:")
                for i, exp in enumerate(resume_analysis['experience'][:2]):
                    print(f"  • {exp['title']} at {exp['company']} ({exp['duration']})")
                    if exp.get('impact'):
                        print(f"    Impact: {exp['impact']}")
                
                if len(resume_analysis['experience']) > 2:
                    print(f"  ...and {len(resume_analysis['experience']) - 2} more positions")
                
                # Display unique selling points
                if resume_analysis.get('unique_selling_points'):
                    print("\n🌟 Unique Selling Points:")
                    for i, point in enumerate(resume_analysis['unique_selling_points'][:3]):
                        print(f"  • {point}")
                
                # Display ATS score if available
                if resume_analysis.get('ats_score', {}).get('overall'):
                    print(f"\n📈 ATS Optimization Score: {resume_analysis['ats_score']['overall']}/10")
                
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
        print("\n" + "="*70)
        print(" "*20 + "STEP 2: ENTER JOB POSTING URL")
        print("="*70)
        job_url = input("\nEnter the job posting URL: ").strip()
        
        if not job_url.startswith(('http://', 'https://')):
            print("Invalid URL format. Please include http:// or https://")
            continue
        
        try:
            print("\n⏳ Scraping and analyzing job description... Please wait...")
            print("   This may take a minute as we perform a comprehensive analysis...")
            job_analysis = agent.process_job_url(job_url)
            
            print("\n✅ Job description processed successfully!")
            
            # Display job and company info
            company_name = job_analysis.get('company_name', 'Company')
            job_title = job_analysis.get('job_title', 'Position')
            job_location = job_analysis.get('job_location', 'Location not specified')
            
            print(f"\n🏢 {job_title} at {company_name}")
            print(f"📍 {job_location}")
            print("-"*50)
            
            # Display executive summary
            if job_analysis.get('executive_summary'):
                print(f"\n📋 Position Overview:")
                print(f"  {job_analysis['executive_summary']}")
            
            # Display company overview
            if job_analysis.get('company_overview'):
                print(f"\n🏢 Company Overview:")
                print(f"  {job_analysis['company_overview']}")
            
            # Display role importance
            if job_analysis.get('role_importance'):
                print(f"\n🎯 Role Importance:")
                print(f"  {job_analysis['role_importance']}")
            
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
            
            # Display key qualifications summary
            if job_analysis.get('key_qualifications_summary'):
                print(f"\n🔑 Key Qualifications Summary:")
                print(f"  {job_analysis['key_qualifications_summary']}")
            
            # Display application advice
            if job_analysis.get('application_advice'):
                print(f"\n💡 Application Advice:")
                print(f"  {job_analysis['application_advice']}")
            
            job_processed = True
        
        except Exception as e:
            print(f"\n❌ Error processing job URL: {str(e)}")
            retry = input("Would you like to try again? (y/n): ").strip().lower()
            if retry != 'y':
                print("Exiting program.")
                return
    
    # Step 3: Show skill match analysis
    try:
        print("\n" + "="*70)
        print(" "*20 + "STEP 3: SKILL MATCH ANALYSIS")
        print("="*70)
        
        print("\n⏳ Analyzing skill match between your resume and the job requirements...")
        print("   This may take a minute as we perform a comprehensive analysis...")
        
        # Check if we need to perform skill matching
        if not agent.skill_match_analysis:
            try:
                agent.match_skills_with_job()
            except Exception as e:
                print(f"\n⚠️ Initial skill matching attempt failed: {str(e)}")
                print("   Retrying with simplified analysis...")
                
                # If the first attempt fails, try again with a simpler approach
                try:
                    # Set up a simpler LLM for skill matching
                    skill_match_llm = GoogleGenerativeAI(
                        model="gemini-pro",
                        google_api_key=agent.api_key,
                        temperature=0.1,
                        max_output_tokens=4000
                    )
                    
                    # Create a simpler prompt
                    prompt = PromptTemplate(
                        template="""Compare the candidate's resume with the job description and provide a basic skill match analysis.
                        
                        Resume Information:
                        {resume_info}
                        
                        Job Description:
                        {job_description}
                        
                        Job Analysis:
                        {job_analysis}
                        
                        Provide a JSON response with the following structure:
                        {
                            "overall_match": {
                                "percentage": 75,
                                "assessment": "Brief assessment of overall match",
                                "recommendation": "Overall recommendation"
                            },
                            "skill_match": {
                                "matching_skills": [
                                    {
                                        "skill": "skill name",
                                        "job_importance": "high/medium/low",
                                        "proficiency_level": "beginner/intermediate/advanced/expert"
                                    }
                                ],
                                "missing_skills": [
                                    {
                                        "skill": "skill name",
                                        "importance": "high/medium/low"
                                    }
                                ]
                            },
                            "experience_match": {
                                "match_assessment": "Assessment of experience match"
                            },
                            "education_match": {
                                "assessment": "Assessment of education match"
                            },
                            "strengths_for_role": [
                                {
                                    "strength": "Candidate strength",
                                    "relevance": "Why this is relevant to the job"
                                }
                            ],
                            "improvement_areas": [
                                {
                                    "area": "Area to improve",
                                    "importance": "high/medium/low",
                                    "suggestion": "How to address this"
                                }
                            ]
                        }
                        
                        Return ONLY the JSON object, no other text.
                        """,
                        input_variables=["resume_info", "job_description", "job_analysis"]
                    )
                    
                    # Format the resume info and job analysis as readable text
                    resume_info = json.dumps(agent.resume_analysis, indent=2)
                    job_analysis = json.dumps(agent.job_analysis, indent=2)
                    
                    chain = LLMChain(llm=skill_match_llm, prompt=prompt)
                    result = chain.invoke({
                        "resume_info": resume_info,
                        "job_description": agent.job_description,
                        "job_analysis": job_analysis
                    })
                    
                    # Clean and parse the response
                    response_text = result['text'].strip()
                    response_text = response_text.replace('```json', '').replace('```', '')
                    
                    # Find the JSON object
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    if start_idx != -1 and end_idx != -1:
                        response_text = response_text[start_idx:end_idx]
                    
                    # Parse the response
                    agent.skill_match_analysis = json.loads(response_text)
                    
                except Exception as e2:
                    print(f"\n❌ Simplified skill matching also failed: {str(e2)}")
                    print("   Proceeding with basic analysis...")
                    
                    # If all else fails, create a basic analysis
                    agent.skill_match_analysis = {
                        "overall_match": {
                            "percentage": 50,
                            "assessment": "Basic analysis based on keyword matching.",
                            "recommendation": "Review the job description and resume manually for a more accurate assessment."
                        },
                        "skill_match": {
                            "matching_skills": [],
                            "missing_skills": []
                        }
                    }
                    
                    # Perform basic keyword matching
                    resume_skills = []
                    for skill_category in agent.resume_analysis.get("skills", {}).values():
                        if isinstance(skill_category, list):
                            resume_skills.extend(skill_category)
                    
                    job_skills = agent.job_analysis.get("technical_skills", []) + agent.job_analysis.get("soft_skills", [])
                    
                    # Find matching skills
                    for job_skill in job_skills:
                        for resume_skill in resume_skills:
                            if job_skill.lower() in resume_skill.lower() or resume_skill.lower() in job_skill.lower():
                                agent.skill_match_analysis["skill_match"]["matching_skills"].append({
                                    "skill": job_skill,
                                    "job_importance": "medium",
                                    "proficiency_level": "intermediate"
                                })
                                break
                    
                    # Find missing skills
                    for job_skill in job_skills:
                        if not any(job_skill.lower() in resume_skill.lower() or resume_skill.lower() in job_skill.lower() for resume_skill in resume_skills):
                            agent.skill_match_analysis["skill_match"]["missing_skills"].append({
                                "skill": job_skill,
                                "importance": "medium"
                            })
        
        # Get and display the skill match summary
        skill_match_summary = agent.get_skill_match_summary()
        print(skill_match_summary)
        
    except Exception as e:
        print(f"\n❌ Error generating skill match analysis: {str(e)}")
        print("   Continuing to the next step...")
    
    # Step 4: Answer questions
    print("\n" + "="*70)
    print(" "*20 + "STEP 4: INTERVIEW QUESTION ASSISTANCE")
    print("="*70)
    print("\nYou can now ask for help with common interview questions.")
    print("I'll craft personalized answers based on your resume and the job description.")
    print("Type 'exit' to quit the program.")
    
    # Get potential questions from the skill match analysis
    potential_questions = []
    if agent.skill_match_analysis and agent.skill_match_analysis.get('application_strategy', {}).get('potential_questions'):
        potential_questions = [q.get('question') for q in agent.skill_match_analysis['application_strategy']['potential_questions'] if q.get('question')]
    
    # If no potential questions found, use default questions
    if not potential_questions:
        potential_questions = [
            "Why am I suitable for this role?",
            "Why do I want to join this company?",
            "How do my skills align with the company's goals?",
            "What relevant experience do I have for this position?",
            "What makes me stand out from other candidates?"
        ]
    
    print("\n💬 Suggested questions:")
    for i, question in enumerate(potential_questions[:5], 1):
        print(f"  {i}. {question}")
    
    while True:
        print("\n" + "-"*70)
        question = input("\nEnter your question (or 'exit' to quit): ").strip()
        
        if question.lower() == 'exit':
            print("\nThank you for using the Job Application Assistant. Good luck with your application!")
            break
        
        # Check if user entered a number corresponding to a suggested question
        try:
            q_num = int(question)
            if 1 <= q_num <= len(potential_questions[:5]):
                question = potential_questions[q_num-1]
                print(f"\nSelected question: {question}")
        except ValueError:
            pass
        
        if not question:
            continue
        
        print("\n⏳ Generating answer... Please wait...")
        answer = agent.answer_question(question)
        
        print("\n🔹 Suggested Answer:")
        print(answer)
        
        feedback = input("\nWas this answer helpful? (y/n): ").strip().lower()
        if feedback == 'n':
            print("\nI'll try to improve my answers. Please provide more specific questions for better results.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc() 