
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class CandidateProfile(BaseModel):
    """Candidate profile extracted from resume"""
    education: List[str] = Field(default_factory=list, description="Educational qualifications")
    skills: List[str] = Field(default_factory=list, description="Technical and soft skills")
    experience: List[str] = Field(default_factory=list, description="Work experience summary")
    certifications: List[str] = Field(default_factory=list, description="Professional certifications")
    projects: List[str] = Field(default_factory=list, description="Notable projects")

class ComparisonItem(BaseModel):
    """Individual requirement comparison"""
    requirement: str = Field(..., description="Job requirement")
    match: bool = Field(..., description="Whether candidate meets this requirement")
    confidence: float = Field(..., description="Confidence score (0-1)")
    explanation: str = Field(..., description="Detailed explanation of the match")

class CandidateEvaluationResponse(BaseModel):
    """Complete candidate evaluation response"""
    fit_score: str = Field(..., description="Overall fit assessment (e.g., 'High Fit', 'Moderate Fit', 'Low Fit')")
    fit_percentage: float = Field(..., description="Numerical fit score (0-100)")
    candidate_name: Optional[str] = Field(None, description="Candidate name if provided")
    candidate_profile: CandidateProfile = Field(..., description="Extracted candidate profile")
    comparison_matrix: List[ComparisonItem] = Field(..., description="Detailed requirement comparisons")
    explanation: str = Field(..., description="Overall evaluation explanation")
    strengths: List[str] = Field(default_factory=list, description="Candidate's key strengths")
    areas_for_improvement: List[str] = Field(default_factory=list, description="Areas where candidate could improve")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for hiring decision")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
