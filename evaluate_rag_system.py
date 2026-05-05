"""
RAG System Evaluation Runner

This script evaluates the RAG system using the custom evaluation framework.
It uploads the evaluation document, runs queries, and measures performance.
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.document_loader import DocumentLoader
from app.services.chunker import TextChunker
from app.services.vector_store import VectorStore
from app.services.llm_service import LLMService
from evaluation_dataset import EVALUATION_DATASET
from rag_evaluator import RAGEvaluator

# Load environment variables
load_dotenv()


class RAGSystemEvaluator:
    """Evaluates the complete RAG system end-to-end."""
    
    def __init__(self, collection_name: str = "eval_collection"):
        """
        Initialize the RAG system evaluator.
        
        Args:
            collection_name: Name of the vector store collection to use
        """
        self.collection_name = collection_name
        self.document_loader = DocumentLoader()
        self.chunker = TextChunker()
        self.vector_store = VectorStore(collection_name=collection_name)
        self.llm_service = LLMService()
        self.evaluator = RAGEvaluator()
        
    def setup_evaluation_document(self, doc_path: str) -> bool:
        """
        Load and index the evaluation document.
        
        Args:
            doc_path: Path to the evaluation document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Loading document: {doc_path}")
            
            # Clear existing collection
            self.vector_store.clear_collection()
            
            # Load document
            content = self.document_loader.load_document(doc_path)
            print(f"  Document loaded: {len(content)} characters")
            
            # Chunk document
            chunks = self.chunker.chunk_text(
                content,
                chunk_size=500,
                chunk_overlap=50
            )
            print(f"  Created {len(chunks)} chunks")
            
            # Add to vector store
            self.vector_store.add_documents(
                documents=chunks,
                metadatas=[{"source": doc_path, "chunk_id": i} for i in range(len(chunks))]
            )
            print(f"  Indexed {len(chunks)} chunks in vector store")
            
            return True
            
        except Exception as e:
            print(f"Error setting up evaluation document: {e}")
            return False
    
    def query_rag_system(self, question: str, use_hybrid: bool = True) -> dict:
        """
        Query the RAG system and return answer with context.
        
        Args:
            question: Question to ask
            use_hybrid: Whether to use hybrid search (default: True)
            
        Returns:
            Dictionary with answer and context chunks
        """
        try:
            # Retrieve relevant chunks
            if use_hybrid:
                results = self.vector_store.hybrid_search(
                    query=question,
                    k=4,
                    initial_k=10
                )
            else:
                results = self.vector_store.search(query=question, k=4)
            
            # Extract chunks and metadata
            context_chunks = [doc["document"] for doc in results]
            
            # Generate answer
            answer = self.llm_service.answer_question(
                question=question,
                context_chunks=context_chunks,
                chat_history=[]
            )
            
            return {
                "answer": answer,
                "context_chunks": context_chunks,
                "num_chunks": len(context_chunks)
            }
            
        except Exception as e:
            print(f"  Error querying RAG system: {e}")
            return {
                "answer": f"Error: {str(e)}",
                "context_chunks": [],
                "num_chunks": 0
            }
    
    def run_evaluation(self, use_hybrid: bool = True) -> dict:
        """
        Run full evaluation on the dataset.
        
        Args:
            use_hybrid: Whether to use hybrid search
            
        Returns:
            Aggregated evaluation results
        """
        print(f"\nRunning evaluation with {'HYBRID' if use_hybrid else 'VECTOR-ONLY'} search...")
        print("=" * 80)
        
        results = []
        
        for i, item in enumerate(EVALUATION_DATASET, 1):
            print(f"\n[{i}/{len(EVALUATION_DATASET)}] {item['question'][:60]}...")
            
            # Query the system
            response = self.query_rag_system(item["question"], use_hybrid=use_hybrid)
            
            # Evaluate the response
            eval_result = self.evaluator.evaluate_single_query(
                question=item["question"],
                answer=response["answer"],
                context_chunks=response["context_chunks"],
                ground_truth=item
            )
            
            results.append(eval_result)
            
            # Brief status
            print(f"    Faithfulness: {eval_result['faithfulness']['score']:.1%} | "
                  f"Relevance: {eval_result['answer_relevance']['score']:.1%} | "
                  f"Precision: {eval_result['context_precision']['score']:.1%} | "
                  f"Recall: {eval_result['context_recall']['score']:.1%}")
        
        # Aggregate results
        aggregated = self.evaluator.aggregate_results(results)
        
        return {
            "aggregated": aggregated,
            "detailed_results": results
        }
    
    def save_results(self, results: dict, output_file: str = "evaluation_results.txt"):
        """
        Save evaluation results to a file.
        
        Args:
            results: Evaluation results
            output_file: Output file path
        """
        with open(output_file, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("RAG SYSTEM EVALUATION RESULTS\n")
            f.write("=" * 80 + "\n\n")
            
            aggregated = results["aggregated"]
            overall = aggregated["overall"]
            
            f.write(f"OVERALL METRICS (n={overall['total_queries']})\n")
            f.write("-" * 80 + "\n")
            f.write(f"Faithfulness:       {overall['faithfulness']:.1%}\n")
            f.write(f"Answer Relevance:   {overall['answer_relevance']:.1%}\n")
            f.write(f"Context Precision:  {overall['context_precision']:.1%}\n")
            f.write(f"Context Recall:     {overall['context_recall']:.1%}\n\n")
            
            f.write("BY CATEGORY\n")
            f.write("-" * 80 + "\n")
            for category, metrics in sorted(aggregated["by_category"].items()):
                f.write(f"\n{category.upper()} (n={metrics['count']})\n")
                f.write(f"  Faithfulness:       {metrics['faithfulness']:.1%}\n")
                f.write(f"  Answer Relevance:   {metrics['answer_relevance']:.1%}\n")
                f.write(f"  Context Precision:  {metrics['context_precision']:.1%}\n")
                f.write(f"  Context Recall:     {metrics['context_recall']:.1%}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("DETAILED RESULTS\n")
            f.write("=" * 80 + "\n\n")
            
            for i, result in enumerate(results["detailed_results"], 1):
                f.write(f"\n[{i}] {result['question']}\n")
                f.write(f"Category: {result['category']}\n")
                f.write(f"Answer: {result['answer'][:200]}...\n")
                f.write(f"Metrics:\n")
                f.write(f"  - Faithfulness: {result['faithfulness']['score']:.1%} "
                       f"({result['faithfulness']['grounded_sentences']}/{result['faithfulness']['total_sentences']} sentences grounded)\n")
                f.write(f"  - Answer Relevance: {result['answer_relevance']['score']:.1%}\n")
                f.write(f"  - Context Precision: {result['context_precision']['score']:.1%} "
                       f"({result['context_precision']['relevant_chunks']}/{result['context_precision']['total_chunks']} chunks relevant)\n")
                f.write(f"  - Context Recall: {result['context_recall']['score']:.1%} "
                       f"({result['context_recall']['found_keywords']}/{result['context_recall']['total_keywords']} keywords found)\n")
                f.write("-" * 80 + "\n")
        
        print(f"\nResults saved to: {output_file}")


def main():
    """Main evaluation function."""
    print("=" * 80)
    print("RAG SYSTEM EVALUATION")
    print("=" * 80)
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables")
        return
    
    # Initialize evaluator
    evaluator = RAGSystemEvaluator(collection_name="ml_eval_collection")
    
    # Setup evaluation document
    doc_path = "data/test_files/ml_evaluation_doc.txt"
    if not Path(doc_path).exists():
        print(f"Error: Evaluation document not found: {doc_path}")
        return
    
    success = evaluator.setup_evaluation_document(doc_path)
    if not success:
        print("Failed to setup evaluation document")
        return
    
    # Run evaluation with hybrid search
    print("\n" + "=" * 80)
    print("RUNNING EVALUATION")
    print("=" * 80)
    
    start_time = time.time()
    results = evaluator.run_evaluation(use_hybrid=True)
    elapsed = time.time() - start_time
    
    # Print results
    evaluator.evaluator.print_results(results["aggregated"])
    
    print(f"\nTotal evaluation time: {elapsed:.1f} seconds")
    print(f"Average time per query: {elapsed / len(EVALUATION_DATASET):.1f} seconds")
    
    # Save results
    evaluator.save_results(results, "evaluation_results.txt")
    
    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
