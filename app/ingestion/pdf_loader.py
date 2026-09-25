import os
import pymupdf
from langdetect import detect, DetectorFactory
from pydantic import BaseModel
from typing import List

# Ensure consistent language detection
DetectorFactory.seed = 0

class Page(BaseModel):
    page_number: int
    text: str
    language: str = "unknown"
    character_count: int

class Document(BaseModel):
    document_id: str
    filename: str
    page_count: int
    language: str = "unknown"
    pages: List[Page]

def detect_language(text: str) -> str:
    if not text or len(text.strip()) < 10:
        return "unknown"
    try:
        return detect(text)
    except Exception:
        return "unknown"

def load_pdf(file_path: str) -> Document:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF not found: {file_path}")
        
    filename = os.path.basename(file_path)
    document_id = os.path.splitext(filename)[0]
    
    doc = pymupdf.open(file_path)
    pages = []
    
    doc_lang_counts = {}
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text") or ""
        
        # Original text preserved, just count chars
        character_count = len(text)
        
        # Detect language
        language = detect_language(text)
        
        if language != "unknown":
            doc_lang_counts[language] = doc_lang_counts.get(language, 0) + 1
            
        pages.append(Page(
            page_number=page_num + 1,  # 1-indexed
            text=text,
            language=language,
            character_count=character_count
        ))
        
    # Determine dominant document language
    doc_language = "unknown"
    if doc_lang_counts:
        doc_language = max(doc_lang_counts.items(), key=lambda x: x[1])[0]
        
    document = Document(
        document_id=document_id,
        filename=filename,
        page_count=len(doc),
        language=doc_language,
        pages=pages
    )
    
    doc.close()
    return document
