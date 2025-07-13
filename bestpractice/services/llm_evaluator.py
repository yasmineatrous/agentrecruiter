import os
import json
import aiohttp
from typing import Dict, Any, List
from bestpractice.config import settings

class LLMEvaluator:
    """Service for LLM-based evaluation using Mistral API"""
    
    def __init__(self):
        self.api_key = settings.MISTRAL_API_KEY
        self.base_url = "https://api.mistral.ai/v1"
        self.model = settings.MISTRAL_MODEL
    
    async def evaluate_candidate_fit(
        self,
        candidate_profile: Dict[str, Any],
        job_requirements: List[str],
        relevant_resume_chunks: List[str],
        job_description: str
    ) -> Dict[str, Any]:
        """
        Evaluate candidate fit using Mistral API
        
        Args:
            candidate_profile: Extracted candidate profile
            job_requirements: List of job requirements
            relevant_resume_chunks: Relevant resume sections
            job_description: Full job description
            
        Returns:
            Dict containing evaluation results
        """
        
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY not found in environment variables")
        
        # Prepare the evaluation prompt
        prompt = self._create_evaluation_prompt(
            candidate_profile,
            job_requirements,
            relevant_resume_chunks,
            job_description
        )
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json',
                }
                
                payload = {
                    'model': self.model,
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You are an expert HR professional and technical recruiter. Your task is to evaluate candidate-job fit based on resume and job description. Provide structured, objective analysis.'
                        },
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ],
                    'temperature': 0.3,
                    'max_tokens': 2000,
                    'response_format': {'type': 'json_object'}
                }
                
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Mistral API error: {response.status} - {error_text}")
                    
                    result = await response.json()
                    
                    # Extract the response content
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content']
                        
                        try:
                            # Parse JSON response
                            evaluation = json.loads(content)
                            return evaluation
                        except json.JSONDecodeError:
                            # Fallback if JSON parsing fails
                            return self._parse_text_response(content)
                    
                    else:
                        raise Exception("No response from Mistral API")
                        
        except Exception as e:
            print(f"Error calling Mistral API: {str(e)}")
            # Return a fallback evaluation
            return self._create_fallback_evaluation(candidate_profile, job_requirements)
    
    def _create_evaluation_prompt(
        self,
        candidate_profile: Dict[str, Any],
        job_requirements: List[str],
        relevant_resume_chunks: List[str],
        job_description: str
    ) -> str:
        """Create structured evaluation prompt"""
        
        prompt = f"""
Please evaluate this candidate's fit for the job position. Analyze the candidate's profile against the job requirements and provide a structured evaluation.

**Job Description:**
{job_description[:2000]}...

**Job Requirements:**
{json.dumps(job_requirements, indent=2)}

**Candidate Profile:**
- Education: {candidate_profile.get('education', [])}
- Skills: {candidate_profile.get('skills', [])}
- Experience: {candidate_profile.get('experience', [])}
- Certifications: {candidate_profile.get('certifications', [])}
- Projects: {candidate_profile.get('projects', [])}

**Relevant Resume Sections:**
{' '.join(relevant_resume_chunks[:3])}

**Instructions:**
1. Evaluate the candidate's fit on a scale of 0-100%
2. Categorize the fit as "High Fit" (80-100%), "Moderate Fit" (50-79%), or "Low Fit" (0-49%)
3. For each job requirement, determine if the candidate meets it (true/false) with confidence level
4. Identify key strengths and areas for improvement
5. Provide hiring recommendations

**Required JSON Response Format:**
{{
    "fit_percentage": <number between 0-100>,
    "fit_score": "<High Fit|Moderate Fit|Low Fit>",
    "comparison_matrix": [
        {{
            "requirement": "<requirement text>",
            "match": <true/false>,
            "confidence": <0.0-1.0>,
            "explanation": "<detailed explanation>"
        }}
    ],
    "explanation": "<overall evaluation explanation>",
    "strengths": ["<strength 1>", "<strength 2>", ...],
    "areas_for_improvement": ["<area 1>", "<area 2>", ...],
    "recommendations": ["<recommendation 1>", "<recommendation 2>", ...]
}}

Provide your evaluation in valid JSON format only.
"""
        
        return prompt
    
    def _parse_text_response(self, content: str) -> Dict[str, Any]:
        """Parse text response if JSON parsing fails"""
        
        # Basic fallback parsing
        return {
            "fit_percentage": 50.0,
            "fit_score": "Moderate Fit",
            "comparison_matrix": [],
            "explanation": content[:500] + "..." if len(content) > 500 else content,
            "strengths": [],
            "areas_for_improvement": [],
            "recommendations": []
        }
    
    def _create_fallback_evaluation(
        self,
        candidate_profile: Dict[str, Any],
        job_requirements: List[str]
    ) -> Dict[str, Any]:
        """Create fallback evaluation when API fails"""
        
        # Simple rule-based evaluation
        skills = candidate_profile.get('skills', [])
        experience = candidate_profile.get('experience', [])
        
        comparison_matrix = []
        matches = 0
        
        for req in job_requirements:
            match = any(skill.lower() in req.lower() for skill in skills)
            comparison_matrix.append({
                "requirement": req,
                "match": match,
                "confidence": 0.7 if match else 0.3,
                "explanation": f"{'Found relevant skills' if match else 'No direct match found'} in candidate profile"
            })
            if match:
                matches += 1
        
        fit_percentage = (matches / len(job_requirements)) * 100 if job_requirements else 50
        
        if fit_percentage >= 80:
            fit_score = "High Fit"
        elif fit_percentage >= 50:
            fit_score = "Moderate Fit"
        else:
            fit_score = "Low Fit"
        
        return {
            "fit_percentage": fit_percentage,
            "fit_score": fit_score,
            "comparison_matrix": comparison_matrix,
            "explanation": f"Candidate matches {matches} out of {len(job_requirements)} requirements based on skills and experience.",
            "strengths": skills[:3],
            "areas_for_improvement": ["API evaluation unavailable - manual review recommended"],
            "recommendations": ["Conduct technical interview", "Verify experience claims"]
        }
    
    async def extract_job_requirements(self, job_description: str) -> List[str]:
        """
        Extract job requirements from job description
        
        Args:
            job_description: Full job description text
            
        Returns:
            List of extracted requirements
        """
        
        if not self.api_key:
            return self._extract_requirements_fallback(job_description)
        
        prompt = f"""
Extract the key job requirements from this job description. Focus on:
- Technical skills
- Educational requirements
- Experience requirements
- Certifications
- Soft skills
- Specific tools/technologies

Job Description:
{job_description[:3000]}...

Return a JSON array of requirement strings:
{{"requirements": ["requirement 1", "requirement 2", ...]}}
"""
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json',
                }
                
                payload = {
                    'model': self.model,
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You are an expert at extracting job requirements from job descriptions. Extract clear, specific requirements.'
                        },
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ],
                    'temperature': 0.1,
                    'max_tokens': 1000,
                    'response_format': {'type': 'json_object'}
                }
                
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        if 'choices' in result and len(result['choices']) > 0:
                            content = result['choices'][0]['message']['content']
                            
                            try:
                                parsed = json.loads(content)
                                return parsed.get('requirements', [])
                            except json.JSONDecodeError:
                                pass
                    
                    # Fallback if API call fails
                    return self._extract_requirements_fallback(job_description)
                    
        except Exception as e:
            print(f"Error extracting requirements: {str(e)}")
            return self._extract_requirements_fallback(job_description)
    
    def _extract_requirements_fallback(self, job_description: str) -> List[str]:
        """Fallback requirement extraction using comprehensive patterns"""
        
        requirements = []
        text = job_description.lower()
        
        # Comprehensive technical skills
        tech_skills = [
            # Programming Languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'swift', 'kotlin',
            'php', 'ruby', 'scala', 'r', 'matlab', 'perl', 'shell scripting', 'bash', 'powershell',
            # Web Technologies
            'react', 'angular', 'vue', 'node.js', 'express', 'fastapi', 'django', 'flask',
            'html', 'css', 'bootstrap', 'tailwind', 'sass', 'less', 'webpack', 'vite',
            'next.js', 'nuxt.js', 'svelte', 'jquery', 'redux', 'graphql', 'rest api',
            # Databases
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
            'oracle', 'sqlite', 'mariadb', 'dynamodb', 'neo4j', 'influxdb',
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible',
            'jenkins', 'gitlab ci', 'github actions', 'ci/cd', 'microservices',
            # AI/ML
            'machine learning', 'deep learning', 'ai', 'nlp', 'computer vision',
            'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy',
            # Tools & Platforms
            'git', 'github', 'gitlab', 'jira', 'confluence', 'slack', 'agile', 'scrum',
            # Mobile & Others
            'android', 'ios', 'react native', 'flutter', 'xamarin'
        ]
        
        # Extract technical skills requirements
        for skill in tech_skills:
            if skill in text:
                requirements.append(f"Experience with {skill.title()}")
        
        # Extract experience requirements using patterns
        import re
        
        # Years of experience patterns
        experience_patterns = [
            r'(\d+)\+?\s*(?:to\s+\d+\s*)?years?\s*(?:of\s*)?(?:experience|exp)',
            r'minimum\s*(?:of\s*)?(\d+)\s*years?',
            r'at\s*least\s*(\d+)\s*years?',
            r'(\d+)\s*years?\s*(?:minimum|min)',
            r'(\d+)\+\s*years?\s*(?:in|of|with)'
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, text)
            if matches:
                years = matches[0]
                requirements.append(f"Minimum {years} years of experience")
                break
        
        # Education requirements
        education_patterns = [
            r'bachelor(?:\'s)?\s*(?:degree)?\s*(?:in\s*)?([^\n,.;]+)',
            r'master(?:\'s)?\s*(?:degree)?\s*(?:in\s*)?([^\n,.;]+)',
            r'phd\s*(?:in\s*)?([^\n,.;]+)',
            r'degree\s*(?:in\s*)?([^\n,.;]+)',
            r'(?:bs|ba|ms|ma|phd)\s*(?:in\s*)?([^\n,.;]+)'
        ]
        
        for pattern in education_patterns:
            matches = re.findall(pattern, text)
            if matches:
                field = matches[0].strip()
                if field and len(field) < 50:
                    requirements.append(f"Education: {field.title()}")
                break
        
        # Certification requirements
        cert_patterns = [
            r'(aws|azure|gcp|google)\s*certified',
            r'(cissp|cisa|cism|pmp|scrum\s*master)',
            r'certified\s*(?:in\s*)?([^\n,.;]+)',
            r'certification\s*(?:in\s*)?([^\n,.;]+)'
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, str):
                    requirements.append(f"Certification: {match.title()}")
                elif isinstance(match, tuple):
                    cert_name = ' '.join([part for part in match if part])
                    requirements.append(f"Certification: {cert_name.title()}")
        
        # Soft skills and requirements
        soft_skills_patterns = [
            r'(?:strong|excellent|good)\s*(?:communication|leadership|problem[\s-]solving|analytical|teamwork|collaboration)',
            r'(?:ability|capable)\s*(?:to\s*)?([^\n,.;]+)',
            r'(?:experience|skilled|proficient)\s*(?:in\s*|with\s*)?([^\n,.;]+)',
            r'(?:knowledge|understanding)\s*(?:of\s*)?([^\n,.;]+)',
            r'(?:familiar|comfortable)\s*(?:with\s*)?([^\n,.;]+)'
        ]
        
        for pattern in soft_skills_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, str) and len(match.strip()) > 5 and len(match.strip()) < 100:
                    requirements.append(f"Requirement: {match.strip()}")
        
        # Extract bullet point requirements
        bullet_patterns = [
            r'[•·▪▫-]\s*([^\n\r]+)',
            r'^\s*[*]\s*([^\n\r]+)',
            r'^\s*\d+\.\s*([^\n\r]+)'
        ]
        
        for pattern in bullet_patterns:
            matches = re.findall(pattern, job_description, re.MULTILINE)
            for match in matches:
                match = match.strip()
                if len(match) > 15 and len(match) < 150:
                    # Check if it looks like a requirement
                    if any(keyword in match.lower() for keyword in ['experience', 'knowledge', 'skill', 'ability', 'proficient', 'familiar', 'required', 'must', 'should']):
                        requirements.append(f"Requirement: {match}")
        
        # Extract specific requirement sections
        section_patterns = [
            r'(?:requirements?|qualifications?|skills?|experience|responsibilities)[\s:]*([^\n\r]+)',
            r'(?:required|must\s*have|essential)[\s:]*([^\n\r]+)',
            r'(?:preferred|nice\s*to\s*have|bonus)[\s:]*([^\n\r]+)'
        ]
        
        for pattern in section_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                match = match.strip()
                if len(match) > 10 and len(match) < 200:
                    requirements.append(f"Requirement: {match}")
        
        # Remove duplicates and limit
        unique_requirements = []
        seen = set()
        for req in requirements:
            req_lower = req.lower()
            if req_lower not in seen:
                seen.add(req_lower)
                unique_requirements.append(req)
        
        return unique_requirements[:20]  # Increased limit to 20
