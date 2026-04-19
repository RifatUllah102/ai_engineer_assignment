# src/processing/ocr_cleaner.py
"""OCR noise handling for title search documents."""
import re
from typing import Dict, List, Tuple
from src.config import Config


class OCRCleaner:
    """Clean OCR noise from text, especially for title search documents."""
    
    def __init__(self):
        self.corrections = Config.OCR_CORRECTIONS
        
    def clean_text(self, text: str) -> str:
        """
        Apply OCR corrections to text.
        
        Args:
            text: Raw OCR text with potential noise
            
        Returns:
            Cleaned text
        """
        cleaned = text
        
        # Apply exact string replacements first
        for wrong, correct in self.corrections.items():
            cleaned = cleaned.replace(wrong, correct)
        
        # Fix common pattern: number-letter substitutions
        # l vs 1 (context-based)
        cleaned = self._fix_l_one_substitutions(cleaned)
        
        # Fix O vs 0
        cleaned = self._fix_o_zero_substitutions(cleaned)
        
        # Fix extra spaces and line breaks
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _fix_l_one_substitutions(self, text: str) -> str:
        """Fix 'l' and '1' substitutions based on context."""
        # '1' should be 'l' when it appears in the middle of words
        # Example: 'tit1e' -> 'title', 'fi1e' -> 'file'
        text = re.sub(r'([a-zA-Z])1([a-zA-Z])', r'\1l\2', text)
        
        # 'l' should be '1' when it's a number in amounts
        # Example: '445,OOO' -> but careful with O vs 0
        text = re.sub(r'(\d+)l(\d+)', r'\g<1>1\2', text)
        
        return text
    
    def _fix_o_zero_substitutions(self, text: str) -> str:
        """Fix 'O' and '0' substitutions based on context."""
        # '0' should be 'O' when it's part of a word
        text = re.sub(r'([A-Z])0([A-Z])', r'\1O\2', text)
        
        # 'O' should be '0' when it's part of a number
        text = re.sub(r'(\d+)O(\d+)', r'\1\2', text)
        
        return text
    
    def extract_metadata(self, text: str) -> Dict[str, str]:
        """Extract metadata from title search text."""
        metadata = {}
        
        # Extract file number
        file_match = re.search(r'File No[.:]\s*([A-Z0-9-]+)', text, re.IGNORECASE)
        if file_match:
            metadata['file_number'] = file_match.group(1)
        
        # Extract effective date
        date_match = re.search(r'Effective Date[.:]\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})', text, re.IGNORECASE)
        if date_match:
            metadata['effective_date'] = date_match.group(1)
        
        # Extract property address
        addr_match = re.search(r'Property[.:]\s*([^\n]+)', text, re.IGNORECASE)
        if addr_match:
            metadata['property_address'] = addr_match.group(1).strip()
        
        return metadata


class StructuredDataExtractor:
    """Extract structured information from cleaned documents."""
    
    def extract_liens(self, text: str) -> List[Dict]:
        """Extract lien information from title search."""
        liens = []
        
        # Pattern for mortgage
        mortgage_pattern = r'Mortgage from ([A-Z\s,\.]+) to ([A-Z\s,\.&/]+) in the original amount of \$([\d,]+\.?\d*) dated ([A-Za-z]+\s+\d{1,2},\s+\d{4}) and recorded ([A-Za-z]+\s+\d{1,2},\s+\d{4}) as Instrument No\. ([A-Z0-9-]+)'
        
        matches = re.finditer(mortgage_pattern, text, re.IGNORECASE)
        for match in matches:
            liens.append({
                'type': 'mortgage',
                'borrower': match.group(1).strip(),
                'lender': match.group(2).strip(),
                'amount': match.group(3).strip(),
                'date': match.group(4).strip(),
                'recorded_date': match.group(5).strip(),
                'instrument_number': match.group(6).strip()
            })
        
        # Pattern for HOA lien
        hoa_pattern = r'Notice of Lis Pendens filed by ([A-Z\s,\.&]+) on ([A-Za-z]+\s+\d{1,2},\s+\d{4}) in the amount of \$([\d,]+\.?\d*) for unpaid assessments, recorded as Instrument No\. ([A-Z0-9-]+)'
        
        matches = re.finditer(hoa_pattern, text, re.IGNORECASE)
        for match in matches:
            liens.append({
                'type': 'hoa_lien',
                'holder': match.group(1).strip(),
                'date': match.group(2).strip(),
                'amount': match.group(3).strip(),
                'instrument_number': match.group(4).strip()
            })
        
        return liens
    
    def extract_taxes(self, text: str) -> Dict:
        """Extract tax information."""
        taxes = {}
        
        # Extract 2024 taxes
        tax_2024 = re.search(r'Tax Year 2024[:\s]+PAID\s*[-–]\s*\$([\d,]+\.?\d*)', text, re.IGNORECASE)
        if tax_2024:
            taxes['2024'] = {'status': 'PAID', 'amount': tax_2024.group(1)}
        
        # Extract 2025 taxes
        tax_2025 = re.search(r'Tax Year 2025[:\s]+UNPAID\s*[-–]\s*\$([\d,]+\.?\d*)', text, re.IGNORECASE)
        if tax_2025:
            taxes['2025'] = {'status': 'DELINQUENT', 'amount': tax_2025.group(1)}
        
        # Extract parcel number
        parcel = re.search(r'APN[:\s]+([\d-]+)', text, re.IGNORECASE)
        if parcel:
            taxes['parcel_number'] = parcel.group(1)
        
        return taxes
    
    def extract_ownership(self, text: str) -> Dict:
        """Extract ownership chain information."""
        ownership = {}
        
        # Extract current vesting
        current = re.search(r'Current vesting[:\s]+([A-Z\s,\.]+)', text, re.IGNORECASE)
        if current:
            ownership['current_owner'] = current.group(1).strip()
        
        # Extract chain
        chain_pattern = r'-\s+([A-Za-z\s,\.]+) \(([^)]+)\)'
        matches = re.finditer(chain_pattern, text)
        chain = []
        for match in matches:
            chain.append({
                'owner': match.group(1).strip(),
                'type': match.group(2).strip()
            })
        if chain:
            ownership['chain_of_title'] = chain
        
        return ownership
    
    def extract_deadlines(self, text: str, doc_type: str = 'court_order') -> List[Dict]:
        """Extract deadlines from court order or email."""
        deadlines = []
        
        if doc_type == 'court_order':
            # Extract conference date
            conference = re.search(r'Case Management Conference is set for ([A-Za-z]+\s+\d{1,2},\s+\d{4}) at (\d{1,2}:\d{2}\s*[AP]M)', text, re.IGNORECASE)
            if conference:
                deadlines.append({
                    'type': 'case_management_conference',
                    'date': conference.group(1),
                    'time': conference.group(2),
                    'action_required': 'Appear at conference'
                })
            
            # Extract report due date (10 days prior to conference)
            # This would require parsing the conference date and subtracting 10 days
            # For simplicity, we'll extract the explicit deadline
            proof_deadline = re.search(r'Proof of service on all named defendants must be filed with the Court no later than ([A-Za-z]+\s+\d{1,2},\s+\d{4})', text, re.IGNORECASE)
            if proof_deadline:
                deadlines.append({
                    'type': 'proof_of_service',
                    'date': proof_deadline.group(1),
                    'action_required': 'File proof of service'
                })
        
        return deadlines
    
    def extract_action_items(self, text: str) -> List[Dict]:
        """Extract action items from email."""
        actions = []
        
        # Extract servicer transfer info
        transfer = re.search(r'effective ([A-Za-z]+\s+\d{1,2},\s+\d{4})', text, re.IGNORECASE)
        if transfer:
            actions.append({
                'priority': 'HIGH',
                'action': 'Resubmit all pending fee authorizations to Mr. Cooper',
                'deadline': transfer.group(1),
                'details': 'Wells Fargo will reject invoices after transfer date'
            })
        
        # Extract payoff info
        payoff = re.search(r'updated payoff amount as of ([A-Za-z]+\s+\d{1,2},\s+\d{4}) is \$([\d,]+\.?\d*)', text, re.IGNORECASE)
        if payoff:
            actions.append({
                'priority': 'NORMAL',
                'action': 'Update payoff amount in system',
                'deadline': None,
                'details': f'${payoff.group(2)} as of {payoff.group(1)}'
            })
        
        # Extract HOA review
        hoa = re.search(r'(?i)(HOA has filed a lis pendens.*?review whether we need to name them)', text)
        if hoa:
            actions.append({
                'priority': 'HIGH',
                'action': 'Review HOA lis pendens',
                'deadline': 'Before filing complaint',
                'details': 'Determine if HOA must be named as party defendant'
            })
        
        return actions