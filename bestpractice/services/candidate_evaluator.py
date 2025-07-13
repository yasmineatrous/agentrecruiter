
import asyncio
from typing import Dict, Any, List, Optional
from bestpractice.models.schemas import CandidateEvaluationResponse, CandidateProfile, ComparisonItem
from bestpractice.services.document_parser import DocumentParser
from bestpractice.services.embedding_service import EmbeddingService
from bestpractice.services.vector_store import VectorStore
from bestpractice.services.llm_evaluator import LLMEvaluator
from bestpractice.utils.text_processing import TextProcessor

class CandidateEvaluator:
    """Main service for evaluating candidate-job fit"""
    
    def __init__(self):
        self.document_parser = DocumentParser()
        self.embedding_service = EmbeddingService()
        self.llm_evaluator = LLMEvaluator()
        self.text_processor = TextProcessor()
        
        # Initialize vector store
        self.vector_store = VectorStore(
            dimension=self.embedding_service.get_embedding_dimension()
        )
    
    async def evaluate_candidate(
        self,
        resume_path: str,
        job_description_path: str,
        candidate_name: Optional[str] = None
    ) -> CandidateEvaluationResponse:
        """
        Evaluate candidate fit for job position
        
        Args:
            resume_path: Path to resume file
            job_description_path: Path to job description file
            candidate_name: Optional candidate name
            
        Returns:
            Complete candidate evaluation response
        """
        
        try:
            # Step 1: Parse documents
            print("Parsing documents...")
            resume_data = await self.document_parser.parse_document(
                resume_path, 
                "resume.pdf"
            )
            job_data = await self.document_parser.parse_document(
                job_description_path, 
                "job_description.pdf"
            )
            
            resume_text = resume_data.get('text', '')
            job_description_text = job_data.get('text', '')
            
            if not resume_text or not job_description_text:
                print(f"Resume text length: {len(resume_text) if resume_text else 0}")
                print(f"Job description text length: {len(job_description_text) if job_description_text else 0}")
                print(f"Resume data: {resume_data}")
                print(f"Job data: {job_data}")
                raise ValueError("Failed to extract text from documents")
            
            # Step 2: Process and chunk documents
            print("Processing and chunking documents...")
            resume_chunks = await self.text_processor.chunk_resume(resume_text)
            job_chunks = await self.text_processor.chunk_job_description(job_description_text)
            
            # Step 3: Extract candidate profile
            print("Extracting candidate profile...")
            candidate_profile = await self.text_processor.extract_candidate_profile(resume_text)
            
            # Step 4: Extract job requirements
            print("Extracting job requirements...")
            job_requirements = await self.llm_evaluator.extract_job_requirements(job_description_text)
            
            # Step 5: Generate embeddings and build vector store
            print("Generating embeddings...")
            await self._build_vector_store(resume_chunks, job_chunks)
            
            # Step 6: Find relevant resume chunks for each requirement
            print("Finding relevant resume sections...")
            relevant_chunks = await self._find_relevant_chunks(job_requirements)
            
            # Step 7: Evaluate candidate using LLM
            print("Evaluating candidate fit...")
            evaluation = await self.llm_evaluator.evaluate_candidate_fit(
                candidate_profile,
                job_requirements,
                relevant_chunks,
                job_description_text
            )
            
            # Step 8: Build response
            response = await self._build_response(
                evaluation,
                candidate_profile,
                candidate_name
            )
            
            print("Evaluation completed successfully")
            return response
            
        except Exception as e:
            print(f"Error in candidate evaluation: {str(e)}")
            raise
    
    async def _build_vector_store(self, resume_chunks: List[str], job_chunks: List[str]):
        """Build vector store with document chunks"""
        
        # Clear existing data
        self.vector_store.clear()
        
        # Combine all chunks
        all_chunks = resume_chunks + job_chunks
        
        # Create metadata
        metadata = []
        for i, chunk in enumerate(resume_chunks):
            metadata.append({
                'type': 'resume',
                'chunk_index': i,
                'source': 'resume'
            })
        
        for i, chunk in enumerate(job_chunks):
            metadata.append({
                'type': 'job_description',
                'chunk_index': i,
                'source': 'job_description'
            })
        
        # Generate embeddings
        if all_chunks:
            embeddings = await self.embedding_service.generate_embeddings(all_chunks)
            
            # Add to vector store
            self.vector_store.add_documents(all_chunks, embeddings, metadata)
    
    async def _find_relevant_chunks(self, job_requirements: List[str]) -> List[str]:
        """Find relevant resume chunks for job requirements"""
        
        relevant_chunks = []
        
        for requirement in job_requirements:
            # Generate embedding for requirement
            requirement_embedding = await self.embedding_service.generate_single_embedding(requirement)
            
            # Search for relevant chunks
            results = self.vector_store.search(requirement_embedding, k=3)
            
            # Filter for resume chunks only
            resume_results = [
                text for text, score, metadata in results
                if metadata.get('type') == 'resume' and score > 0.3
            ]
            
            relevant_chunks.extend(resume_results)
        
        # Remove duplicates while preserving order
        unique_chunks = []
        seen = set()
        for chunk in relevant_chunks:
            if chunk not in seen:
                unique_chunks.append(chunk)
                seen.add(chunk)
        
        return unique_chunks[:5]  # Limit to top 5 chunks
    
    async def _build_response(
        self,
        evaluation: Dict[str, Any],
        candidate_profile: Dict[str, Any],
        candidate_name: Optional[str]
    ) -> CandidateEvaluationResponse:
        """Build the final evaluation response"""
        
        # Create candidate profile object
        profile = CandidateProfile(
            education=candidate_profile.get('education', []),
            skills=candidate_profile.get('skills', []),
            experience=candidate_profile.get('experience', []),
            certifications=candidate_profile.get('certifications', []),
            projects=candidate_profile.get('projects', [])
        )
        
        # Create comparison matrix
        comparison_matrix = []
        for item in evaluation.get('comparison_matrix', []):
            comparison_item = ComparisonItem(
                requirement=item.get('requirement', ''),
                match=item.get('match', False),
                confidence=item.get('confidence', 0.5),
                explanation=item.get('explanation', '')
            )
            comparison_matrix.append(comparison_item)
        
        # Create response
        response = CandidateEvaluationResponse(
            fit_score=evaluation.get('fit_score', 'Moderate Fit'),
            fit_percentage=evaluation.get('fit_percentage', 50.0),
            candidate_name=candidate_name,
            candidate_profile=profile,
            comparison_matrix=comparison_matrix,
            explanation=evaluation.get('explanation', ''),
            strengths=evaluation.get('strengths', []),
            areas_for_improvement=evaluation.get('areas_for_improvement', []),
            recommendations=evaluation.get('recommendations', [])
        )
        
        return response
