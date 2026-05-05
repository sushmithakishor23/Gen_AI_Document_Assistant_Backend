"""
Custom RAG Evaluation Framework

This module implements custom evaluation metrics for RAG systems:
1. Faithfulness: How well the answer is grounded in the retrieved context
2. Answer Relevance: How relevant the answer is to the question
3. Context Precision: How many retrieved documents are actually relevant
4. Context Recall: Whether all necessary information was retrieved

These metrics use OpenAI embeddings for semantic similarity and keyword matching
for grounding verification.
"""

import os
import re
from typing import List, Dict, Tuple
import numpy as np
from openai import OpenAI
from evaluation_dataset import EVALUATION_DATASET

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class RAGEvaluator:
    """Comprehensive RAG evaluation with custom metrics."""
    
    def __init__(self):
        """Initialize the evaluator."""
        self.client = client
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text using OpenAI.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        response = self.client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def calculate_faithfulness(self, answer: str, context_chunks: List[str]) -> Dict[str, float]:
        """
        Calculate faithfulness score: How well the answer is grounded in context.
        
        Method:
        1. Split answer into sentences
        2. For each sentence, check if it can be verified in any context chunk
        3. Use embedding similarity to determine if sentence is grounded
        
        Args:
            answer: Generated answer
            context_chunks: Retrieved context chunks
            
        Returns:
            Dictionary with faithfulness score and details
        """
        if not answer or not context_chunks:
            return {"score": 0.0, "grounded_sentences": 0, "total_sentences": 0}
        
        # Split answer into sentences
        sentences = [s.strip() for s in re.split(r'[.!?]+', answer) if s.strip()]
        
        if not sentences:
            return {"score": 0.0, "grounded_sentences": 0, "total_sentences": 0}
        
        # Combine all context
        combined_context = " ".join(context_chunks)
        context_embedding = self.get_embedding(combined_context)
        
        # Check each sentence
        grounded_count = 0
        for sentence in sentences:
            sentence_embedding = self.get_embedding(sentence)
            similarity = self.cosine_similarity(sentence_embedding, context_embedding)
            
            # Threshold for considering a sentence grounded (0.7 is reasonable)
            if similarity >= 0.7:
                grounded_count += 1
        
        faithfulness_score = grounded_count / len(sentences)
        
        return {
            "score": faithfulness_score,
            "grounded_sentences": grounded_count,
            "total_sentences": len(sentences)
        }
    
    def calculate_answer_relevance(self, question: str, answer: str) -> Dict[str, float]:
        """
        Calculate answer relevance: How relevant the answer is to the question.
        
        Method:
        Uses embedding similarity between question and answer.
        
        Args:
            question: User's question
            answer: Generated answer
            
        Returns:
            Dictionary with relevance score
        """
        if not question or not answer:
            return {"score": 0.0}
        
        question_embedding = self.get_embedding(question)
        answer_embedding = self.get_embedding(answer)
        
        similarity = self.cosine_similarity(question_embedding, answer_embedding)
        
        return {"score": similarity}
    
    def calculate_context_precision(self, 
                                    context_chunks: List[str], 
                                    expected_keywords: List[str]) -> Dict[str, float]:
        """
        Calculate context precision: How many retrieved chunks are relevant.
        
        Method:
        Check how many context chunks contain expected keywords.
        
        Args:
            context_chunks: Retrieved context chunks
            expected_keywords: Keywords that should appear in relevant context
            
        Returns:
            Dictionary with precision score and details
        """
        if not context_chunks or not expected_keywords:
            return {"score": 0.0, "relevant_chunks": 0, "total_chunks": 0}
        
        relevant_count = 0
        for chunk in context_chunks:
            chunk_lower = chunk.lower()
            # Check if chunk contains any expected keyword
            for keyword in expected_keywords:
                if keyword.lower() in chunk_lower:
                    relevant_count += 1
                    break  # Count chunk only once
        
        precision = relevant_count / len(context_chunks)
        
        return {
            "score": precision,
            "relevant_chunks": relevant_count,
            "total_chunks": len(context_chunks)
        }
    
    def calculate_context_recall(self, 
                                 context_chunks: List[str], 
                                 expected_keywords: List[str]) -> Dict[str, float]:
        """
        Calculate context recall: Did we retrieve all necessary information?
        
        Method:
        Check how many expected keywords appear in the retrieved context.
        
        Args:
            context_chunks: Retrieved context chunks
            expected_keywords: Keywords that should be retrieved
            
        Returns:
            Dictionary with recall score and details
        """
        if not context_chunks or not expected_keywords:
            return {"score": 0.0, "found_keywords": 0, "total_keywords": 0}
        
        combined_context = " ".join(context_chunks).lower()
        
        found_count = 0
        for keyword in expected_keywords:
            if keyword.lower() in combined_context:
                found_count += 1
        
        recall = found_count / len(expected_keywords)
        
        return {
            "score": recall,
            "found_keywords": found_count,
            "total_keywords": len(expected_keywords)
        }
    
    def evaluate_single_query(self, 
                             question: str,
                             answer: str,
                             context_chunks: List[str],
                             ground_truth: Dict) -> Dict:
        """
        Evaluate a single RAG query with all metrics.
        
        Args:
            question: User's question
            answer: Generated answer
            context_chunks: Retrieved context chunks
            ground_truth: Ground truth data with expected answer and keywords
            
        Returns:
            Dictionary with all evaluation metrics
        """
        print(f"  Evaluating: {question[:60]}...")
        
        faithfulness = self.calculate_faithfulness(answer, context_chunks)
        answer_relevance = self.calculate_answer_relevance(question, answer)
        context_precision = self.calculate_context_precision(
            context_chunks, 
            ground_truth.get("expected_context_keywords", [])
        )
        context_recall = self.calculate_context_recall(
            context_chunks,
            ground_truth.get("expected_context_keywords", [])
        )
        
        return {
            "question": question,
            "answer": answer,
            "faithfulness": faithfulness,
            "answer_relevance": answer_relevance,
            "context_precision": context_precision,
            "context_recall": context_recall,
            "category": ground_truth.get("category", "unknown")
        }
    
    def aggregate_results(self, results: List[Dict]) -> Dict:
        """
        Aggregate evaluation results across all queries.
        
        Args:
            results: List of evaluation results
            
        Returns:
            Aggregated metrics
        """
        if not results:
            return {}
        
        total = len(results)
        
        avg_faithfulness = sum(r["faithfulness"]["score"] for r in results) / total
        avg_answer_relevance = sum(r["answer_relevance"]["score"] for r in results) / total
        avg_context_precision = sum(r["context_precision"]["score"] for r in results) / total
        avg_context_recall = sum(r["context_recall"]["score"] for r in results) / total
        
        # Category-wise breakdown
        category_scores = {}
        for result in results:
            cat = result["category"]
            if cat not in category_scores:
                category_scores[cat] = []
            category_scores[cat].append({
                "faithfulness": result["faithfulness"]["score"],
                "answer_relevance": result["answer_relevance"]["score"],
                "context_precision": result["context_precision"]["score"],
                "context_recall": result["context_recall"]["score"]
            })
        
        category_avg = {}
        for cat, scores in category_scores.items():
            category_avg[cat] = {
                "faithfulness": sum(s["faithfulness"] for s in scores) / len(scores),
                "answer_relevance": sum(s["answer_relevance"] for s in scores) / len(scores),
                "context_precision": sum(s["context_precision"] for s in scores) / len(scores),
                "context_recall": sum(s["context_recall"] for s in scores) / len(scores),
                "count": len(scores)
            }
        
        return {
            "overall": {
                "faithfulness": avg_faithfulness,
                "answer_relevance": avg_answer_relevance,
                "context_precision": avg_context_precision,
                "context_recall": avg_context_recall,
                "total_queries": total
            },
            "by_category": category_avg
        }
    
    def print_results(self, aggregated: Dict):
        """
        Print evaluation results in a readable format.
        
        Args:
            aggregated: Aggregated evaluation results
        """
        print("\n" + "=" * 80)
        print("RAG EVALUATION RESULTS")
        print("=" * 80)
        
        overall = aggregated["overall"]
        print(f"\nOVERALL METRICS (n={overall['total_queries']})")
        print("-" * 80)
        print(f"  Faithfulness:       {overall['faithfulness']:.1%} - Answer grounded in context")
        print(f"  Answer Relevance:   {overall['answer_relevance']:.1%} - Answer matches question")
        print(f"  Context Precision:  {overall['context_precision']:.1%} - Retrieved docs are relevant")
        print(f"  Context Recall:     {overall['context_recall']:.1%} - All needed info retrieved")
        
        print("\nBY CATEGORY")
        print("-" * 80)
        for category, metrics in sorted(aggregated["by_category"].items()):
            print(f"\n{category.upper()} (n={metrics['count']})")
            print(f"  Faithfulness:       {metrics['faithfulness']:.1%}")
            print(f"  Answer Relevance:   {metrics['answer_relevance']:.1%}")
            print(f"  Context Precision:  {metrics['context_precision']:.1%}")
            print(f"  Context Recall:     {metrics['context_recall']:.1%}")
        
        print("\n" + "=" * 80)
        print("INTERVIEW TALKING POINTS:")
        print("-" * 80)
        print(f"✓ Achieved {overall['faithfulness']:.1%} faithfulness (answers grounded in documents)")
        print(f"✓ Achieved {overall['answer_relevance']:.1%} answer relevance (answers match questions)")
        print(f"✓ Hybrid search + reranking provides {overall['context_precision']:.1%} precision")
        print(f"✓ System retrieves {overall['context_recall']:.1%} of expected information")
        print("=" * 80 + "\n")


def format_percentage(value: float) -> str:
    """Format a decimal value as a percentage."""
    return f"{value * 100:.1f}%"


if __name__ == "__main__":
    print("RAG Evaluator - Custom Metrics Implementation")
    print("This module provides evaluation metrics for RAG systems.\n")
    print("To use this evaluator:")
    print("1. Upload the evaluation document to your RAG system")
    print("2. Run the evaluation script (evaluate_rag_system.py)")
    print("3. Review the detailed metrics\n")
