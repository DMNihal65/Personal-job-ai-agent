import unittest
import os
import io
from unittest.mock import patch, MagicMock
from job_application_agent import JobApplicationAgent, EnhancedJobScraper, ResumeParser

class TestJobApplicationAgent(unittest.TestCase):
    """Test cases for the JobApplicationAgent class"""
    
    def setUp(self):
        """Set up test environment"""
        # Use a test API key (this won't be used in mocked tests)
        self.api_key = "test_api_key"
        
        # Sample job description and resume text for testing
        self.job_description = """
        Software Engineer at TechCorp
        
        We are looking for a Software Engineer with 3+ years of experience in Python and JavaScript.
        The ideal candidate will have experience with web development frameworks like React and Django.
        
        Responsibilities:
        - Develop and maintain web applications
        - Collaborate with cross-functional teams
        - Write clean, maintainable code
        
        Requirements:
        - Bachelor's degree in Computer Science or related field
        - 3+ years of experience in software development
        - Proficiency in Python and JavaScript
        - Experience with React and Django
        - Strong problem-solving skills
        """
        
        self.resume_text = """
        John Doe
        Software Developer
        john.doe@example.com
        (123) 456-7890
        
        Summary:
        Experienced software developer with 4 years of experience in web development.
        Proficient in Python, JavaScript, and various frameworks.
        
        Experience:
        Software Developer, ABC Tech (2020-Present)
        - Developed web applications using Python and Django
        - Implemented front-end features using React
        - Collaborated with cross-functional teams
        
        Junior Developer, XYZ Corp (2018-2020)
        - Assisted in developing web applications
        - Wrote unit tests for existing code
        
        Education:
        Bachelor of Science in Computer Science, University of Technology (2018)
        
        Skills:
        - Python, JavaScript, HTML, CSS
        - Django, React, Flask
        - Git, Docker, AWS
        - Problem-solving, Communication
        """
    
    @patch('job_application_agent.LLMChain')
    @patch('job_application_agent.WebDriverWait')
    @patch('job_application_agent.Service')
    @patch('job_application_agent.webdriver.Chrome')
    def test_process_job_url(self, mock_chrome, mock_service, mock_wait, mock_llm_chain):
        """Test processing a job URL"""
        # Mock the Chrome driver
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.page_source = "<html><body><div class='job-description'>Test Job Description</div></body></html>"
        
        # Mock LLMChain
        mock_chain = MagicMock()
        mock_llm_chain.return_value = mock_chain
        mock_chain.invoke.return_value = {'text': '{"company_name": "TechCorp", "job_title": "Software Engineer"}'}
        
        # Create agent
        agent = JobApplicationAgent(self.api_key)
        
        # Process job URL
        result = agent.process_job_url("https://example.com/job")
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result.get("company_name"), "TechCorp")
        self.assertEqual(result.get("job_title"), "Software Engineer")
    
    @patch('job_application_agent.LLMChain')
    @patch('job_application_agent.PyPDF2.PdfReader')
    def test_process_resume(self, mock_pdf_reader, mock_llm_chain):
        """Test processing a resume"""
        # Mock PDF reader
        mock_pdf = MagicMock()
        mock_pdf_reader.return_value = mock_pdf
        mock_page = MagicMock()
        mock_page.extract_text.return_value = self.resume_text
        mock_pdf.pages = [mock_page]
        
        # Mock LLMChain
        mock_chain = MagicMock()
        mock_llm_chain.return_value = mock_chain
        mock_chain.invoke.return_value = {'text': '{"personal_info": {"name": "John Doe"}, "skills": {"technical": ["Python", "JavaScript"]}}'}
        
        # Create agent
        agent = JobApplicationAgent(self.api_key)
        
        # Process resume
        with open("dummy_path", "rb") as f:
            result = agent.process_resume(f)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result.get("personal_info", {}).get("name"), "John Doe")
        self.assertIn("Python", result.get("skills", {}).get("technical", []))
    
    @patch('job_application_agent.LLMChain')
    def test_match_skills_with_job(self, mock_llm_chain):
        """Test matching skills with job"""
        # Mock LLMChain
        mock_chain = MagicMock()
        mock_llm_chain.return_value = mock_chain
        mock_chain.invoke.return_value = {'text': '{"overall_match": {"percentage": 85}, "skill_match": {"matching_skills": [{"skill": "Python"}]}}'}
        
        # Create agent
        agent = JobApplicationAgent(self.api_key)
        
        # Set up mock data
        agent.job_description = self.job_description
        agent.job_analysis = {"technical_skills": ["Python", "JavaScript"]}
        agent.resume_analysis = {"skills": {"technical": ["Python", "HTML"]}}
        
        # Match skills
        result = agent.match_skills_with_job()
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result.get("overall_match", {}).get("percentage"), 85)
        self.assertIn("Python", [skill.get("skill") for skill in result.get("skill_match", {}).get("matching_skills", [])])
    
    @patch('job_application_agent.LLMChain')
    def test_answer_question(self, mock_llm_chain):
        """Test answering a question"""
        # Mock LLMChain
        mock_chain = MagicMock()
        mock_llm_chain.return_value = mock_chain
        mock_chain.invoke.return_value = {'text': 'I am a good fit for this role because of my Python experience.'}
        
        # Create agent
        agent = JobApplicationAgent(self.api_key)
        
        # Set up mock data
        agent.job_description = self.job_description
        agent.job_analysis = {"technical_skills": ["Python", "JavaScript"]}
        agent.resume_text = self.resume_text
        agent.resume_analysis = {"skills": {"technical": ["Python", "HTML"]}}
        agent.skill_match_analysis = {"overall_match": {"percentage": 85}}
        
        # Answer question
        result = agent.answer_question("Why am I suitable for this role?")
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIn("Python", result)

if __name__ == '__main__':
    unittest.main() 