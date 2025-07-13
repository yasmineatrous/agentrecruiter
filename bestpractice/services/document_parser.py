
import os
import aiohttp
import asyncio
import json
from typing import Dict, Any, Optional, List
from config import settings

class DocumentParser:
 
    
    def __init__(self):
        self.api_key = settings.LLAMA_PARSE_API_KEY
        self.base_url = "https://api.cloud.llamaindex.ai/api/parsing"
        
    async def parse_document(self, file_path: str, filename: str) -> Dict[str, Any]:

        
        if not self.api_key:
            raise ValueError("LLAMA_PARSE_API_KEY not found in environment variables")
        
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Step 1: Upload file and start parsing
            job_id = await self._upload_file(file_content, filename)
            
            # Step 2: Poll for completion
            return await self._poll_for_completion(job_id, file_path, filename)
                    
        except Exception as e:
            print(f"Error parsing document with LlamaParser: {str(e)}")
            # Fallback to simple text extraction
            return await self._fallback_text_extraction(file_path, filename)
    
    async def _upload_file(self, file_content: bytes, filename: str) -> str:

        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'accept': 'application/json'
        }
        
        # Create form data
        form_data = aiohttp.FormData()
        form_data.add_field('file', file_content, filename=filename)
        
        # Add optional parameters for better parsing
        form_data.add_field('language', 'en')
        form_data.add_field('parsing_instruction', 'Extract all text content while preserving structure and formatting.')
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/upload",
                headers=headers,
                data=form_data
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Upload error: {response.status} - {error_text}")
                    raise Exception(f"Upload failed: {response.status} - {error_text}")
                
                result = await response.json()
                print(f"DEBUG: Upload response: {json.dumps(result, indent=2)}")
                
                job_id = result.get('id')
                if not job_id:
                    raise Exception(f"No job ID in upload response: {result}")
                
                return job_id
    
    async def _poll_for_completion(self, job_id: str, file_path: str, filename: str, max_attempts: int = 60) -> Dict[str, Any]:
  
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'accept': 'application/json'
        }
        
        for attempt in range(max_attempts):
            try:
                # Check job status
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.base_url}/job/{job_id}",
                        headers=headers
                    ) as response:
                        
                        if response.status != 200:
                            error_text = await response.text()
                            print(f"Status check error: {response.status} - {error_text}")
                            raise Exception(f"Status check failed: {response.status} - {error_text}")
                        
                        result = await response.json()
                        print(f"DEBUG: Status check attempt {attempt + 1}: {json.dumps(result, indent=2)}")
                        
                        status = result.get('status')
                        
                        if status == 'SUCCESS':
                            # Get the parsed content in markdown format
                            return await self._get_markdown_result(job_id, file_path, filename)
                        
                        elif status == 'ERROR':
                            error_msg = result.get('error', 'Unknown error')
                            print(f"Job failed: {error_msg}")
                            raise Exception(f"Parsing job failed: {error_msg}")
                        
                        elif status in ['PENDING', 'RUNNING']:
                            print(f"Job {job_id} status: {status}, waiting...")
                            await asyncio.sleep(5)
                            continue
                        
                        else:
                            print(f"Unknown status: {status}")
                            raise Exception(f"Unknown status: {status}")
                            
            except Exception as e:
                print(f"Polling attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_attempts - 1:
                    print(f"Polling failed after {max_attempts} attempts, using fallback")
                    return await self._fallback_text_extraction(file_path, filename)
                await asyncio.sleep(5)
        
        print("Job did not complete within timeout, using fallback")
        return await self._fallback_text_extraction(file_path, filename)
    
    async def _get_markdown_result(self, job_id: str, file_path: str, filename: str) -> Dict[str, Any]:

        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'accept': 'application/json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/job/{job_id}/result/markdown",
                    headers=headers
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Result fetch error: {response.status} - {error_text}")
                        # Try to get text result instead
                        return await self._get_text_result(job_id, file_path, filename)
                    
                    result = await response.json()
                    print(f"DEBUG: Markdown result: {json.dumps(result, indent=2)}")
                    
                    # Extract markdown content
                    markdown_content = result.get('markdown', '')
                    if not markdown_content:
                        # Try alternative field names
                        markdown_content = result.get('text', '') or result.get('content', '')
                    
                    if not markdown_content or markdown_content.strip() == '':
                        print("No markdown content found, trying text endpoint")
                        return await self._get_text_result(job_id, file_path, filename)
                    
                    return {
                        'text': markdown_content,
                        'metadata': {
                            'job_id': job_id,
                            'source': 'llamaparser_markdown',
                            'filename': filename,
                            'format': 'markdown'
                        }
                    }
                    
        except Exception as e:
            print(f"Error getting markdown result: {str(e)}")
            return await self._get_text_result(job_id, file_path, filename)
    
    async def _get_text_result(self, job_id: str, file_path: str, filename: str) -> Dict[str, Any]:

        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'accept': 'application/json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/job/{job_id}/result/text",
                    headers=headers
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Text result fetch error: {response.status} - {error_text}")
                        raise Exception(f"Failed to get text result: {response.status} - {error_text}")
                    
                    result = await response.json()
                    print(f"DEBUG: Text result: {json.dumps(result, indent=2)}")
                    
                    # Extract text content
                    text_content = result.get('text', '')
                    if not text_content:
                        # Try alternative field names
                        text_content = result.get('content', '') or result.get('markdown', '')
                    
                    if not text_content or text_content.strip() == '':
                        print("No text content found, using fallback")
                        return await self._fallback_text_extraction(file_path, filename)
                    
                    return {
                        'text': text_content,
                        'metadata': {
                            'job_id': job_id,
                            'source': 'llamaparser_text',
                            'filename': filename,
                            'format': 'text'
                        }
                    }
                    
        except Exception as e:
            print(f"Error getting text result: {str(e)}")
            return await self._fallback_text_extraction(file_path, filename)
    
    async def _fallback_text_extraction(self, file_path: str, filename: str) -> Dict[str, Any]:
        """
        Fallback text extraction for when LlamaParser fails
        
        Args:
            file_path: Path to the file
            filename: Original filename
            
        Returns:
            Dict containing extracted text
        """
        
        try:
            file_ext = os.path.splitext(filename.lower())[1]
            
            if file_ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    
            elif file_ext == '.pdf':
                try:
                    import PyPDF2
                    text = ""
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        for page in pdf_reader.pages:
                            text += page.extract_text() + "\n"
                except ImportError:
                    try:
                        # Try alternative PDF library
                        import fitz  # PyMuPDF
                        doc = fitz.open(file_path)
                        text = ""
                        for page in doc:
                            text += page.get_text() + "\n"
                        doc.close()
                    except ImportError:
                        text = "PDF parsing requires PyPDF2 or PyMuPDF library"
                    
            elif file_ext == '.docx':
                try:
                    import docx
                    doc = docx.Document(file_path)
                    text = "\n".join([para.text for para in doc.paragraphs])
                except ImportError:
                    text = "DOCX parsing requires python-docx library"
                    
            elif file_ext in ['.doc']:
                text = "DOC format not supported in fallback mode"
                
            else:
                text = f"Unsupported file format: {file_ext}"
            
            # Ensure we have some text
            if not text or text.strip() == "":
                text = f"No text content could be extracted from {filename}"
            
            return {
                'text': text,
                'metadata': {
                    'source': 'fallback_extraction',
                    'filename': filename,
                    'file_type': file_ext
                }
            }
            
        except Exception as e:
            print(f"Error in fallback extraction: {str(e)}")
            return {
                'text': f"Error extracting text from {filename}: {str(e)}",
                'metadata': {
                    'source': 'fallback_extraction',
                    'error': str(e),
                    'filename': filename
                }
            }
    
    async def test_api_connection(self) -> bool:
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'accept': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                # Test with a simple request - you might need to adjust this endpoint
                async with session.get(
                    "https://api.cloud.llamaindex.ai/api/parsing/jobs",
                    headers=headers
                ) as response:
                    print(f"API test response: {response.status}")
                    return response.status in [200, 404]  # 404 is ok, means auth worked
                    
        except Exception as e:
            print(f"API connection test failed: {str(e)}")
            return False