"""
RAG System Evaluation via API

This script evaluates the RAG system by calling the API endpoints directly.
This avoids import issues and tests the system as users would use it.
"""

import os
import requests
import time
from pathlib import Path
from dotenv import load_dotenv
from evaluation_dataset import EVALUATION_DATASET
from rag_evaluator import RAGEvaluator

load_dotenv()

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
UPLOAD_ENDPOINT = f"{API_BASE_URL}/upload"
QUERY_ENDPOINT = f"{API_BASE_URL}/query"


class APIBasedEvaluator:
    """Evaluates RAG system through API calls."""
    
    def __init__(self):
        """Initialize the evaluator."""
        self.evaluator = RAGEvaluator()
        self.collection_name = "ml_eval_collection"
        self.document_id = None
    
    def check_server(self) -> bool:
        """Check if the server is running."""
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def upload_document(self, file_path: str) -> bool:
        """
        Upload the evaluation document to the RAG system.
        
        Args:
            file_path: Path to the document
            
        Returns:
            True if successful
        """
        print(f"Uploading document: {file_path}")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (Path(file_path).name, f, 'text/plain')}
                data = {
                    'collection_name': self.collection_name,
                    'chunk_size': 500,
                    'chunk_overlap': 50
                }
                
                response = requests.post(UPLOAD_ENDPOINT, files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    self.document_id = result.get('document_id')
                    print(f"  ✓ Document uploaded successfully (ID: {self.document_id})")
                    print(f"  ✓ Created {result.get('chunks_count', 0)} chunks")
                    return True
                else:
                    print(f"  ✗ Upload failed: {response.status_code}")
                    print(f"  Response: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"  ✗ Error uploading document: {e}")
            return False
    
    def query_system(self, question: str) -> dict:
        """
        Query the RAG system.
        
        Args:
            question: Question to ask
            
        Returns:
            Dictionary with answer and context
        """
        try:
            payload = {
                "query": question,
                "collection_name": self.collection_name,
                "chat_history": []
            }
            
            response = requests.post(QUERY_ENDPOINT, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "answer": result.get("answer", ""),
                    "context_chunks": [source["content"] for source in result.get("sources", [])]
                }
            else:
                print(f"  ✗ Query failed: {response.status_code}")
                return {
                    "answer": f"Error: {response.status_code}",
                    "context_chunks": []
                }
                
        except Exception as e:
            print(f"  ✗ Error querying system: {e}")
            return {
                "answer": f"Error: {str(e)}",
                "context_chunks": []
            }
    
    def run_evaluation(self) -> dict:
        """
        Run full evaluation on the dataset.
        
        Returns:
            Evaluation results
        """
        print("\n" + "=" * 80)
        print("RUNNING RAG EVALUATION VIA API")
        print("=" * 80)
        
        results = []
        
        for i, item in enumerate(EVALUATION_DATASET, 1):
            print(f"\n[{i}/{len(EVALUATION_DATASET)}] {item['question'][:60]}...")
            
            # Query the system
            response = self.query_system(item["question"])
            
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
            
            # Small delay between requests
            time.sleep(0.5)
        
        # Aggregate results
        aggregated = self.evaluator.aggregate_results(results)
        
        return {
            "aggregated": aggregated,
            "detailed_results": results
        }
    
    def save_results(self, results: dict, output_file: str = "api_evaluation_results.txt"):
        """Save evaluation results to a file."""
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("RAG SYSTEM EVALUATION RESULTS (API-Based)\n")
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
        
        print(f"\n✓ Results saved to: {output_file}")


def main():
    """Main function."""
    print("=" * 80)
    print("RAG SYSTEM EVALUATION (API-Based)")
    print("=" * 80)
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("✗ Error: OPENAI_API_KEY not found in environment variables")
        print("  Please set your OpenAI API key in the .env file")
        return
    
    # Initialize evaluator
    evaluator = APIBasedEvaluator()
    
    # Check if server is running
    print("\nChecking if server is running...")
    if not evaluator.check_server():
        print("✗ Server is not running!")
        print("\nPlease start the server first:")
        print("  python start_server.py")
        print("\nOr in a separate terminal:")
        print("  uvicorn main:app --reload --port 8000")
        return
    print("✓ Server is running")
    
    # Upload evaluation document
    doc_path = "data/test_files/ml_evaluation_doc.txt"
    if not Path(doc_path).exists():
        print(f"✗ Error: Evaluation document not found: {doc_path}")
        return
    
    if not evaluator.upload_document(doc_path):
        print("✗ Failed to upload evaluation document")
        return
    
    # Run evaluation
    print("\n" + "=" * 80)
    print("STARTING EVALUATION")
    print("=" * 80)
    
    start_time = time.time()
    results = evaluator.run_evaluation()
    elapsed = time.time() - start_time
    
    # Print results
    evaluator.evaluator.print_results(results["aggregated"])
    
    print(f"\nTotal evaluation time: {elapsed:.1f} seconds")
    print(f"Average time per query: {elapsed / len(EVALUATION_DATASET):.1f} seconds")
    
    # Save results
    evaluator.save_results(results)
    
    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Review the results in api_evaluation_results.txt")
    print("2. Use these metrics in interviews:")
    print(f"   - 'I achieved {results['aggregated']['overall']['faithfulness']:.0%} faithfulness'")
    print(f"   - 'I implemented hybrid search with {results['aggregated']['overall']['context_precision']:.0%} precision'")
    print("3. If scores are low, iterate on:")
    print("   - Chunk size and overlap")
    print("   - Number of retrieved documents")
    print("   - Reranker model")
    print("=" * 80)


if __name__ == "__main__":
    main()
