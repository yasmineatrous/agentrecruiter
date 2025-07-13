
import os
import tempfile
import traceback
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from bestpractice.models.schemas import CandidateEvaluationResponse
from bestpractice.services.candidate_evaluator import CandidateEvaluator
from bestpractice.config import settings

# Initialize FastAPI app
app = FastAPI(
    title="AI Candidate Fit Evaluator",
    description="Evaluate how well a candidate's resume matches a job description using AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="bestpractice/static"), name="static")

# Initialize the candidate evaluator
candidate_evaluator = CandidateEvaluator()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    with open("bestpractice/static/index.html", "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.post("/evaluate-candidate", response_model=CandidateEvaluationResponse)
async def evaluate_candidate(
    resume_file: UploadFile = File(..., description="Resume file (PDF or DOCX)"),
    job_description_file: UploadFile = File(..., description="Job description file (PDF, DOCX, or TXT)"),
    candidate_name: Optional[str] = Form(None, description="Candidate name (optional)")
):
    """
    Evaluate how well a candidate's resume matches a job description
    
    Args:
        resume_file: PDF or DOCX file containing the candidate's resume
        job_description_file: PDF, DOCX, or TXT file containing the job description
        candidate_name: Optional candidate name for metadata
        
    Returns:
        CandidateEvaluationResponse: Structured evaluation with fit score, profile, and comparison matrix
    """
    
    # Validate file types
    allowed_extensions = {'.pdf', '.docx', '.txt'}
    
    def get_file_extension(filename: str) -> str:
        return os.path.splitext(filename.lower())[1]
    
    resume_ext = get_file_extension(resume_file.filename)
    job_ext = get_file_extension(job_description_file.filename)
    
    if resume_ext not in {'.pdf', '.docx'}:
        raise HTTPException(
            status_code=400,
            detail="Resume file must be PDF or DOCX format"
        )
    
    if job_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Job description file must be PDF, DOCX, or TXT format"
        )
    
    # Create temporary files
    resume_temp = None
    job_temp = None
    
    try:
        # Save uploaded files temporarily
        resume_temp = tempfile.NamedTemporaryFile(delete=False, suffix=resume_ext)
        job_temp = tempfile.NamedTemporaryFile(delete=False, suffix=job_ext)
        
        # Write file contents
        resume_content = await resume_file.read()
        job_content = await job_description_file.read()
        
        resume_temp.write(resume_content)
        job_temp.write(job_content)
        resume_temp.close()
        job_temp.close()
        
        # Evaluate candidate
        evaluation = await candidate_evaluator.evaluate_candidate(
            resume_path=resume_temp.name,
            job_description_path=job_temp.name,
            candidate_name=candidate_name
        )
        
        return evaluation
        
    except Exception as e:
        print(f"Error during evaluation: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error processing files: {str(e)}"
        )
    
    finally:
        # Clean up temporary files
        if resume_temp and os.path.exists(resume_temp.name):
            os.unlink(resume_temp.name)
        if job_temp and os.path.exists(job_temp.name):
            os.unlink(job_temp.name)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "AI Candidate Fit Evaluator is running"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    print(f"Global exception handler: {str(exc)}")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )
