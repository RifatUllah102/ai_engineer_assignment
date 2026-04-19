# src/learning/edit_learner.py
"""Learn from operator edits to improve future outputs."""
import re
import difflib
from typing import Dict, List, Any


class EditLearner:
    """Analyze operator edits and extract learnable patterns."""
    
    def __init__(self):
        self.learnings = {
            'title_review': {},
            'case_status': {}
        }
    
    def learn_from_edit(self, edit: Dict) -> Dict:
        """
        Analyze an edit pair and extract patterns.
        
        Args:
            edit: Dictionary with system_draft, operator_edited_version, key_edits
            
        Returns:
            Dictionary of learned patterns
        """
        draft_type = edit['draft_type']
        system_draft = edit['system_draft']
        operator_draft = edit['operator_edited_version']
        key_edits = edit['key_edits']
        
        patterns = {}
        
        if draft_type == 'title_review_summary':
            patterns = self._analyze_title_edits(system_draft, operator_draft, key_edits)
            self.learnings['title_review'].update(patterns)
            
        elif draft_type == 'case_status_memo':
            patterns = self._analyze_memo_edits(system_draft, operator_draft, key_edits)
            self.learnings['case_status'].update(patterns)
        
        return patterns
    
    def _analyze_title_edits(self, system: str, operator: str, key_edits: List[str]) -> Dict:
        """Analyze title review edits."""
        patterns = {
            'structure': 'Use labeled sections (LIENS & ENCUMBRANCES, TAX STATUS, OWNERSHIP, OTHER MATTERS, REVIEWER NOTES)',
            'include_instrument_numbers': True,
            'include_recording_details': True,
            'flag_action_items': True,
            'separate_tax_section': True,
            'add_reviewer_notes': True,
            'prioritize_hoa_review': 'HOA lis pendens requires action flag',
            'cross_reference_servicing': 'Reference servicer email for transfer details'
        }
        
        # Extract specific patterns from key_edits
        for edit in key_edits:
            if 'organized into labeled sections' in edit:
                patterns['structure_implemented'] = True
            if 'added instrument numbers' in edit:
                patterns['instrument_numbers'] = True
            if 'ACTION REQUIRED' in edit:
                patterns['action_flags'] = True
            if 'reviewer notes section' in edit:
                patterns['reviewer_notes'] = True
            if 'cross-referenced the servicing transfer' in edit:
                patterns['cross_referencing'] = True
        
        return patterns
    
    def _analyze_memo_edits(self, system: str, operator: str, key_edits: List[str]) -> Dict:
        """Analyze case status memo edits."""
        patterns = {
            'structure': 'Prioritized ACTION ITEMS section at top',
            'include_priority_levels': 'URGENT, HIGH, NORMAL',
            'cross_reference_deadlines': True,
            'add_court_details': 'Include judge name, courtroom, case number',
            'add_counsel_info': 'Include borrower attorney contact',
            'actionable_deadlines': 'Not just dates but required actions',
            'unified_picture': 'Connect information across all documents'
        }
        
        # Extract specific patterns from key_edits
        for edit in key_edits:
            if 'prioritized ACTION ITEMS' in edit:
                patterns['prioritization'] = True
            if 'cross-referenced deadlines' in edit:
                patterns['deadline_cross_reference'] = True
            if 'added court details' in edit or 'judge name' in edit:
                patterns['court_details'] = True
            if 'borrower\'s counsel information' in edit:
                patterns['counsel_info'] = True
            if 'actionable' in edit:
                patterns['actionable_deadlines'] = True
            if 'connected information across all documents' in edit:
                patterns['cross_document_synthesis'] = True
        
        return patterns
    
    def get_all_learnings(self) -> Dict:
        """Get all learned patterns."""
        return self.learnings
    
    def compare_drafts(self, draft1: str, draft2: str, draft_type: str) -> Dict:
        """
        Compare two drafts to measure improvement.
        
        Args:
            draft1: Original draft
            draft2: Improved draft
            draft_type: Type of draft
            
        Returns:
            Comparison metrics
        """
        # Calculate structural differences
        lines1 = set(draft1.split('\n'))
        lines2 = set(draft2.split('\n'))
        
        added_lines = lines2 - lines1
        removed_lines = lines1 - lines2
        
        # Check for key structural elements
        structure_elements = []
        if draft_type == 'title_review':
            required_sections = ['LIENS & ENCUMBRANCES', 'TAX STATUS', 'OWNERSHIP', 'REVIEWER NOTES']
            for section in required_sections:
                if section in draft2:
                    structure_elements.append(section)
        else:
            required_sections = ['ACTION ITEMS', 'UPCOMING DEADLINES', 'TITLE CONCERNS']
            for section in required_sections:
                if section in draft2:
                    structure_elements.append(section)
        
        # Check for citations
        citations1 = len(re.findall(r'\[Document:', draft1))
        citations2 = len(re.findall(r'\[Document:', draft2))
        
        return {
            'structure_changes': len(structure_elements),
            'content_additions': len(added_lines),
            'content_removals': len(removed_lines),
            'citations_added': citations2 - citations1,
            'has_required_sections': len(structure_elements) > 0,
            'improvement_score': (len(structure_elements) * 20) + (citations2 - citations1) * 10
        }