# src/processing/document_processor.py
"""Main document processing pipeline."""
import os
import re
from typing import Dict, List, Any
from src.config import Config
from src.processing.ocr_cleaner import OCRCleaner, StructuredDataExtractor


class DocumentProcessor:
    """Process all documents and extract structured information."""
    
    def __init__(self):
        self.ocr_cleaner = OCRCleaner()
        self.extractor = StructuredDataExtractor()
        
    def process_all_documents(self, documents_dir: str) -> Dict[str, Dict]:
        """
        Process all documents in the directory.
        
        Args:
            documents_dir: Path to documents directory
            
        Returns:
            Dictionary with processed content for each document
        """
        processed_docs = {}
        
        # Process title search page 1 (has OCR noise)
        title_page1_path = os.path.join(documents_dir, Config.DOCUMENT_TYPES['title_search_page1'])
        if os.path.exists(title_page1_path):
            processed_docs['title_search_page1'] = self.process_title_search_page1(title_page1_path)
        
        # Process title search page 2
        title_page2_path = os.path.join(documents_dir, Config.DOCUMENT_TYPES['title_search_page2'])
        if os.path.exists(title_page2_path):
            processed_docs['title_search_page2'] = self.process_title_search_page2(title_page2_path)
        
        # Process servicer email
        email_path = os.path.join(documents_dir, Config.DOCUMENT_TYPES['servicer_email'])
        if os.path.exists(email_path):
            processed_docs['servicer_email'] = self.process_servicer_email(email_path)
        
        # Process court order
        court_path = os.path.join(documents_dir, Config.DOCUMENT_TYPES['court_order'])
        if os.path.exists(court_path):
            processed_docs['court_order'] = self.process_court_order(court_path)
        
        return processed_docs
    
    def process_title_search_page1(self, file_path: str) -> Dict[str, Any]:
        """Process title search page 1 with OCR noise."""
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
        
        # Clean OCR noise
        cleaned_text = self.ocr_cleaner.clean_text(raw_text)
        
        # Extract structured data
        metadata = self.ocr_cleaner.extract_metadata(cleaned_text)
        liens = self.extractor.extract_liens(cleaned_text)
        taxes = self.extractor.extract_taxes(cleaned_text)
        ownership = self.extractor.extract_ownership(cleaned_text)
        
        return {
            'type': 'title_search',
            'page': 1,
            'raw_text': raw_text,
            'cleaned_text': cleaned_text,
            'metadata': metadata,
            'liens': liens,
            'taxes': taxes,
            'ownership': ownership,
            'easements': self._extract_easements(cleaned_text),
            'restrictive_covenants': self._extract_covenants(cleaned_text)
        }
    
    def process_title_search_page2(self, file_path: str) -> Dict[str, Any]:
        """Process title search page 2 (cleaner text)."""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Extract additional information
        taxes = self.extractor.extract_taxes(text)
        ownership = self.extractor.extract_ownership(text)
        
        # Extract legal description
        legal_desc = self._extract_legal_description(text)
        
        return {
            'type': 'title_search',
            'page': 2,
            'text': text,
            'legal_description': legal_desc,
            'taxes': taxes,
            'ownership': ownership,
            'judgment_search': self._extract_judgment_search(text)
        }
    
    def process_servicer_email(self, file_path: str) -> Dict[str, Any]:
        """Process servicer email."""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Extract structured information
        action_items = self.extractor.extract_action_items(text)
        
        # Extract contact information
        contact_info = self._extract_contact_info(text)
        
        return {
            'type': 'email',
            'text': text,
            'action_items': action_items,
            'contact_info': contact_info,
            'payoff_amount': self._extract_payoff(text),
            'transfer_date': self._extract_transfer_date(text)
        }
    
    def process_court_order(self, file_path: str) -> Dict[str, Any]:
        """Process court order."""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        deadlines = self.extractor.extract_deadlines(text, 'court_order')
        
        return {
            'type': 'court_order',
            'text': text,
            'case_number': self._extract_case_number(text),
            'judge': self._extract_judge(text),
            'deadlines': deadlines,
            'requirements': self._extract_requirements(text)
        }
    
    def _extract_easements(self, text: str) -> List[Dict]:
        """Extract easement information."""
        easements = []
        easement_pattern = r'Easement in favor of ([^,]+) for ([^.]+)\. recorded in ([^,]+), Page (\d+)'
        
        matches = re.finditer(easement_pattern, text, re.IGNORECASE)
        for match in matches:
            easements.append({
                'beneficiary': match.group(1).strip(),
                'purpose': match.group(2).strip(),
                'recording': f"{match.group(3)}, Page {match.group(4)}"
            })
        
        return easements
    
    def _extract_covenants(self, text: str) -> List[Dict]:
        """Extract restrictive covenants."""
        covenants = []
        covenant_pattern = r'Restrictive covenants recorded in ([^,]+), Page (\d+)'
        
        matches = re.finditer(covenant_pattern, text, re.IGNORECASE)
        for match in matches:
            covenants.append({
                'recording': f"{match.group(1)}, Page {match.group(2)}"
            })
        
        return covenants
    
    def _extract_legal_description(self, text: str) -> str:
        """Extract legal description."""
        desc_pattern = r'LEGAL DESCRIPTION\s*\n(.*?)(?=\n\n|\Z)'
        match = re.search(desc_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_judgment_search(self, text: str) -> Dict:
        """Extract judgment search results."""
        results = {
            'unsatisfied_judgments': False,
            'federal_tax_liens': False,
            'state_tax_liens': False
        }
        
        if 'No unsatisfied judgments found' in text:
            results['unsatisfied_judgments'] = True
        
        if 'No federal tax liens found' in text:
            results['federal_tax_liens'] = True
        
        if 'No state tax liens found' in text:
            results['state_tax_liens'] = True
        
        return results
    
    def _extract_contact_info(self, text: str) -> Dict:
        """Extract contact information from email."""
        contact = {}
        
        # Extract attorney info
        attorney_match = re.search(r'([A-Za-z\s,]+) at ([A-Za-z\s&]+), \(([\d-]+)\)', text)
        if attorney_match:
            contact['borrower_counsel'] = {
                'name': attorney_match.group(1).strip(),
                'firm': attorney_match.group(2).strip(),
                'phone': attorney_match.group(3).strip()
            }
        
        # Extract servicer info
        servicer_match = re.search(r'Nationstar Mortgage LLC d/b/a Mr\. Cooper\s+Attn: Default Servicing\s+([^\n]+)\s+([^\n]+)\s+([^\n]+)', text, re.DOTALL)
        if servicer_match:
            contact['new_servicer'] = {
                'address': f"{servicer_match.group(1)}, {servicer_match.group(2)}, {servicer_match.group(3)}"
            }
        
        return contact
    
    def _extract_payoff(self, text: str) -> Dict:
        """Extract payoff information."""
        payoff_match = re.search(r'updated payoff amount as of ([A-Za-z]+\s+\d{1,2},\s+\d{4}) is \$([\d,]+\.?\d*)', text, re.IGNORECASE)
        
        if payoff_match:
            return {
                'amount': payoff_match.group(2),
                'as_of_date': payoff_match.group(1)
            }
        return {}
    
    def _extract_transfer_date(self, text: str) -> str:
        """Extract servicer transfer date."""
        transfer_match = re.search(r'effective ([A-Za-z]+\s+\d{1,2},\s+\d{4})', text, re.IGNORECASE)
        
        if transfer_match:
            return transfer_match.group(1)
        return ""
    
    def _extract_case_number(self, text: str) -> str:
        """Extract case number from court order."""
        case_match = re.search(r'CASE NO\.:\s*([\d-]+)', text, re.IGNORECASE)
        
        if case_match:
            return case_match.group(1)
        return ""
    
    def _extract_judge(self, text: str) -> str:
        """Extract judge name."""
        judge_match = re.search(r'HONORABLE JUDGE ([A-Za-z\s,\.]+)', text, re.IGNORECASE)
        
        if judge_match:
            return judge_match.group(1).strip()
        return ""
    
    def _extract_requirements(self, text: str) -> List[str]:
        """Extract filing requirements."""
        requirements = []
        
        # Extract case management report requirements
        if 'Case Management Report' in text:
            requirements.append('File Case Management Report 10 days before conference')
        
        if 'Proof of service' in text:
            requirements.append('File proof of service on all defendants')
        
        return requirements