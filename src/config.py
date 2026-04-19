# src/config.py
import os
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

class Config:
    """Configuration settings."""
    
    # OpenAI settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-4o-mini"
    EMBEDDING_MODEL = "text-embedding-3-small"
    
    # Chunking settings
    CHUNK_SIZE = 800
    CHUNK_OVERLAP = 100
    
    # Retrieval settings
    TOP_K_CHUNKS = 5
    
    # File paths - use absolute paths
    DATA_DIR = str(PROJECT_ROOT / "ai_engineer_assignment_data")
    DOCUMENTS_DIR = str(PROJECT_ROOT / "ai_engineer_assignment_data" / "sample_documents")
    
    # Output settings
    OUTPUT_DIR = str(PROJECT_ROOT / "outputs")
    
    # OCR corrections (rest of the config remains the same)
    OCR_CORRECTIONS = {
        '1': 'l',
        'O': '0',
        '0': 'O',
        'T1TLE': 'TITLE',
        'EXCEPT1ONS': 'EXCEPTIONS',
        'Fi1e': 'File',
        'Pa1metto': 'Palmetto',
        'F1orida': 'Florida',
        'tit1e': 'title',
        '1ien': 'lien',
        'po1icy': 'policy',
        'WE11S': 'WELLS',
        'PALMETT0': 'PALMETTO',
        'ASSOCIATI0N': 'ASSOCIATION',
        '2O21': '2021',
        '2O25': '2025',
        '2O26': '2026',
    }
    
    DOCUMENT_TYPES = {
        'court_order': 'court_order.txt',
        'servicer_email': 'servicer_email.txt',
        'title_search_page1': 'title_search_page1.txt',
        'title_search_page2': 'title_search_page2.txt',
    }