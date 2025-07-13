# AI-Based Candidate Evaluation System

## Overview

This project is an AI-powered system that evaluates how well a candidate's resume fits a job description. It uses advanced document parsing, semantic embeddings, vector search, and Large Language Models (LLMs) to generate detailed candidate-job fit scores and insights.
<iframe width="560" height="315" src="[https://youtu.be/kCU_4uS3H2o]" frameborder="0" allowfullscreen></iframe>


## System Architecture

The system is modular and service-oriented, composed of:

### 1. Document Parsing

- **Primary parser:** [LlamaParse](https://llamaparse.ai/) — used for extracting structured text from PDFs and DOCX files.
- **Fallback parser:** [PyPDF](https://pypdf.readthedocs.io/en/latest/) — used if LlamaParse is unavailable or fails.

### 2. Text Processing

- Regex-based cleaning and section detection using Python's `re` module.
- Chunking documents into overlapping 500-word segments.
- Extracting candidate profile sections: education, skills, experience, certifications, and projects.

### 3. Embedding Generation

- [Sentence Transformers](https://www.sbert.net/) with the `all-MiniLM-L6-v2` model for text embeddings.

### 4. Vector Store

- [FAISS](https://faiss.ai/) (Facebook AI Similarity Search) for fast semantic similarity search on embeddings.

### 5. LLM Evaluation

- [Mistral LLM](https://mistral.ai/) (model: `mistral-small-latest`) to analyze candidate fit against job requirements and generate detailed explanations.

## Data Flow

1. Resume and job description files are uploaded.
2. Text is extracted via LlamaParse, or PyPDF if needed.
3. Text is cleaned, segmented, and chunked.
4. Embeddings are computed and indexed using FAISS.
5. Mistral LLM evaluates candidate fit by comparing embeddings and textual context.
6. The system outputs a structured JSON report with fit scores, strengths, weaknesses, and recommendations.

---

# Installation & Setup

## Prerequisites

- Python 3.11 or higher
- Poetry or pip for dependency management
- API keys for:
  - LlamaParse
  - Mistral

## Environment Variables (`.env`)

Create a `.env` file at the project root with:

```ini
LLAMAPARSE_API_KEY=your_llamaparse_api_key
MISTRAL_API_KEY=your_mistral_api_key
``` 

## Install Dependencies
```ini
pip install poetry
```
```ini
poetry install
```
```ini
cd bestpractice
```
```ini
python main.py
```
Ensure Python 3.11+ is active:

