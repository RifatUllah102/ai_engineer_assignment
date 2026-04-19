# src/retrieval/vector_store.py
"""Vector store for document retrieval."""
import os
from typing import List, Dict, Any, Tuple
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from openai import OpenAI
from src.config import Config


class OpenAIEmbeddingFunction(EmbeddingFunction):
    """Custom OpenAI embedding function to avoid compatibility issues."""
    
    def __init__(self, api_key: str, model_name: str = "text-embedding-3-small"):
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
    
    def __call__(self, input: Documents) -> Embeddings:
        """Generate embeddings for input documents."""
        # Ensure input is a list
        if isinstance(input, str):
            input = [input]
        
        # Handle empty input
        if not input:
            return []
        
        # Generate embeddings
        response = self.client.embeddings.create(
            model=self.model_name,
            input=input
        )
        
        # Extract embeddings
        embeddings = [item.embedding for item in response.data]
        return embeddings


class DocumentRetriever:
    """Handle document indexing and retrieval."""
    
    def __init__(self):
        """Initialize ChromaDB client and embedding function."""
        # Use persistent client to avoid issues
        self.client = chromadb.PersistentClient(path="./chromadb_data")
        
        # Create custom embedding function
        self.embedding_fn = OpenAIEmbeddingFunction(
            api_key=Config.OPENAI_API_KEY,
            model_name=Config.EMBEDDING_MODEL
        )
        
        # Delete existing collection if it exists to avoid conflicts
        try:
            self.client.delete_collection("legal_documents")
        except:
            pass
        
        # Create or get collection
        self.collection = self.client.create_collection(
            name="legal_documents",
            embedding_function=self.embedding_fn
        )
        
        self.chunks = []  # Store chunk metadata
        self.chunk_counter = 0
    
    def index_documents(self, processed_docs: Dict[str, Dict]) -> None:
        """
        Index processed documents for retrieval.
        
        Args:
            processed_docs: Dictionary of processed documents
        """
        for doc_name, doc_content in processed_docs.items():
            # Create chunks based on document type
            chunks = self._create_chunks(doc_name, doc_content)
            
            # Add to vector store in batches
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                
                if batch:
                    self.collection.add(
                        documents=[chunk['text'] for chunk in batch],
                        metadatas=[chunk['metadata'] for chunk in batch],
                        ids=[chunk['id'] for chunk in batch]
                    )
                    self.chunks.extend(batch)
    
    def _create_chunks(self, doc_name: str, doc_content: Dict) -> List[Dict]:
        """
        Create chunks from document content.
        
        Args:
            doc_name: Document identifier
            doc_content: Processed document content
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        
        if doc_content['type'] == 'title_search':
            # Chunk title search by sections
            if 'cleaned_text' in doc_content and doc_content['cleaned_text']:
                chunks.extend(self._chunk_text(
                    doc_content['cleaned_text'],
                    doc_name,
                    'cleaned_text'
                ))
            
            # Create structured chunks for liens
            for idx, lien in enumerate(doc_content.get('liens', [])):
                lien_text = f"Lien: {lien.get('type', 'unknown')} - Amount: {lien.get('amount', 'unknown')} - Instrument: {lien.get('instrument_number', 'unknown')}"
                chunks.append({
                    'id': f"{doc_name}_lien_{idx}_{len(chunks)}",
                    'text': lien_text,
                    'metadata': {
                        'source': doc_name,
                        'type': 'lien',
                        'instrument': lien.get('instrument_number', '')
                    }
                })
            
            # Create structured chunks for taxes
            for year, tax_info in doc_content.get('taxes', {}).items():
                if isinstance(tax_info, dict) and year not in ['parcel_number']:
                    tax_text = f"Tax Year {year}: {tax_info.get('status', 'unknown')} - Amount: {tax_info.get('amount', 'unknown')}"
                    chunks.append({
                        'id': f"{doc_name}_tax_{year}_{len(chunks)}",
                        'text': tax_text,
                        'metadata': {
                            'source': doc_name,
                            'type': 'tax',
                            'year': year
                        }
                    })
        
        elif doc_content['type'] == 'email':
            # Chunk email content
            if doc_content.get('text'):
                chunks.extend(self._chunk_text(
                    doc_content['text'],
                    doc_name,
                    'full_text'
                ))
            
            # Create action item chunks
            for idx, action in enumerate(doc_content.get('action_items', [])):
                action_text = f"Action Item ({action.get('priority', 'NORMAL')}): {action.get('action', '')} - {action.get('details', '')}"
                chunks.append({
                    'id': f"{doc_name}_action_{idx}_{len(chunks)}",
                    'text': action_text,
                    'metadata': {
                        'source': doc_name,
                        'type': 'action_item',
                        'priority': action.get('priority', 'NORMAL')
                    }
                })
        
        elif doc_content['type'] == 'court_order':
            # Chunk court order
            if doc_content.get('text'):
                chunks.extend(self._chunk_text(
                    doc_content['text'],
                    doc_name,
                    'full_text'
                ))
            
            # Create deadline chunks
            for deadline in doc_content.get('deadlines', []):
                deadline_text = f"Deadline: {deadline.get('type', 'unknown')} - {deadline.get('date', 'unknown')} - {deadline.get('action_required', '')}"
                chunks.append({
                    'id': f"{doc_name}_deadline_{deadline.get('type', 'unknown')}_{len(chunks)}",
                    'text': deadline_text,
                    'metadata': {
                        'source': doc_name,
                        'type': 'deadline',
                        'date': deadline.get('date', '')
                    }
                })
        
        # Ensure we have at least some chunks
        if not chunks:
            # Fallback: create a single chunk with the text
            fallback_text = str(doc_content)
            chunks = self._chunk_text(fallback_text, doc_name, 'fallback')
        
        return chunks
    
    def _chunk_text(self, text: str, source: str, section: str) -> List[Dict]:
        """Chunk text into smaller pieces."""
        chunks = []
        
        if not text:
            return chunks
        
        # Simple chunking by character count
        words = text.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            current_length += len(word) + 1
            if current_length > Config.CHUNK_SIZE and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'id': f"{source}_{section}_{len(chunks)}",
                    'text': chunk_text,
                    'metadata': {
                        'source': source,
                        'section': section,
                        'chunk_id': len(chunks)
                    }
                })
                current_chunk = [word]
                current_length = len(word) + 1
            else:
                current_chunk.append(word)
        
        # Add last chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'id': f"{source}_{section}_{len(chunks)}",
                'text': chunk_text,
                'metadata': {
                    'source': source,
                    'section': section,
                    'chunk_id': len(chunks)
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
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            retrieved = []
            if results['documents'] and results['metadatas']:
                for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                    retrieved.append((doc, metadata))
            
            return retrieved
        except Exception as e:
            print(f"Warning: Retrieval failed: {e}")
            return []
    
    def get_all_chunks(self) -> List[Dict]:
        """Get all indexed chunks."""
        return self.chunks