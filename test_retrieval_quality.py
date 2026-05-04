"""
Retrieval Quality Comparison Test
Demonstrates the improvement from hybrid search + reranking vs. basic vector search.

This script compares:
- Baseline: Pure vector (semantic) search
- Improved: Hybrid search (vector + BM25 + cross-encoder reranking)
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.vector_store import VectorStore
from app.services.chunker import chunk_text


# Sample documents for testing
SAMPLE_DOCUMENTS = [
    {
        "title": "Machine Learning Basics",
        "text": """
        Machine learning is a subset of artificial intelligence that enables computers to learn 
        from data without being explicitly programmed. It uses algorithms to identify patterns 
        and make predictions. Common types include supervised learning, unsupervised learning, 
        and reinforcement learning. Deep learning is a subfield that uses neural networks with 
        multiple layers.
        """
    },
    {
        "title": "Python Programming",
        "text": """
        Python is a high-level programming language known for its simplicity and readability. 
        It supports multiple programming paradigms including procedural, object-oriented, and 
        functional programming. Python has extensive libraries for data science, web development, 
        and automation. Popular frameworks include Django, Flask, NumPy, and Pandas.
        """
    },
    {
        "title": "Data Science Process",
        "text": """
        The data science process typically involves collecting data, cleaning and preprocessing, 
        exploratory data analysis, feature engineering, model building, and evaluation. It requires 
        knowledge of statistics, programming, and domain expertise. Tools commonly used include 
        Python, R, SQL, and various visualization libraries.
        """
    },
    {
        "title": "Neural Networks",
        "text": """
        Neural networks are computing systems inspired by biological neural networks. They consist 
        of interconnected nodes (neurons) organized in layers. Input layer receives data, hidden 
        layers process information, and output layer produces results. Training involves adjusting 
        weights through backpropagation to minimize error.
        """
    },
    {
        "title": "Cloud Computing",
        "text": """
        Cloud computing delivers computing services over the internet including servers, storage, 
        databases, networking, and software. Major providers include AWS, Azure, and Google Cloud. 
        Benefits include scalability, cost efficiency, and accessibility. Common models are IaaS, 
        PaaS, and SaaS.
        """
    }
]


# Test queries with expected relevant documents
TEST_QUERIES = [
    {
        "query": "What is backpropagation in neural networks?",
        "expected_docs": ["Neural Networks"],
        "description": "Technical keyword search - should find exact technical term"
    },
    {
        "query": "How do I analyze data with Python?",
        "expected_docs": ["Python Programming", "Data Science Process"],
        "description": "Multi-concept query - needs both Python AND data analysis"
    },
    {
        "query": "What are the benefits of using cloud services?",
        "expected_docs": ["Cloud Computing"],
        "description": "Semantic understanding - 'benefits' vs 'advantages'"
    },
    {
        "query": "supervised learning algorithms",
        "expected_docs": ["Machine Learning Basics"],
        "description": "Specific terminology - exact phrase matching important"
    },
    {
        "query": "layers in deep learning models",
        "expected_docs": ["Neural Networks", "Machine Learning Basics"],
        "description": "Cross-document concept - related to both neural nets and ML"
    }
]


def setup_test_collection():
    """Create a test vector store with sample documents."""
    print("=" * 80)
    print("SETUP: Creating test collection")
    print("=" * 80)
    
    # Create vector store
    vector_store = VectorStore(
        collection_name="retrieval_test",
        persist_directory="./test_chroma_db",
        use_openai_embeddings=False  # Use free sentence transformers
    )
    
    # Clear existing data
    try:
        vector_store.clear_collection()
    except:
        pass
    
    # Add documents
    all_chunks = []
    all_metadata = []
    all_ids = []
    
    for i, doc in enumerate(SAMPLE_DOCUMENTS):
        # Chunk the text
        chunks = chunk_text(doc["text"], chunk_size=200, chunk_overlap=20)
        
        for j, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadata.append({
                "source": doc["title"],
                "chunk_index": j,
                "total_chunks": len(chunks)
            })
            all_ids.append(f"doc_{i}_chunk_{j}")
    
    # Add to vector store
    vector_store.add_documents(all_chunks, metadata=all_metadata, ids=all_ids)
    
    print(f"\n✓ Added {len(all_chunks)} chunks from {len(SAMPLE_DOCUMENTS)} documents")
    return vector_store


def evaluate_retrieval(results, expected_docs, top_k=3):
    """
    Evaluate retrieval quality.
    
    Returns:
        dict with precision, recall, and found documents
    """
    # Get top k result sources
    retrieved_sources = set()
    for i, result in enumerate(results[:top_k]):
        source = result.get('metadata', {}).get('source', '')
        retrieved_sources.add(source)
    
    # Calculate metrics
    expected_set = set(expected_docs)
    true_positives = len(retrieved_sources & expected_set)
    
    precision = true_positives / len(retrieved_sources) if retrieved_sources else 0
    recall = true_positives / len(expected_set) if expected_set else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "retrieved": list(retrieved_sources),
        "expected": list(expected_set),
        "matches": list(retrieved_sources & expected_set)
    }


def run_comparison_test():
    """Run the retrieval quality comparison."""
    print("\n" + "=" * 80)
    print("RETRIEVAL QUALITY COMPARISON TEST")
    print("=" * 80)
    
    # Setup
    vector_store = setup_test_collection()
    
    # Results tracking
    baseline_scores = []
    hybrid_scores = []
    
    # Test each query
    for i, test in enumerate(TEST_QUERIES):
        print("\n" + "-" * 80)
        print(f"TEST {i+1}: {test['description']}")
        print(f"Query: \"{test['query']}\"")
        print(f"Expected documents: {', '.join(test['expected_docs'])}")
        print("-" * 80)
        
        # Baseline: Vector search only
        print("\n[BASELINE] Vector Search Only")
        baseline_results = vector_store.search(query=test['query'], k=10)
        baseline_eval = evaluate_retrieval(baseline_results, test['expected_docs'])
        baseline_scores.append(baseline_eval)
        
        print(f"  Retrieved: {', '.join(baseline_eval['retrieved'][:3])}")
        print(f"  Matches: {', '.join(baseline_eval['matches']) if baseline_eval['matches'] else 'None'}")
        print(f"  Precision@3: {baseline_eval['precision']:.2f}")
        print(f"  Recall@3: {baseline_eval['recall']:.2f}")
        print(f"  F1@3: {baseline_eval['f1']:.2f}")
        
        # Improved: Hybrid search with reranking
        print("\n[IMPROVED] Hybrid Search + Reranking")
        hybrid_results = vector_store.hybrid_search(
            query=test['query'],
            k=3,
            initial_k=10,
            use_reranking=True
        )
        hybrid_eval = evaluate_retrieval(hybrid_results, test['expected_docs'])
        hybrid_scores.append(hybrid_eval)
        
        print(f"  Retrieved: {', '.join(hybrid_eval['retrieved'][:3])}")
        print(f"  Matches: {', '.join(hybrid_eval['matches']) if hybrid_eval['matches'] else 'None'}")
        print(f"  Precision@3: {hybrid_eval['precision']:.2f}")
        print(f"  Recall@3: {hybrid_eval['recall']:.2f}")
        print(f"  F1@3: {hybrid_eval['f1']:.2f}")
        
        # Show improvement
        f1_improvement = ((hybrid_eval['f1'] - baseline_eval['f1']) / baseline_eval['f1'] * 100) if baseline_eval['f1'] > 0 else 0
        print(f"\n  → F1 Improvement: {f1_improvement:+.1f}%")
    
    # Overall summary
    print("\n" + "=" * 80)
    print("OVERALL RESULTS")
    print("=" * 80)
    
    avg_baseline_f1 = sum(s['f1'] for s in baseline_scores) / len(baseline_scores)
    avg_hybrid_f1 = sum(s['f1'] for s in hybrid_scores) / len(hybrid_scores)
    
    avg_baseline_precision = sum(s['precision'] for s in baseline_scores) / len(baseline_scores)
    avg_hybrid_precision = sum(s['precision'] for s in hybrid_scores) / len(hybrid_scores)
    
    avg_baseline_recall = sum(s['recall'] for s in baseline_scores) / len(baseline_scores)
    avg_hybrid_recall = sum(s['recall'] for s in hybrid_scores) / len(hybrid_scores)
    
    print(f"\nBaseline (Vector Search Only):")
    print(f"  Average Precision@3: {avg_baseline_precision:.3f}")
    print(f"  Average Recall@3: {avg_baseline_recall:.3f}")
    print(f"  Average F1@3: {avg_baseline_f1:.3f}")
    
    print(f"\nImproved (Hybrid + Reranking):")
    print(f"  Average Precision@3: {avg_hybrid_precision:.3f}")
    print(f"  Average Recall@3: {avg_hybrid_recall:.3f}")
    print(f"  Average F1@3: {avg_hybrid_f1:.3f}")
    
    overall_improvement = ((avg_hybrid_f1 - avg_baseline_f1) / avg_baseline_f1 * 100) if avg_baseline_f1 > 0 else 0
    
    print(f"\n{'🎉' * 40}")
    print(f"OVERALL F1 IMPROVEMENT: {overall_improvement:+.1f}%")
    print(f"{'🎉' * 40}")
    
    print(f"\nKey Improvements:")
    print(f"  ✓ BM25 adds keyword matching for exact terminology")
    print(f"  ✓ Hybrid fusion combines semantic + lexical signals")
    print(f"  ✓ Cross-encoder reranking refines final results")
    print(f"  ✓ Better handles multi-concept and technical queries")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        run_comparison_test()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nError running test: {e}")
        import traceback
        traceback.print_exc()
