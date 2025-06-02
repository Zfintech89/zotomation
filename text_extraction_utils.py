import os
import re
import logging
import hashlib
import mimetypes
from werkzeug.utils import secure_filename
from pathlib import Path
from datetime import datetime


try:
    import fitz  
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import docx  
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_MB = 50
MIN_CONTENT_LENGTH = 50
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

ALLOWED_EXTENSIONS = {
    'pdf': {'pdf'},
    'text': {'txt', 'md', 'rtf'},
    'document': {'docx', 'doc'}
}

FILE_SIZE_LIMITS = {
    'pdf': 50 * 1024 * 1024,      # 50MB for PDFs
    'text': 10 * 1024 * 1024,     # 10MB for text
    'document': 25 * 1024 * 1024  # 25MB for docs
}

def detect_file_type(file):
    """Detect file type from filename and MIME type"""
    if not hasattr(file, 'filename') or not file.filename:
        return None
        
    filename = file.filename.lower()
    ext = filename.rsplit('.', 1)[1] if '.' in filename else ''
    
    # Check extension first
    for type_key, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return type_key
    
    return None

def validate_file(file):
    """Validate file for processing"""
    if not file or not hasattr(file, 'filename'):
        return False, "Invalid file provided"
    
    if not file.filename:
        return False, "No filename provided"
    
    # Security check
    filename = file.filename
    if '..' in filename or '/' in filename or '\\' in filename:
        return False, "Invalid filename - security violation"
    
    file_type = detect_file_type(file)
    if not file_type:
        return False, f"Unsupported file type: {filename}"
    
    return True, file_type

def validate_file_size(file_path, file_type):
    """Validate file size based on type"""
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    file_size = os.path.getsize(file_path)
    limit = FILE_SIZE_LIMITS.get(file_type, MAX_FILE_SIZE_MB * 1024 * 1024)
    
    if file_size > limit:
        size_mb = file_size / (1024 * 1024)
        limit_mb = limit / (1024 * 1024)
        return False, f"File size ({size_mb:.1f}MB) exceeds limit ({limit_mb:.1f}MB)"
    
    return True, None

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyMuPDF"""
    if not PDF_AVAILABLE:
        return "", "PyMuPDF not available. Install with: pip install PyMuPDF"
    
    if not os.path.exists(pdf_path):
        return "", f"PDF file not found: {pdf_path}"
    
    try:
        # Validate file size
        size_ok, error = validate_file_size(pdf_path, 'pdf')
        if not size_ok:
            return "", error
        
        doc = fitz.open(pdf_path)
        text_parts = []
        total_pages = len(doc)
        
        if total_pages == 0:
            doc.close()
            return "", "PDF has no pages"
        
        successful_pages = 0
        
        for page_num in range(total_pages):
            try:
                page = doc[page_num]
                page_text = page.get_text()
                
                if page_text and page_text.strip():
                    cleaned_text = page_text.strip()
                    if len(cleaned_text) > 10:  # Minimum content threshold
                        text_parts.append(f"[Page {page_num + 1}]\n{cleaned_text}")
                        successful_pages += 1
                
            except Exception as e:
                logger.warning(f"Error processing page {page_num + 1}: {e}")
                continue
        
        doc.close()
        
        if successful_pages == 0:
            return "", "No readable content found in PDF"
        
        extracted_text = "\n\n".join(text_parts)
        logger.info(f"PDF extraction: {successful_pages}/{total_pages} pages, {len(extracted_text)} characters")
        
        return extracted_text, None
        
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return "", f"PDF extraction failed: {str(e)}"

def extract_text_from_docx(docx_path):
    """Extract text from DOCX using python-docx"""
    if not DOCX_AVAILABLE:
        return "", "python-docx not available. Install with: pip install python-docx"
    
    if not os.path.exists(docx_path):
        return "", f"DOCX file not found: {docx_path}"
    
    try:
        # Validate file size
        size_ok, error = validate_file_size(docx_path, 'document')
        if not size_ok:
            return "", error
        
        doc = docx.Document(docx_path)
        text_parts = []
        
        # Extract paragraphs
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text.strip())
        
        # Extract tables
        for table in doc.tables:
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    if cell.text.strip():
                        row_text.append(cell.text.strip())
                if row_text:
                    text_parts.append(" | ".join(row_text))
        
        if not text_parts:
            return "", "No readable content found in DOCX"
        
        extracted_text = "\n\n".join(text_parts)
        logger.info(f"DOCX extraction: {len(text_parts)} elements, {len(extracted_text)} characters")
        
        return extracted_text, None
        
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}")
        return "", f"DOCX extraction failed: {str(e)}"

def extract_text_from_text_file(file_path):
    """Extract text from plain text files with encoding detection"""
    if not os.path.exists(file_path):
        return "", f"Text file not found: {file_path}"
    
    try:
        # Validate file size
        size_ok, error = validate_file_size(file_path, 'text')
        if not size_ok:
            return "", error
        
        # Try multiple encodings
        encodings = ['utf-8', 'utf-16', 'utf-8-sig', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                
                if content and content.strip():
                    logger.info(f"Text file read with {encoding}: {len(content)} characters")
                    return content.strip(), None
                    
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                logger.error(f"Error reading with {encoding}: {e}")
                break
        
        return "", "Could not read text file with any supported encoding"
        
    except Exception as e:
        logger.error(f"Error processing text file: {e}")
        return "", f"Text file processing failed: {str(e)}"

def extract_text_from_file(file_path, file_type=None):
    """Universal text extraction based on file type"""
    if not file_type:
        # Auto-detect based on extension
        ext = file_path.lower().rsplit('.', 1)[-1] if '.' in file_path else ''
        
        if ext == 'pdf':
            file_type = 'pdf'
        elif ext in ['docx', 'doc']:
            file_type = 'document'
        else:
            file_type = 'text'
    
    # Route to appropriate extractor
    if file_type == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_type == 'document':
        return extract_text_from_docx(file_path)
    else:
        return extract_text_from_text_file(file_path)

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Smart text chunking with overlap for better context"""
    if not text or not isinstance(text, str):
        return []
    
    text = text.strip()
    text_length = len(text)
    
    if text_length <= chunk_size:
        return [text] if text_length >= MIN_CONTENT_LENGTH else []
    
    chunks = []
    start = 0
    
    while start < text_length:
        end = start + chunk_size
        
        if end < text_length:
            # Smart boundary detection
            boundaries = [
                ('\n\n', 300),  # Paragraph boundaries
                ('.', 200),     # Sentence boundaries
                ('!', 200),     # Exclamation boundaries
                ('?', 200),     # Question boundaries
                (';', 150),     # Semicolon boundaries
                ('\n', 100),    # Line boundaries
                (' ', 50)       # Word boundaries
            ]
            
            best_boundary = end
            for boundary_char, search_range in boundaries:
                search_start = max(start, end - search_range)
                boundary_pos = text.rfind(boundary_char, search_start, end)
                if boundary_pos > start:
                    best_boundary = boundary_pos + len(boundary_char)
                    break
            
            end = best_boundary
        
        chunk = text[start:end].strip()
        
        # Validate chunk
        if len(chunk) >= MIN_CONTENT_LENGTH and len(chunk.split()) >= 3:
            chunks.append(chunk)
        
        start = max(end - overlap, start + 1)
        if start >= text_length:
            break
    
    return chunks

def analyze_text_content(text):
    """Analyze text content and suggest slide count"""
    if not text:
        return {
            'chars': 0,
            'words': 0,
            'sentences': 0,
            'paragraphs': 0,
            'suggested_slides': 3
        }
    
    # Basic metrics
    chars = len(text)
    words = len(text.split()) if text.strip() else 0
    sentences = len(re.findall(r'[.!?]+', text))
    paragraphs = len([p for p in text.split('\n\n') if p.strip()])
    
    # Smart slide suggestion
    if words < 100:
        suggested_slides = 3
    elif words < 300:
        suggested_slides = 4
    elif words < 600:
        suggested_slides = 5
    elif words < 1000:
        suggested_slides = 6
    elif words < 1500:
        suggested_slides = 7
    elif words < 2500:
        suggested_slides = 8
    else:
        suggested_slides = min(10, max(8, words // 300))
    
    return {
        'chars': chars,
        'words': words,
        'sentences': sentences,
        'paragraphs': paragraphs,
        'suggested_slides': suggested_slides,
        'readability': 'high' if words > 500 else 'medium' if words > 100 else 'low'
    }

def process_uploaded_file(file, temp_dir):
    """Process uploaded file and extract text content"""
    try:
        # Validate file
        is_valid, result = validate_file(file)
        if not is_valid:
            return None, result
        
        file_type = result
        
        # Save file securely
        filename = secure_filename(file.filename)
        if not filename:
            return None, "Invalid filename"
        
        # Create unique filename to avoid conflicts
        file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
        safe_filename = f"{file_hash}_{filename}"
        file_path = os.path.join(temp_dir, safe_filename)
        
        # Ensure temp directory exists
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save uploaded file
        file.save(file_path)
        
        # Extract text
        extracted_text, error = extract_text_from_file(file_path, file_type)
        
        # Clean up
        try:
            os.remove(file_path)
        except:
            pass
        
        if error:
            return None, error
        
        if not extracted_text or len(extracted_text.strip()) < MIN_CONTENT_LENGTH:
            return None, "Could not extract meaningful text from file"
        
        # Analyze content
        analysis = analyze_text_content(extracted_text)
                # Log extracted text to a file
        try:
            log_dir = os.path.join(temp_dir, "logs")
            os.makedirs(log_dir, exist_ok=True)
            
            log_filename = os.path.join(log_dir, "extracted_text.log")
            with open(log_filename, "a", encoding="utf-8") as log_file:
                log_file.write(f"\n----- {datetime.now()} - {filename} -----\n")
                log_file.write(extracted_text[:5000])  # Limit to first 5000 chars to avoid overload
                log_file.write("\n\n")
        except Exception as log_error:
            logger.warning(f"Failed to log extracted text: {log_error}")

        return {
            'text': extracted_text,
            'analysis': analysis,
            'file_type': file_type,
            'original_filename': filename
        }, None
        
    except Exception as e:
        logger.error(f"Error processing uploaded file: {e}")
        return None, f"File processing failed: {str(e)}"
