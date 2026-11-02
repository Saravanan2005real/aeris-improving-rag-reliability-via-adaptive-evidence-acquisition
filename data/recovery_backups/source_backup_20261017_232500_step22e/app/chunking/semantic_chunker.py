import re
from pydantic import BaseModel
from typing import List
from app.ingestion.pdf_loader import Document

class Chunk(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    language: str
    pages: List[int]
    start_page: int
    end_page: int
    character_count: int

def split_into_sentences(text: str) -> List[str]:
    # Basic sentence boundary detection
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in sentences if s.strip()]

def chunk_document(
    document: Document, 
    target_size: int = 1200, 
    max_size: int = 1800, 
    min_size: int = 300
) -> List[Chunk]:
    chunks = []
    
    # Gather all blocks (paragraphs) with their page numbers
    blocks = []
    for page in document.pages:
        # Split by blank lines or standard paragraph breaks
        paragraphs = re.split(r'\n\s*\n', page.text)
        for p in paragraphs:
            p = p.strip()
            if p:
                blocks.append({
                    'text': p,
                    'page': page.page_number
                })
                
    # Accumulate blocks into chunks
    current_text = ""
    current_pages = []
    chunk_index = 1
    
    def finalize_chunk():
        nonlocal current_text, current_pages, chunk_index
        if not current_text.strip():
            return
            
        text_str = current_text.strip()
        pages_list = sorted(list(set(current_pages)))
        start_p = pages_list[0]
        end_p = pages_list[-1]
        
        chunk_id = f"{document.document_id}_p{start_p:03d}_c{chunk_index:03d}"
        
        chunks.append(Chunk(
            chunk_id=chunk_id,
            document_id=document.document_id,
            text=text_str,
            language=document.language,
            pages=pages_list,
            start_page=start_p,
            end_page=end_p,
            character_count=len(text_str)
        ))
        
        chunk_index += 1
        current_text = ""
        current_pages = []

    for block in blocks:
        block_text = block['text']
        block_page = block['page']
        
        if len(current_text) >= target_size:
            finalize_chunk()
            
        if len(block_text) > max_size:
            sentences = split_into_sentences(block_text)
            for sentence in sentences:
                if len(current_text) + len(sentence) > max_size and len(current_text) >= min_size:
                    finalize_chunk()
                    
                if len(sentence) > max_size:
                    # hard split for extremely long sentences
                    for i in range(0, len(sentence), target_size):
                        part = sentence[i:i+target_size]
                        if len(current_text) + len(part) > max_size and len(current_text) >= min_size:
                            finalize_chunk()
                        current_text += part + " "
                        current_pages.append(block_page)
                else:
                    current_text += sentence + " "
                    current_pages.append(block_page)
        else:
            if len(current_text) + len(block_text) > max_size and len(current_text) >= min_size:
                finalize_chunk()
            
            current_text += block_text + "\n\n"
            current_pages.append(block_page)
            
    finalize_chunk()
    return chunks
