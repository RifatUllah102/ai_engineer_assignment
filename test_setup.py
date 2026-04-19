# test_setup.py
"""Test script to verify everything is working."""
import os
from pathlib import Path

def test_file_structure():
    """Test that all required files exist."""
    print("Testing file structure...")
    
    required_files = [
        "ai_engineer_assignment_data/case_context.json",
        "ai_engineer_assignment_data/sample_edits.json",
        "ai_engineer_assignment_data/sample_documents/court_order.txt",
        "ai_engineer_assignment_data/sample_documents/servicer_email.txt",
        "ai_engineer_assignment_data/sample_documents/title_search_page1.txt",
        "ai_engineer_assignment_data/sample_documents/title_search_page2.txt",
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} - MISSING")
            all_exist = False
    
    return all_exist

def test_imports():
    """Test that all modules import correctly."""
    print("\nTesting imports...")
    
    try:
        from src.config import Config
        print("  ✓ Config imported")
        
        from src.processing.ocr_cleaner import OCRCleaner
        print("  ✓ OCRCleaner imported")
        
        from src.processing.document_processor import DocumentProcessor
        print("  ✓ DocumentProcessor imported")
        
        from src.retrieval.vector_store import DocumentRetriever
        print("  ✓ DocumentRetriever imported")
        
        from src.generation.draft_generator import DraftGenerator
        print("  ✓ DraftGenerator imported")
        
        from src.learning.edit_learner import EditLearner
        print("  ✓ EditLearner imported")
        
        return True
    except Exception as e:
        print(f"  ✗ Import error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("TESTING SETUP")
    print("=" * 50)
    
    # Test file structure
    files_ok = test_file_structure()
    
    # Test imports
    imports_ok = test_imports()
    
    # Check API key
    print("\nChecking API key...")
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"  ✓ API key found (starts with: {api_key[:10]}...)")
    else:
        print("  ✗ OPENAI_API_KEY not set in environment")
        print("  Please create a .env file with your API key")
    
    print("\n" + "=" * 50)
    if files_ok and imports_ok and api_key:
        print("✅ All tests passed! Ready to run main.py")
        print("\nRun: python main.py")
    else:
        print("⚠️  Some tests failed. Please fix issues before running main.py")
    print("=" * 50)