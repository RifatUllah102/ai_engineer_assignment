# src/generation/draft_generator.py
"""Generate grounded drafts from retrieved context."""
import json
from typing import List, Dict, Any, Tuple
import openai
from src.config import Config


class DraftGenerator:
    """Generate structured drafts based on retrieved context."""
    
    def __init__(self):
        openai.api_key = Config.OPENAI_API_KEY
        self.learning_preferences = {}  # Store learned patterns from edits
    
    def generate_title_review_summary(self, retrieved_chunks: List[Tuple[str, Dict]], 
                                      case_context: Dict,
                                      apply_learnings: bool = False) -> Dict[str, Any]:
        """
        Generate a title review summary.
        
        Args:
            retrieved_chunks: Retrieved document chunks
            case_context: Case context information
            apply_learnings: Whether to apply learned patterns from edits
            
        Returns:
            Generated draft with citations
        """
        # Prepare context
        context_text = self._format_retrieved_chunks(retrieved_chunks)
        
        # Build prompt with or without learned patterns
        if apply_learnings and self.learning_preferences.get('title_review'):
            system_prompt = self._build_title_prompt_with_learnings()
        else:
            system_prompt = self._build_title_prompt_default()
        
        user_prompt = f"""
Case Context:
- Case Number: {case_context.get('case_number', 'Unknown')}
- Borrower: {case_context.get('borrower', 'Unknown')}
- Property: {case_context.get('property_address', 'Unknown')}
- County: {case_context.get('county', 'Unknown')}
- State: {case_context.get('state', 'Unknown')}

Retrieved Document Sections:
{context_text}

Generate a Title Review Summary following the required structure. For each piece of information, cite the source document in brackets [Document: X, Section: Y].
"""
        
        # Use older OpenAI API syntax
        response = openai.ChatCompletion.create(
            model=Config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        
        draft = response['choices'][0]['message']['content']
        
        # Extract citations for grounding verification
        citations = self._extract_citations(draft)
        
        return {
            'draft_type': 'title_review_summary',
            'content': draft,
            'citations': citations,
            'learnings_applied': apply_learnings
        }
    
    def generate_case_status_memo(self, retrieved_chunks: List[Tuple[str, Dict]],
                                 case_context: Dict,
                                 apply_learnings: bool = False) -> Dict[str, Any]:
        """
        Generate a case status memo.
        
        Args:
            retrieved_chunks: Retrieved document chunks
            case_context: Case context information
            apply_learnings: Whether to apply learned patterns from edits
            
        Returns:
            Generated draft with citations
        """
        # Prepare context
        context_text = self._format_retrieved_chunks(retrieved_chunks)
        
        # Build prompt with or without learned patterns
        if apply_learnings and self.learning_preferences.get('case_status'):
            system_prompt = self._build_memo_prompt_with_learnings()
        else:
            system_prompt = self._build_memo_prompt_default()
        
        user_prompt = f"""
Case Context:
{json.dumps(case_context, indent=2)}

Retrieved Document Sections:
{context_text}

Generate a Case Status Memo following the required structure. Prioritize action items and cross-reference deadlines across documents. Cite all sources.
"""
        
        # Use older OpenAI API syntax
        response = openai.ChatCompletion.create(
            model=Config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        
        draft = response['choices'][0]['message']['content']
        
        # Extract citations
        citations = self._extract_citations(draft)
        
        return {
            'draft_type': 'case_status_memo',
            'content': draft,
            'citations': citations,
            'learnings_applied': apply_learnings
        }
    
    def _format_retrieved_chunks(self, chunks: List[Tuple[str, Dict]]) -> str:
        """Format retrieved chunks for prompt context."""
        if not chunks:
            return "No relevant document sections found. Please use available case context only."
        
        formatted = []
        for i, (text, metadata) in enumerate(chunks, 1):
            source = metadata.get('source', 'Unknown')
            doc_type = metadata.get('type', 'unknown')
            formatted.append(f"[Chunk {i}] Source: {source} (Type: {doc_type})\n{text}\n")
        
        return '\n'.join(formatted)
    
    def _build_title_prompt_default(self) -> str:
        """Default system prompt for title review."""
        return """You are a legal document assistant specializing in title searches. Generate a title review summary that is:
1. GROUNDED: Only include information from the provided document chunks
2. CITED: Cite sources using [Document: X] format
3. STRUCTURED: Include the following sections:
   - Header (property, county, state)
   - Liens & Encumbrances (mortgages, assignments, HOA liens)
   - Tax Status
   - Ownership Chain
   - Other Matters (easements, covenants)
4. ACCURATE: If information is not in the chunks, state "Not found in documents"

Do not fabricate information. Do not add legal analysis beyond what's in the documents."""
    
    def _build_title_prompt_with_learnings(self) -> str:
        """Enhanced system prompt with learned patterns from operator edits."""
        learnings = self.learning_preferences.get('title_review', {})
        
        return f"""You are a legal document assistant specializing in title searches. Generate a title review summary that incorporates the following operator preferences:

LEARNED PATTERNS:
- Use labeled sections: LIENS & ENCUMBRANCES, TAX STATUS, OWNERSHIP, OTHER MATTERS, REVIEWER NOTES
- Include instrument numbers and recording details for all liens
- Flag action items with ACTION REQUIRED labels
- Add reviewer notes section with actionable items
- Cross-reference information from other documents when available

Follow these requirements:
1. GROUNDED: Only include information from provided chunks
2. CITED: Cite all sources with [Document: X]
3. STRUCTURED: Use the labeled sections mentioned above
4. ACCURATE: If information missing, state "Not found"

Do not fabricate information."""
    
    def _build_memo_prompt_default(self) -> str:
        """Default system prompt for case status memo."""
        return """You are a legal case assistant. Generate a case status memo that:
1. Prioritizes action items (URGENT, HIGH, NORMAL)
2. Cross-references deadlines across all documents
3. Includes court details (judge, courtroom, case number)
4. Adds borrower's counsel information when available
5. Makes deadlines actionable (not just dates but required actions)
6. Cites all sources with [Document: X]

Only include information from provided document chunks. Do not fabricate."""
    
    def _build_memo_prompt_with_learnings(self) -> str:
        """Enhanced system prompt with learned patterns."""
        return """You are a legal case assistant. Generate a case status memo that incorporates:

LEARNED PATTERNS:
- Start with ACTION ITEMS section with priority levels (URGENT, HIGH, NORMAL)
- Include UPCOMING DEADLINES with specific required actions
- Add TITLE CONCERNS section when relevant
- Include court details (judge, courtroom, case number)
- Add borrower's counsel contact information
- Cross-reference information across all documents

Requirements:
1. GROUNDED in provided chunks only
2. CITED with [Document: X]
3. ACTIONABLE - tell what needs to be done
4. ACCURATE - don't fabricate

Do not add information not in the source documents."""
    
    def _extract_citations(self, draft: str) -> List[str]:
        """Extract citations from draft text."""
        import re
        citations = re.findall(r'\[Document:[^\]]+\]', draft)
        return list(set(citations))  # Return unique citations