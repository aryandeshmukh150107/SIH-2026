# pyrefly: ignore [missing-import]
from transformers import pipeline

MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"

sentiment_model = pipeline(
    "sentiment-analysis",
    model=MODEL_NAME
)


def analyze_sentiment(text):
    result = sentiment_model(text)[0]

    return {
        "sentiment": result["label"],
        "confidence": round(result["score"], 4)
    }


if __name__ == "__main__":

    comments = [
        "This policy is excellent and will really help citizens.",
        "The policy is completely useless and poorly implemented.",
        "The policy is acceptable but there are some concerns.",
        "I like this work but the government spent ₹24cr on it."
    ]

    for comment in comments:

        result = analyze_sentiment(comment)

        print("\nComment:", comment)
        print("Sentiment:", result["sentiment"])
        print("Confidence:", result["confidence"])