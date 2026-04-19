# src/retrieval/simple_retriever.py
"""Simple retriever without ChromaDB to avoid compatibility issues."""
import numpy as np
from typing import List, Dict, Any, Tuple
import openai
from src.config import Config


class SimpleRetriever:
    """Simple vector retriever using NumPy and OpenAI embeddings."""
    
    def __init__(self):
        """Initialize the retriever."""
        openai.api_key = Config.OPENAI_API_KEY
        self.chunks = []  # List of (text, metadata)
        self.embeddings = []  # List of embeddings
        self.is_indexed = False
        
    def index_documents(self, processed_docs: Dict[str, Dict]) -> None:
        """
        Index processed documents for retrieval.
        
        Args:
            processed_docs: Dictionary of processed documents
        """
        print("  Creating chunks from documents...")
        chunks = []
        
        for doc_name, doc_content in processed_docs.items():
            # Create chunks based on document type
            doc_chunks = self._create_chunks(doc_name, doc_content)
            chunks.extend(doc_chunks)
        
        print(f"  Created {len(chunks)} chunks")
        
        if not chunks:
            print("  Warning: No chunks created")
            return
        
        # Store chunks
        self.chunks = chunks
        
        # Generate embeddings for all chunks
        print("  Generating embeddings...")
        texts = [chunk['text'] for chunk in chunks]
        
        try:
            # Process in batches to avoid rate limits
            batch_size = 20
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                # Use older OpenAI API syntax
                response = openai.Embedding.create(
                    model=Config.EMBEDDING_MODEL,
                    input=batch
                )
                batch_embeddings = [item['embedding'] for item in response['data']]
                all_embeddings.extend(batch_embeddings)
                
                print(f"    Processed batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            
            self.embeddings = np.array(all_embeddings)
            self.is_indexed = True
            print(f"  ✓ Successfully indexed {len(self.chunks)} chunks")
            
        except Exception as e:
            print(f"  Error generating embeddings: {e}")
            self.is_indexed = False
    
    def _create_chunks(self, doc_name: str, doc_content: Dict) -> List[Dict]:
        """Create chunks from document content."""
        chunks = []
        
        if doc_content['type'] == 'title_search':
            # Add cleaned text as chunks
            if 'cleaned_text' in doc_content and doc_content['cleaned_text']:
                # Split into paragraphs
                paragraphs = doc_content['cleaned_text'].split('\n\n')
                for i, para in enumerate(paragraphs):
                    if len(para.strip()) > 50:  # Only keep substantial paragraphs
                        chunks.append({
                            'id': f"{doc_name}_para_{i}",
                            'text': para.strip(),
                            'metadata': {
                                'source': doc_name,
                                'type': 'title_search',
                                'section': 'cleaned_text'
                            }
                        })
            
            # Add lien chunks
            for idx, lien in enumerate(doc_content.get('liens', [])):
                lien_text = f"Lien: {lien.get('type', 'unknown')} - Amount: {lien.get('amount', 'unknown')} - Instrument: {lien.get('instrument_number', 'unknown')}"
                chunks.append({
                    'id': f"{doc_name}_lien_{idx}",
                    'text': lien_text,
                    'metadata': {
                        'source': doc_name,
                        'type': 'lien',
                        'instrument': lien.get('instrument_number', '')
                    }
                })
        
        elif doc_content['type'] == 'email':
            # Split email into sections
            text = doc_content.get('text', '')
            # Split by double newlines
            sections = text.split('\n\n')
            for i, section in enumerate(sections):
                if len(section.strip()) > 50:
                    chunks.append({
                        'id': f"{doc_name}_section_{i}",
                        'text': section.strip(),
                        'metadata': {
                            'source': doc_name,
                            'type': 'email'
                        }
                    })
            
            # Add action items
            for idx, action in enumerate(doc_content.get('action_items', [])):
                action_text = f"Action Item ({action.get('priority', 'NORMAL')}): {action.get('action', '')} - {action.get('details', '')}"
                chunks.append({
                    'id': f"{doc_name}_action_{idx}",
                    'text': action_text,
                    'metadata': {
                        'source': doc_name,
                        'type': 'action_item',
                        'priority': action.get('priority', 'NORMAL')
                    }
                })
        
        elif doc_content['type'] == 'court_order':
            # Split court order
            text = doc_content.get('text', '')
            sections = text.split('\n\n')
            for i, section in enumerate(sections):
                if len(section.strip()) > 50:
                    chunks.append({
                        'id': f"{doc_name}_section_{i}",
                        'text': section.strip(),
                        'metadata': {
                            'source': doc_name,
                            'type': 'court_order'
                        }
                    })
            
            # Add deadlines
            for deadline in doc_content.get('deadlines', []):
                deadline_text = f"Deadline: {deadline.get('type', 'unknown')} - {deadline.get('date', 'unknown')} - {deadline.get('action_required', '')}"
                chunks.append({
                    'id': f"{doc_name}_deadline_{deadline.get('type', 'unknown')}",
                    'text': deadline_text,
                    'metadata': {
                        'source': doc_name,
                        'type': 'deadline',
                        'date': deadline.get('date', '')
                    }
                })
        
        # Ensure we have at least some chunks
        if not chunks and 'text' in doc_content:
            # Fallback: add the whole document as one chunk
            chunks.append({
                'id': f"{doc_name}_full",
                'text': doc_content['text'][:2000],  # Limit length
                'metadata': {
                    'source': doc_name,
                    'type': doc_content['type']
                }
            })
        
        return chunks
    
    def retrieve_relevant_context(self, query: str, top_k: int = None) -> List[Tuple[str, Dict]]:
        """
        Retrieve relevant document chunks for a query.
        
        Args:
            query: Search query
            top_k: Number of chunks to retrieve
            
        Returns:
            List of (chunk_text, metadata) tuples
        """
        if top_k is None:
            top_k = Config.TOP_K_CHUNKS
        
        if not self.is_indexed or len(self.chunks) == 0:
            print(f"  Warning: No indexed chunks available for query: {query}")
            return []
        
        try:
            # Generate embedding for the query using older API
            response = openai.Embedding.create(
                model=Config.EMBEDDING_MODEL,
                input=[query]
            )
            query_embedding = np.array(response['data'][0]['embedding'])
            
            # Calculate similarities
            similarities = np.dot(self.embeddings, query_embedding)
            
            # Get top-k indices
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            # Return top chunks
            retrieved = []
            for idx in top_indices:
                if similarities[idx] > 0.3:  # Only return reasonably similar chunks
                    retrieved.append((self.chunks[idx]['text'], self.chunks[idx]['metadata']))
            
            return retrieved
            
        except Exception as e:
            print(f"  Error during retrieval: {e}")
            return []
    
    def get_all_chunks(self) -> List[Dict]:
        """Get all indexed chunks."""
        return self.chunks