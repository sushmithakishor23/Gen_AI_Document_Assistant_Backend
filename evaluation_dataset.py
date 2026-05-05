"""
RAG Evaluation Dataset
Contains ground-truth Q&A pairs for evaluating the RAG system.
Each entry includes: question, expected answer, and relevant context sections.
"""

EVALUATION_DATASET = [
    {
        "question": "What is machine learning?",
        "ground_truth_answer": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.",
        "expected_context_keywords": ["subset of artificial intelligence", "learn", "experience", "Arthur Samuel"],
        "category": "definition"
    },
    {
        "question": "What are the three main types of machine learning?",
        "ground_truth_answer": "The three main types of machine learning are supervised learning (learning from labeled data), unsupervised learning (finding patterns in unlabeled data), and reinforcement learning (learning through interaction with an environment using rewards and penalties).",
        "expected_context_keywords": ["supervised learning", "unsupervised learning", "reinforcement learning"],
        "category": "classification"
    },
    {
        "question": "What is the difference between overfitting and underfitting?",
        "ground_truth_answer": "Overfitting occurs when a model learns the training data too well, including noise and outliers, resulting in poor generalization to new data. Underfitting happens when the model is too simple to capture the underlying patterns in the data.",
        "expected_context_keywords": ["overfitting", "underfitting", "noise", "too simple", "generalization"],
        "category": "concepts"
    },
    {
        "question": "How do you calculate precision in classification?",
        "ground_truth_answer": "Precision is calculated as TP / (TP + FP), where TP is true positives and FP is false positives. It represents the proportion of true positive predictions among all positive predictions.",
        "expected_context_keywords": ["precision", "TP", "FP", "true positive", "false positive"],
        "category": "metrics"
    },
    {
        "question": "What is the F1 score?",
        "ground_truth_answer": "The F1 score is the harmonic mean of precision and recall, calculated as 2 * (Precision * Recall) / (Precision + Recall).",
        "expected_context_keywords": ["F1", "harmonic mean", "precision", "recall"],
        "category": "metrics"
    },
    {
        "question": "What is K-fold cross-validation?",
        "ground_truth_answer": "K-fold cross-validation divides the data into K subsets (folds), training on K-1 folds and validating on the remaining fold. This process repeats K times, with each fold serving as the validation set once.",
        "expected_context_keywords": ["K-fold", "cross-validation", "subsets", "training", "validation"],
        "category": "evaluation"
    },
    {
        "question": "What is the bias-variance tradeoff?",
        "ground_truth_answer": "Bias is the error from erroneous assumptions in the learning algorithm (high bias causes underfitting). Variance is the error from sensitivity to small fluctuations in the training set (high variance causes overfitting). The goal is to minimize both.",
        "expected_context_keywords": ["bias", "variance", "tradeoff", "underfitting", "overfitting"],
        "category": "concepts"
    },
    {
        "question": "What are some common regularization techniques?",
        "ground_truth_answer": "Common regularization techniques include L1 regularization (Lasso), L2 regularization (Ridge), Elastic Net (combining L1 and L2), Dropout (for neural networks), and Early Stopping.",
        "expected_context_keywords": ["L1", "L2", "Lasso", "Ridge", "Dropout", "Early Stopping"],
        "category": "techniques"
    },
    {
        "question": "What is the difference between bagging and boosting?",
        "ground_truth_answer": "Bagging trains multiple models on different subsets of data in parallel (e.g., Random Forest), while boosting sequentially trains models where each focuses on mistakes of previous ones (e.g., XGBoost, AdaBoost).",
        "expected_context_keywords": ["bagging", "boosting", "parallel", "sequential", "ensemble"],
        "category": "algorithms"
    },
    {
        "question": "What is a Convolutional Neural Network used for?",
        "ground_truth_answer": "Convolutional Neural Networks (CNNs) are specialized for image processing, using convolutional layers to detect spatial patterns in images.",
        "expected_context_keywords": ["CNN", "Convolutional", "image", "spatial patterns", "convolutional layers"],
        "category": "deep_learning"
    },
    {
        "question": "What is feature engineering?",
        "ground_truth_answer": "Feature engineering is the process of creating new features or transforming existing ones to improve model performance. Techniques include normalization, standardization, one-hot encoding, feature extraction, and creating polynomial features.",
        "expected_context_keywords": ["feature engineering", "creating features", "transforming", "normalization", "one-hot encoding"],
        "category": "preprocessing"
    },
    {
        "question": "What is the purpose of a validation set?",
        "ground_truth_answer": "A validation set is used for hyperparameter tuning and model selection, helping to assess model performance during development without using the test set.",
        "expected_context_keywords": ["validation", "hyperparameter tuning", "training", "testing"],
        "category": "evaluation"
    },
    {
        "question": "What is Mean Squared Error?",
        "ground_truth_answer": "Mean Squared Error (MSE) is the average of squared differences between predicted and actual values. It's a common metric for regression tasks.",
        "expected_context_keywords": ["MSE", "Mean Squared Error", "squared differences", "regression"],
        "category": "metrics"
    },
    {
        "question": "What is supervised learning?",
        "ground_truth_answer": "Supervised learning algorithms learn from labeled training data, where each example has an input and a corresponding output label. The model learns to map inputs to outputs.",
        "expected_context_keywords": ["supervised", "labeled", "input", "output", "training data"],
        "category": "classification"
    },
    {
        "question": "What are some examples of ensemble methods?",
        "ground_truth_answer": "Ensemble methods include bagging (like Random Forest), boosting (like XGBoost, AdaBoost, Gradient Boosting), and stacking (training a meta-model to combine predictions from multiple base models).",
        "expected_context_keywords": ["ensemble", "bagging", "boosting", "stacking", "Random Forest", "XGBoost"],
        "category": "algorithms"
    }
]

# Statistics about the dataset
def get_dataset_stats():
    """Get statistics about the evaluation dataset."""
    total = len(EVALUATION_DATASET)
    categories = {}
    for item in EVALUATION_DATASET:
        cat = item["category"]
        categories[cat] = categories.get(cat, 0) + 1
    
    return {
        "total_questions": total,
        "categories": categories,
        "avg_keywords_per_question": sum(len(item["expected_context_keywords"]) for item in EVALUATION_DATASET) / total
    }

if __name__ == "__main__":
    stats = get_dataset_stats()
    print("=" * 60)
    print("RAG EVALUATION DATASET STATISTICS")
    print("=" * 60)
    print(f"Total Questions: {stats['total_questions']}")
    print(f"Average Keywords per Question: {stats['avg_keywords_per_question']:.1f}")
    print("\nQuestions by Category:")
    for category, count in sorted(stats['categories'].items()):
        print(f"  - {category}: {count}")
    print("=" * 60)
