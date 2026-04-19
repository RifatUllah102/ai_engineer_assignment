# main.py
"""Main entry point for the document intelligence pipeline."""
import os
import json
import sys
from pathlib import Path
from src.config import Config
from src.processing.document_processor import DocumentProcessor
from src.retrieval.simple_retriever import SimpleRetriever
from src.generation.draft_generator import DraftGenerator
from src.learning.edit_learner import EditLearner


class DocumentIntelligencePipeline:
    """Main pipeline orchestrating all components."""
    
    def __init__(self):
        print("Initializing pipeline components...")
        self.processor = DocumentProcessor()
        self.retriever = SimpleRetriever()
        self.generator = DraftGenerator()
        self.learner = EditLearner()
        
    def run_full_pipeline(self):
        """Run the complete pipeline."""
        print("=" * 60)
        print("DOCUMENT INTELLIGENCE PIPELINE")
        print("=" * 60)
        
        # Step 1: Process documents
        print("\n📄 STEP 1: Processing Documents...")
        print("-" * 40)
        
        # Check if documents directory exists
        if not os.path.exists(Config.DOCUMENTS_DIR):
            print(f"ERROR: Documents directory not found: {Config.DOCUMENTS_DIR}")
            print("Please check your file paths.")
            return None
            
        processed_docs = self.processor.process_all_documents(Config.DOCUMENTS_DIR)
        
        if not processed_docs:
            print("ERROR: No documents were processed. Please check the documents directory.")
            return None
        
        # Display processing results
        for doc_name, doc_content in processed_docs.items():
            print(f"  ✓ Processed: {doc_name} ({doc_content['type']})")
            if doc_content['type'] == 'title_search':
                print(f"    - Liens found: {len(doc_content.get('liens', []))}")
                print(f"    - OCR cleaned: {'Yes' if 'cleaned_text' in doc_content else 'No'}")
            elif doc_content['type'] == 'email':
                print(f"    - Action items: {len(doc_content.get('action_items', []))}")
            elif doc_content['type'] == 'court_order':
                print(f"    - Deadlines: {len(doc_content.get('deadlines', []))}")
        
        # Step 2: Index documents for retrieval
        print("\n🔍 STEP 2: Indexing Documents for Retrieval...")
        print("-" * 40)
        
        try:
            self.retriever.index_documents(processed_docs)
        except Exception as e:
            print(f"  ⚠️  Warning: Could not index documents: {e}")
        
        # Step 3: Generate drafts
        print("\n📝 STEP 3: Generating Drafts...")
        print("-" * 40)
        
        # Load case context
        case_context_path = os.path.join(Config.DATA_DIR, "case_context.json")
        if not os.path.exists(case_context_path):
            print(f"ERROR: Case context not found: {case_context_path}")
            return None
            
        with open(case_context_path, 'r', encoding='utf-8') as f:
            case_context = json.load(f)
        
        # Generate Title Review Summary
        print("\n  Generating Title Review Summary...")
        title_query = "title search liens mortgages assignments ownership taxes"
        title_chunks = self.retriever.retrieve_relevant_context(title_query, top_k=5)
        print(f"    Retrieved {len(title_chunks)} relevant chunks")
        
        title_draft = self.generator.generate_title_review_summary(
            title_chunks, case_context, apply_learnings=False
        )
        print(f"  ✓ Title Review Summary generated ({len(title_draft['citations'])} citations)")
        
        # Generate Case Status Memo
        print("\n  Generating Case Status Memo...")
        memo_query = "deadlines action items servicer transfer court conference"
        memo_chunks = self.retriever.retrieve_relevant_context(memo_query, top_k=5)
        print(f"    Retrieved {len(memo_chunks)} relevant chunks")
        
        memo_draft = self.generator.generate_case_status_memo(
            memo_chunks, case_context, apply_learnings=False
        )
        print(f"  ✓ Case Status Memo generated ({len(memo_draft['citations'])} citations)")
        
        # Save initial drafts
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
        
        with open(f"{Config.OUTPUT_DIR}/initial_title_review.txt", 'w', encoding='utf-8') as f:
            f.write(title_draft['content'])
        
        with open(f"{Config.OUTPUT_DIR}/initial_case_status_memo.txt", 'w', encoding='utf-8') as f:
            f.write(memo_draft['content'])
        
        print(f"\n  💾 Initial drafts saved to {Config.OUTPUT_DIR}/")
        
        # Step 4: Learn from operator edits
        print("\n🎓 STEP 4: Learning from Operator Edits...")
        print("-" * 40)
        
        edits_path = os.path.join(Config.DATA_DIR, "sample_edits.json")
        if not os.path.exists(edits_path):
            print(f"Warning: Edits file not found: {edits_path}")
            print("Skipping learning step...")
        else:
            with open(edits_path, 'r', encoding='utf-8') as f:
                sample_edits = json.load(f)
            
            # Learn from each edit
            for edit in sample_edits:
                print(f"\n  Analyzing {edit['draft_type']} edits...")
                learnings = self.learner.learn_from_edit(edit)
                print(f"    ✓ Learned {len(learnings)} patterns")
                for key, value in list(learnings.items())[:3]:
                    print(f"      - {key}: {str(value)[:50]}...")
        
        # Step 5: Generate improved drafts
        print("\n✨ STEP 5: Generating Improved Drafts (with learnings)...")
        print("-" * 40)
        
        # Apply learnings to generator
        self.generator.learning_preferences = self.learner.get_all_learnings()
        
        # Generate improved Title Review
        print("\n  Generating IMPROVED Title Review Summary...")
        improved_title = self.generator.generate_title_review_summary(
            title_chunks, case_context, apply_learnings=True
        )
        
        # Generate improved Case Status Memo
        print("\n  Generating IMPROVED Case Status Memo...")
        improved_memo = self.generator.generate_case_status_memo(
            memo_chunks, case_context, apply_learnings=True
        )
        
        # Save improved drafts
        with open(f"{Config.OUTPUT_DIR}/improved_title_review.txt", 'w', encoding='utf-8') as f:
            f.write(improved_title['content'])
        
        with open(f"{Config.OUTPUT_DIR}/improved_case_status_memo.txt", 'w', encoding='utf-8') as f:
            f.write(improved_memo['content'])
        
        print(f"\n  💾 Improved drafts saved to {Config.OUTPUT_DIR}/")
        
        # Step 6: Generate comparison report
        print("\n📊 STEP 6: Generating Comparison Report...")
        print("-" * 40)
        
        comparison = self.learner.compare_drafts(
            title_draft['content'],
            improved_title['content'],
            "title_review"
        )
        
        print(f"\n  Title Review Improvements:")
        print(f"    - Structure changes: {comparison['structure_changes']}")
        print(f"    - Content additions: {comparison['content_additions']}")
        print(f"    - Improvement score: {comparison['improvement_score']}")
        
        # Save comparison
        with open(f"{Config.OUTPUT_DIR}/comparison_report.json", 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2)
        
        print("\n" + "=" * 60)
        print("✅ PIPELINE COMPLETE!")
        print(f"📁 All outputs saved to {Config.OUTPUT_DIR}/")
        print("=" * 60)
        
        return {
            'processed_docs': processed_docs,
            'initial_drafts': {'title': title_draft, 'memo': memo_draft},
            'improved_drafts': {'title': improved_title, 'memo': improved_memo},
            'learnings': self.learner.get_all_learnings(),
            'comparison': comparison
        }


if __name__ == "__main__":
    # Create necessary directories
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    
    # Run pipeline
    try:
        pipeline = DocumentIntelligencePipeline()
        results = pipeline.run_full_pipeline()
        
        if results:
            print("\n🎉 Pipeline execution successful!")
        else:
            print("\n❌ Pipeline execution failed. Check errors above.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)