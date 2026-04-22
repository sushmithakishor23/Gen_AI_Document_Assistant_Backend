# Windows PyTorch DLL Issue - Troubleshooting Guide

## Issue
When running tests that use sentence-transformers, you may encounter:
```
OSError: [WinError 1114] A dynamic link library (DLL) initialization routine failed.
Error loading "...\torch\lib\c10.dll" or one of its dependencies.
```

## Root Cause
This is a known issue on Windows where PyTorch requires Microsoft Visual C++ Redistributable packages that may not be installed on your system.

## Solutions

### Option 1: Use OpenAI Embeddings (Recommended for Testing)
Instead of sentence-transformers (which requires PyTorch), use OpenAI's cloud-based embeddings:

```bash
# Set your OpenAI API key
$env:OPENAI_API_KEY='your-key-here'

# Run the OpenAI-based test
py test_vector_store_openai.py
```

**Code example:**
```python
from app.services.embeddings import EmbeddingsService, EmbeddingProvider
from app.services.vector_store import VectorStore

# Use OpenAI embeddings
embeddings = EmbeddingsService(
    provider=EmbeddingProvider.OPENAI,
    model_name="text-embedding-3-small"
)

vector_store = VectorStore(
    embeddings_service=embeddings
)
```

### Option 2: Install Visual C++ Redistributable
1. Download and install [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. Restart your computer
3. Try running the tests again

### Option 3: Use Python 3.11 or 3.10
Python 3.14 is very new and may have compatibility issues. Try using Python 3.11:
```bash
# Install Python 3.11 from https://www.python.org/downloads/
# Create a new virtual environment with Python 3.11
py -3.11 -m venv venv311
.\venv311\Scripts\activate
pip install -r requirements.txt
```

### Option 4: Use Conda (If Available)
Conda often handles PyTorch dependencies better:
```bash
conda create -n genai python=3.11
conda activate genai
conda install pytorch cpuonly -c pytorch
pip install -r requirements.txt
```

## Testing Your Setup

### Test 1: Check PyTorch Installation
```bash
py -c "import torch; print('PyTorch version:', torch.__version__)"
```

If this fails, PyTorch is not working.

### Test 2: Test Sentence-Transformers
```bash
py -c "from sentence_transformers import SentenceTransformer; print('sentence-transformers OK')"
```

### Test 3: Test Embeddings Service
```bash
py -c "from app.services.embeddings import EmbeddingsService, EmbeddingProvider; e = EmbeddingsService(EmbeddingProvider.SENTENCE_TRANSFORMERS); print('Embeddings OK')"
```

## Comparison: OpenAI vs Sentence-Transformers

| Feature | OpenAI | Sentence-Transformers |
|---------|--------|----------------------|
| Cost | Paid (very cheap) | Free |
| Setup | Easy (just API key) | Requires PyTorch |
| Performance | Excellent | Very good |
| Speed | Network dependent | Fast (local) |
| Privacy | Data sent to OpenAI | Fully local |
| Embedding Dim | 1536 | 384 (default model) |

## Recommended Approach

For **Development/Testing**: Use OpenAI embeddings (easier setup, no DLL issues)
For **Production (if cost is a concern)**: Fix PyTorch and use sentence-transformers

## Files

- `test_vector_store_openai.py` - Test script using OpenAI embeddings
- `test_vector_store.py` - Test script using sentence-transformers (requires working PyTorch)

Both scripts test the same functionality - choose based on what works on your system.
