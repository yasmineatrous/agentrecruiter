import re
from typing import List, Dict, Any
import asyncio

class TextProcessor:
    """Utility class for text processing operations"""
    
    def __init__(self):
        self.chunk_size = 500
        self.chunk_overlap = 50
    
    async def chunk_resume(self, resume_text: str) -> List[str]:
        """
        Chunk resume text into semantic sections
        
        Args:
            resume_text: Full resume text
            
        Returns:
            List of text chunks
        """
        
        # Clean text
        cleaned_text = self._clean_text(resume_text)
        
        # Try to identify sections
        sections = self._identify_resume_sections(cleaned_text)
        
        if sections:
            # If sections identified, chunk each section
            chunks = []
            for section_name, section_text in sections.items():
                section_chunks = self._chunk_text(section_text, section_name)
                chunks.extend(section_chunks)
            return chunks
        else:
            # Fallback to simple chunking
            return self._chunk_text(cleaned_text, "resume")
    
    async def chunk_job_description(self, job_text: str) -> List[str]:
        """
        Chunk job description text
        
        Args:
            job_text: Full job description text
            
        Returns:
            List of text chunks
        """
        
        # Clean text
        cleaned_text = self._clean_text(job_text)
        
        # Try to identify sections
        sections = self._identify_job_sections(cleaned_text)
        
        if sections:
            # If sections identified, chunk each section
            chunks = []
            for section_name, section_text in sections.items():
                section_chunks = self._chunk_text(section_text, section_name)
                chunks.extend(section_chunks)
            return chunks
        else:
            # Fallback to simple chunking
            return self._chunk_text(cleaned_text, "job_description")
    
    async def extract_candidate_profile(self, resume_text: str) -> Dict[str, Any]:
        """
        Extract candidate profile information from resume
        
        Args:
            resume_text: Full resume text
            
        Returns:
            Dict containing extracted profile information
        """
        
        text = self._clean_text(resume_text)
        
        # Extract different sections
        education = self._extract_education(text)
        skills = self._extract_skills(text)
        experience = self._extract_experience(text)
        certifications = self._extract_certifications(text)
        projects = self._extract_projects(text)
        
        return {
            'education': education,
            'skills': skills,
            'experience': experience,
            'certifications': certifications,
            'projects': projects
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s\.\,\:\;\-\(\)\[\]\/\@\+\#\&\%\$]', '', text)
        
        # Normalize case for better processing
        return text.strip()
    
    def _identify_resume_sections(self, text: str) -> Dict[str, str]:
        """Identify and extract resume sections"""
        
        sections = {}
        
        # Common section headers
        section_patterns = {
            'education': r'(education|academic|qualifications|degrees?)',
            'experience': r'(experience|employment|work\s+history|career|professional)',
            'skills': r'(skills|competencies|technical|technologies|tools)',
            'projects': r'(projects|portfolio|achievements|accomplishments)',
            'certifications': r'(certifications?|certificates?|licenses?)',
            'summary': r'(summary|objective|profile|about)'
        }
        
        text_lower = text.lower()
        
        for section_name, pattern in section_patterns.items():
            # Find section start
            match = re.search(f'\\b{pattern}\\b', text_lower)
            if match:
                start_pos = match.start()
                
                # Find next section or end of text
                remaining_text = text_lower[start_pos:]
                next_section_match = None
                
                for other_pattern in section_patterns.values():
                    if other_pattern != pattern:
                        next_match = re.search(f'\\b{other_pattern}\\b', remaining_text[50:])
                        if next_match:
                            if next_section_match is None or next_match.start() < next_section_match.start():
                                next_section_match = next_match
                
                if next_section_match:
                    end_pos = start_pos + 50 + next_section_match.start()
                    section_text = text[start_pos:end_pos]
                else:
                    section_text = text[start_pos:]
                
                sections[section_name] = section_text.strip()
        
        return sections
    
    def _identify_job_sections(self, text: str) -> Dict[str, str]:
        """Identify and extract job description sections"""
        
        sections = {}
        
        # Common job section headers
        section_patterns = {
            'requirements': r'(requirements?|qualifications?|skills?|must\s+have)',
            'responsibilities': r'(responsibilities?|duties|role|what\s+you|you\s+will)',
            'benefits': r'(benefits?|perks?|compensation|salary|package)',
            'about': r'(about|company|organization|team|mission)',
            'preferred': r'(preferred|nice\s+to\s+have|bonus|plus)'
        }
        
        text_lower = text.lower()
        
        for section_name, pattern in section_patterns.items():
            match = re.search(f'\\b{pattern}\\b', text_lower)
            if match:
                start_pos = match.start()
                
                # Find next section or end of text
                remaining_text = text_lower[start_pos:]
                next_section_match = None
                
                for other_pattern in section_patterns.values():
                    if other_pattern != pattern:
                        next_match = re.search(f'\\b{other_pattern}\\b', remaining_text[50:])
                        if next_match:
                            if next_section_match is None or next_match.start() < next_section_match.start():
                                next_section_match = next_match
                
                if next_section_match:
                    end_pos = start_pos + 50 + next_section_match.start()
                    section_text = text[start_pos:end_pos]
                else:
                    section_text = text[start_pos:]
                
                sections[section_name] = section_text.strip()
        
        return sections
    
    def _chunk_text(self, text: str, section_name: str = "") -> List[str]:
        """Chunk text into smaller pieces"""
        
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        words = text.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            word_size = len(word) + 1  # +1 for space
            
            if current_size + word_size > self.chunk_size and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)
                
                # Start new chunk with overlap
                overlap_words = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                current_chunk = overlap_words + [word]
                current_size = sum(len(w) + 1 for w in current_chunk)
            else:
                current_chunk.append(word)
                current_size += word_size
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)
        
        return chunks
    
    def _extract_education(self, text: str) -> List[str]:
        """Extract education information"""
        
        education = []
        
        # Enhanced degree patterns with better capture groups
        degree_patterns = [
            r'(bachelor(?:\'s)?|master(?:\'s)?|phd|doctorate|associate|diploma|certificate)[\s\w]*(?:in|of)\s+([\w\s,]+?)(?=\.|,|\n|$)',
            r'(b\.?[sa]\.?|m\.?[sa]\.?|m\.?s\.?|ph\.?d\.?|b\.?eng\.?|m\.?eng\.?)[\s\w]*(?:in|of)\s+([\w\s,]+?)(?=\.|,|\n|$)',
            r'(university|college|institute|school)[\s\w]*(?:of|in)\s+([\w\s,]+?)(?=\.|,|\n|graduated|$)',
            r'graduated\s+from\s+([\w\s,]+?)(?=\.|,|\n|with|$)',
            r'degree\s+in\s+([\w\s,]+?)(?=\.|,|\n|from|$)',
            r'major\s+in\s+([\w\s,]+?)(?=\.|,|\n|from|$)',
            r'studied\s+([\w\s,]+?)(?=\.|,|\n|at|$)',
            r'gpa[\s:]*(\d+\.?\d*)\s*/?\s*(\d+\.?\d*)?',
            r'(cum\s+laude|magna\s+cum\s+laude|summa\s+cum\s+laude|honors?|dean\'s\s+list)'
        ]
        
        for pattern in degree_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Join non-empty parts of the tuple
                    education_item = ' '.join([part.strip() for part in match if part.strip()])
                else:
                    education_item = match.strip()
                
                if education_item and len(education_item) > 3:
                    education.append(education_item)
        
        # Also look for years/dates in education section
        education_section = self._find_section_text(text, 'education')
        if education_section:
            date_patterns = [
                r'(19|20)\d{2}[-\s]*(19|20)\d{2}',
                r'(19|20)\d{2}',
                r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(19|20)\d{2}'
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, education_section, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        date_str = ''.join(match)
                    else:
                        date_str = match
                    education.append(f"Year: {date_str}")
        
        return list(set(education))[:10]  # Increase limit
    
    def _find_section_text(self, text: str, section_name: str) -> str:
        """Find and extract text from a specific section"""
        
        section_patterns = {
            'education': r'education|academic|qualifications|degrees?',
            'experience': r'experience|employment|work\s+history|professional',
            'skills': r'skills|technologies|technical|competencies',
            'projects': r'projects?|portfolio|work\s+samples',
            'certifications': r'certifications?|licenses?|credentials'
        }
        
        pattern = section_patterns.get(section_name.lower(), section_name)
        
        # Find section start
        section_match = re.search(f'\\b{pattern}\\b', text, re.IGNORECASE)
        if not section_match:
            return ""
        
        start_pos = section_match.start()
        
        # Find next section or end
        remaining_text = text[start_pos + 100:]  # Skip current section header
        next_section_patterns = [
            r'\b(education|experience|skills|projects?|certifications?|summary|objective|contact|references?)\b'
        ]
        
        end_pos = len(text)
        for pattern in next_section_patterns:
            next_match = re.search(pattern, remaining_text, re.IGNORECASE)
            if next_match:
                end_pos = start_pos + 100 + next_match.start()
                break
        
        return text[start_pos:end_pos]
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from text"""
        
        skills = []
        
        # Get skills section specifically
        skills_section = self._find_section_text(text, 'skills')
        text_to_search = skills_section if skills_section else text
        
        # Expanded technical skills database
        tech_skills = [
            # Programming Languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'swift', 'kotlin',
            'php', 'ruby', 'scala', 'r', 'matlab', 'perl', 'shell', 'bash', 'powershell',
            # Web Technologies
            'react', 'angular', 'vue', 'nodejs', 'express', 'fastapi', 'django', 'flask',
            'html', 'css', 'bootstrap', 'tailwind', 'sass', 'less', 'webpack', 'vite',
            'next.js', 'nuxt.js', 'svelte', 'jquery', 'redux', 'mobx', 'graphql', 'rest api',
            # Databases
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
            'oracle', 'sqlite', 'mariadb', 'dynamodb', 'neo4j', 'influxdb',
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible',
            'jenkins', 'gitlab ci', 'github actions', 'ci/cd', 'vagrant', 'chef', 'puppet',
            # Tools & Platforms
            'git', 'github', 'gitlab', 'bitbucket', 'jira', 'confluence', 'slack',
            'visual studio', 'vs code', 'intellij', 'eclipse', 'pycharm',
            # AI/ML
            'machine learning', 'deep learning', 'ai', 'nlp', 'computer vision',
            'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy', 'matplotlib',
            'jupyter', 'keras', 'opencv', 'hugging face',
            # Operating Systems
            'linux', 'windows', 'macos', 'ubuntu', 'centos', 'debian', 'fedora',
            # Mobile Development
            'android', 'ios', 'react native', 'flutter', 'xamarin', 'ionic',
            # Testing
            'unit testing', 'integration testing', 'selenium', 'cypress', 'jest', 'mocha',
            'pytest', 'junit', 'testng', 'cucumber'
        ]
        
        text_lower = text_to_search.lower()
        
        # Direct skill matching
        for skill in tech_skills:
            if skill in text_lower:
                skills.append(skill.title())
        
        # Pattern-based skill extraction
        skill_patterns = [
            r'(?:proficient|skilled|experienced|expert)\s+(?:in|with)\s+([\w\s,]+?)(?=\.|,|\n|$)',
            r'(?:knowledge|experience)\s+(?:of|in|with)\s+([\w\s,]+?)(?=\.|,|\n|$)',
            r'(?:familiar|comfortable)\s+with\s+([\w\s,]+?)(?=\.|,|\n|$)',
            r'(?:using|worked with|utilized)\s+([\w\s,]+?)(?=\.|,|\n|$)',
            r'(?:languages?|technologies?|tools?|frameworks?|platforms?)[:\s]+([\w\s,/]+?)(?=\.|,|\n|$)',
            r'(?:including|such as)[:\s]+([\w\s,/]+?)(?=\.|,|\n|$)'
        ]
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, text_to_search, re.IGNORECASE)
            for match in matches:
                # Split by common delimiters
                skill_list = re.split(r'[,/|&;]', match)
                for skill in skill_list:
                    skill = skill.strip()
                    if skill and len(skill) > 2 and len(skill) < 50:
                        skills.append(skill.title())
        
        # Also extract from bullet points
        bullet_patterns = [
            r'[•·▪▫-]\s*([^\n\r]+)',
            r'^\s*[*-]\s*([^\n\r]+)',
        ]
        
        for pattern in bullet_patterns:
            matches = re.findall(pattern, text_to_search, re.MULTILINE)
            for match in matches:
                match = match.strip()
                if len(match) > 5 and len(match) < 100:
                    skills.append(match)
        
        return list(set(skills))[:20]  # Increased limit
    
    def _extract_experience(self, text: str) -> List[str]:
        """Extract work experience"""
        
        experience = []
        
        # Get experience section specifically
        experience_section = self._find_section_text(text, 'experience')
        text_to_search = experience_section if experience_section else text
        
        # Enhanced job title patterns
        job_title_patterns = [
            r'(software\s+engineer|senior\s+software\s+engineer|lead\s+software\s+engineer|principal\s+software\s+engineer)',
            r'(developer|web\s+developer|full\s+stack\s+developer|frontend\s+developer|backend\s+developer)',
            r'(architect|technical\s+architect|solution\s+architect|system\s+architect)',
            r'(manager|engineering\s+manager|project\s+manager|product\s+manager|team\s+lead)',
            r'(analyst|data\s+analyst|business\s+analyst|system\s+analyst)',
            r'(consultant|technical\s+consultant|solutions\s+consultant)',
            r'(specialist|technical\s+specialist|it\s+specialist)',
            r'(devops|sre|site\s+reliability\s+engineer|infrastructure\s+engineer)',
            r'(qa|quality\s+assurance|test\s+engineer|automation\s+engineer)',
            r'(data\s+scientist|machine\s+learning\s+engineer|ai\s+engineer)',
            r'(cto|cio|vp\s+engineering|director\s+of\s+engineering)',
            r'(intern|internship|graduate\s+trainee|junior|senior|lead|principal)'
        ]
        
        # Company and employment patterns
        company_patterns = [
            r'(?:at|@)\s+([A-Z][\w\s&.,]+?)(?:\s+\||,|\n|$)',
            r'(?:worked\s+at|employed\s+at|company:)\s+([A-Z][\w\s&.,]+?)(?:\s+\||,|\n|$)',
            r'([A-Z][\w\s&.,]+?)(?:\s+\-\s+[\w\s]+)?(?:\s+\||\n|$)',
            r'(?:^|\n)\s*([A-Z][\w\s&.,]+?)\s*(?:\-|\|)',
        ]
        
        # Duration patterns
        duration_patterns = [
            r'(\d+)\s+(?:years?|yrs?)',
            r'(\d+)\s+(?:months?|mos?)',
            r'(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}',
            r'(19|20)\d{2}\s*[-–]\s*(?:present|current|now)',
            r'(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+(19|20)\d{2}'
        ]
        
        # Extract job titles
        for pattern in job_title_patterns:
            matches = re.findall(pattern, text_to_search, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str):
                    experience.append(f"Role: {match.title()}")
        
        # Extract companies
        for pattern in company_patterns:
            matches = re.findall(pattern, text_to_search, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str) and len(match.strip()) > 2:
                    company = match.strip()
                    if len(company) < 50:  # Reasonable company name length
                        experience.append(f"Company: {company}")
        
        # Extract durations
        for pattern in duration_patterns:
            matches = re.findall(pattern, text_to_search, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    duration = ' '.join([part for part in match if part])
                else:
                    duration = match
                experience.append(f"Duration: {duration}")
        
        # Extract achievements and responsibilities
        achievement_patterns = [
            r'[•·▪▫-]\s*([^\n\r]+)',
            r'(?:achieved|accomplished|delivered|implemented|developed|created|built|designed|managed|led)\s+([^\n\r.]+)',
            r'(?:responsible\s+for|duties\s+include|key\s+responsibilities)\s*:?\s*([^\n\r]+)',
            r'(?:reduced|increased|improved|optimized|enhanced)\s+([^\n\r.]+)',
            r'(?:\d+%|\d+\+|\$\d+)\s*(?:improvement|increase|decrease|reduction|growth|savings)'
        ]
        
        for pattern in achievement_patterns:
            matches = re.findall(pattern, text_to_search, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str):
                    achievement = match.strip()
                    if len(achievement) > 10 and len(achievement) < 200:
                        experience.append(f"Achievement: {achievement}")
        
        return list(set(experience))[:15]  # Increased limit
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications"""
        
        certifications = []
        
        # Get certifications section specifically
        cert_section = self._find_section_text(text, 'certifications')
        text_to_search = cert_section if cert_section else text
        
        # Enhanced certification patterns
        cert_patterns = [
            # Cloud certifications
            r'(aws|amazon)\s+certified\s+[\w\s-]+',
            r'(azure|microsoft)\s+certified\s+[\w\s-]+',
            r'(gcp|google\s+cloud)\s+certified\s+[\w\s-]+',
            # Professional certifications
            r'(cissp|cisa|cism|ceh|oscp|gsec)',
            r'(pmp|prince2|capm|psm|csm|safe)',
            r'(scrum\s+master|agile\s+certified|product\s+owner)',
            r'(itil|cobit|togaf|zachman)',
            # Technology certifications
            r'(oracle|oca|ocp|ocm)\s+certified',
            r'(cisco|ccna|ccnp|ccie|ccda|ccdp)',
            r'(vmware|vcp|vcap|vcdx)',
            r'(red\s+hat|rhcsa|rhce|rhca)',
            r'(comptia|a\+|network\+|security\+|linux\+)',
            r'(salesforce|administrator|developer|architect)',
            # General patterns
            r'certified\s+[\w\s-]+(?:administrator|developer|architect|engineer|specialist|professional)',
            r'[\w\s-]+\s+certification',
            r'[\w\s-]+\s+certified',
            # Academic and professional
            r'(cpa|cfa|frm|phr|sphr|shrm)',
            r'(six\s+sigma|lean|yellow\s+belt|green\s+belt|black\s+belt)',
            r'(chartered|professional)\s+[\w\s-]+',
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, text_to_search, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str):
                    cert = match.strip()
                    if len(cert) > 2:
                        certifications.append(cert.title())
        
        # Extract certification years/dates
        cert_with_dates = []
        date_patterns = [
            r'([\w\s-]+certified?\s+[\w\s-]+)[\s,]*\(?(19|20)\d{2}\)?',
            r'([\w\s-]+certified?\s+[\w\s-]+)[\s,]*(?:in|from)?\s*(19|20)\d{2}',
            r'(certified?\s+[\w\s-]+)[\s,]*\(?(19|20)\d{2}\)?'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text_to_search, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    cert_name = match[0].strip()
                    year = match[1] if len(match) > 1 else match[2] if len(match) > 2 else ''
                    if cert_name and year:
                        cert_with_dates.append(f"{cert_name.title()} ({year})")
        
        certifications.extend(cert_with_dates)
        
        return list(set(certifications))[:10]
    
    def _extract_projects(self, text: str) -> List[str]:
        """Extract project information"""
        
        projects = []
        
        # Get projects section specifically
        projects_section = self._find_section_text(text, 'projects')
        text_to_search = projects_section if projects_section else text
        
        # Enhanced project patterns
        project_patterns = [
            r'project[\s\w]*:?\s*([^\n\r]+)',
            r'(?:built|developed|created|designed|implemented)\s+([^\n\r]+?)(?:using|with|in)\s+([^\n\r]+)',
            r'(?:^|\n)\s*([A-Z][\w\s]+?)\s*[-–]\s*([^\n\r]+)',
            r'(?:portfolio|github|demo|live)\s*:?\s*([^\n\r]+)',
            r'(?:technologies|stack|built with)\s*:?\s*([^\n\r]+)',
            r'[•·▪▫-]\s*([^\n\r]+?)(?:\s*[-–]\s*([^\n\r]+))?',
            r'(?:web\s+app|mobile\s+app|application|system|platform|tool)\s*:?\s*([^\n\r]+)',
            r'(?:open\s+source|personal|side|freelance)\s+project\s*:?\s*([^\n\r]+)'
        ]
        
        for pattern in project_patterns:
            matches = re.findall(pattern, text_to_search, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Join non-empty parts
                    project_info = ' - '.join([part.strip() for part in match if part.strip()])
                else:
                    project_info = match.strip()
                
                if project_info and len(project_info) > 10:
                    projects.append(project_info)
        
        # Extract GitHub/portfolio links
        link_patterns = [
            r'(?:github|gitlab|bitbucket)\.com/[\w\-./]+',
            r'(?:portfolio|demo|live|website)\s*:?\s*(https?://[^\s\n\r]+)',
            r'(?:link|url)\s*:?\s*(https?://[^\s\n\r]+)'
        ]
        
        for pattern in link_patterns:
            matches = re.findall(pattern, text_to_search, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str):
                    projects.append(f"Link: {match}")
        
        return list(set(projects))[:10]
