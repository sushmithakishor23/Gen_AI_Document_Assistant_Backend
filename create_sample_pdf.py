"""
Script to generate a sample PDF for testing the document loader.
Creates a simple PDF with text content using reportlab.
"""

from pathlib import Path


def create_sample_pdf():
    """Create a sample PDF file for testing."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
    except ImportError:
        print("Error: reportlab is not installed.")
        print("Installing reportlab...")
        import subprocess
        subprocess.check_call(["pip", "install", "reportlab"])
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
    
    # Create test directory
    test_dir = Path("data/test_files")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Output file
    pdf_file = test_dir / "sample_document.pdf"
    
    # Create PDF
    c = canvas.Canvas(str(pdf_file), pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawString(1 * inch, height - 1 * inch, "Sample Document for Testing")
    
    # Content
    c.setFont("Helvetica", 12)
    y_position = height - 1.8 * inch
    
    content = [
        "Introduction to Natural Language Processing",
        "",
        "Natural Language Processing (NLP) is a branch of artificial intelligence that helps",
        "computers understand, interpret, and manipulate human language. NLP draws from many",
        "disciplines, including computer science and computational linguistics, in its pursuit",
        "to fill the gap between human communication and computer understanding.",
        "",
        "Key Applications:",
        "- Machine Translation: Translating text from one language to another",
        "- Sentiment Analysis: Determining the emotional tone behind words",
        "- Text Summarization: Creating concise summaries of longer documents",
        "- Named Entity Recognition: Identifying and classifying named entities",
        "- Question Answering: Building systems that can answer questions",
        "",
        "Core Techniques:",
        "1. Tokenization: Breaking text into individual words or tokens",
        "2. Part-of-Speech Tagging: Identifying grammatical parts of speech",
        "3. Parsing: Analyzing grammatical structure of sentences",
        "4. Word Embeddings: Representing words as numerical vectors",
        "5. Language Models: Statistical models of word sequences",
        "",
        "Modern NLP leverages deep learning techniques such as transformers, which have",
        "revolutionized the field. Models like BERT, GPT, and T5 have achieved remarkable",
        "results on a wide range of NLP tasks.",
    ]
    
    for line in content:
        if y_position < 1 * inch:
            c.showPage()
            c.setFont("Helvetica", 12)
            y_position = height - 1 * inch
        
        c.drawString(1 * inch, y_position, line)
        y_position -= 0.25 * inch
    
    # New page with more content
    c.showPage()
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, height - 1 * inch, "Challenges in NLP")
    
    c.setFont("Helvetica", 12)
    y_position = height - 1.5 * inch
    
    challenges = [
        "Despite recent advances, NLP still faces several challenges:",
        "",
        "Ambiguity: Natural language is inherently ambiguous. The same word or phrase",
        "can have different meanings depending on context.",
        "",
        "Context Understanding: Understanding context requires world knowledge and",
        "common sense reasoning, which is difficult for machines.",
        "",
        "Multilingual Support: Most NLP research focuses on English, making it",
        "challenging to develop systems for low-resource languages.",
        "",
        "Bias and Fairness: Language models can perpetuate biases present in",
        "training data, leading to fairness concerns.",
        "",
        "Conclusion:",
        "NLP continues to evolve rapidly, with new techniques and applications emerging",
        "regularly. As models become more sophisticated, they promise to transform how",
        "we interact with technology and process information.",
    ]
    
    for line in challenges:
        if y_position < 1 * inch:
            c.showPage()
            c.setFont("Helvetica", 12)
            y_position = height - 1 * inch
        
        c.drawString(1 * inch, y_position, line)
        y_position -= 0.25 * inch
    
    # Save PDF
    c.save()
    
    print(f"✓ Sample PDF created: {pdf_file}")
    print(f"  File size: {pdf_file.stat().st_size} bytes")
    
    return str(pdf_file)


if __name__ == "__main__":
    create_sample_pdf()
