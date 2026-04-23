"""
LLM Service
Handles interactions with Large Language Models for RAG (Retrieval-Augmented Generation).
"""

import os
from typing import List, Dict, Any, Optional
from openai import OpenAI


class LLMService:
    """
    Service for interacting with LLMs for question answering using retrieved context.
    """
    
    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        """
        Initialize the LLM service.
        
        Args:
            model: OpenAI model to use (default: gpt-3.5-turbo)
            api_key: Optional API key (defaults to OPENAI_API_KEY env var)
            temperature: Sampling temperature (0-2, default: 0.7)
            max_tokens: Maximum tokens in response (default: 1000)
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.client = OpenAI(api_key=self.api_key)
    
    def generate_rag_prompt(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        include_metadata: bool = True
    ) -> str:
        """
        Generate a RAG prompt from question and context chunks.
        
        Args:
            question: User's question
            context_chunks: List of retrieved chunks with metadata
            include_metadata: Whether to include source metadata in context
            
        Returns:
            Formatted prompt string
        """
        # Build context section
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            text = chunk.get('document', chunk.get('text', ''))
            
            if include_metadata and 'metadata' in chunk:
                metadata = chunk['metadata']
                source = metadata.get('source', 'Unknown')
                chunk_idx = metadata.get('chunk_index', 'N/A')
                context_parts.append(
                    f"[Source {i}: {source}, Chunk {chunk_idx}]\n{text}"
                )
            else:
                context_parts.append(f"[Context {i}]\n{text}")
        
        context_text = "\n\n".join(context_parts)
        
        # Create the full prompt
        prompt = f"""You are a helpful AI assistant that answers questions based on the provided context. 
Use the following pieces of context to answer the question at the end. 
If you don't know the answer based on the context, just say that you don't know - don't try to make up an answer.
Always cite which source(s) you used to formulate your answer.

Context:
{context_text}

Question: {question}

Answer: """
        
        return prompt
    
    def answer_question(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG with retrieved context chunks.
        
        Args:
            question: User's question
            context_chunks: Retrieved context chunks from vector search
            system_prompt: Optional custom system prompt
            include_sources: Whether to include source information in response
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        if not context_chunks:
            return {
                "answer": "I don't have any relevant context to answer this question.",
                "sources": [],
                "model": self.model,
                "context_used": 0
            }
        
        # Generate the prompt
        user_prompt = self.generate_rag_prompt(question, context_chunks)
        
        # Default system prompt
        if system_prompt is None:
            system_prompt = (
                "You are a knowledgeable AI assistant. Answer questions accurately "
                "based on the provided context. Be concise but thorough. "
                "Always cite your sources when providing information."
            )
        
        # Call OpenAI API
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Extract source information
            sources = []
            if include_sources:
                for chunk in context_chunks:
                    source_info = {
                        "text": chunk.get('document', chunk.get('text', ''))[:200] + "...",
                        "similarity_score": chunk.get('similarity_score', 0),
                    }
                    
                    if 'metadata' in chunk:
                        source_info['metadata'] = chunk['metadata']
                    
                    sources.append(source_info)
            
            return {
                "answer": answer,
                "sources": sources,
                "model": self.model,
                "context_used": len(context_chunks),
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            raise RuntimeError(f"LLM API call failed: {str(e)}")
    
    def simple_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Simple text completion without RAG.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Generated text
        """
        if system_prompt is None:
            system_prompt = "You are a helpful AI assistant."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise RuntimeError(f"LLM API call failed: {str(e)}")
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the LLM service configuration."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "api_configured": bool(self.api_key)
        }


# Convenience functions
def create_llm_service(
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7
) -> LLMService:
    """
    Create an LLM service with default settings.
    
    Args:
        model: OpenAI model to use
        temperature: Sampling temperature
        
    Returns:
        Configured LLMService instance
    """
    return LLMService(model=model, temperature=temperature)


def answer_with_rag(
    question: str,
    context_chunks: List[Dict[str, Any]],
    model: str = "gpt-3.5-turbo"
) -> Dict[str, Any]:
    """
    Quick function to answer a question with RAG.
    
    Args:
        question: User's question
        context_chunks: Retrieved context chunks
        model: OpenAI model to use
        
    Returns:
        Answer with sources
    """
    service = create_llm_service(model=model)
    return service.answer_question(question, context_chunks)
