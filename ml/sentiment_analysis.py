from transformers import pipeline

sentiment_model = pipeline("sentiment-analysis")

def analyze_sentiment(review_text: str) -> str:
    result = sentiment_model(review_text)[0]
    label = result["label"].lower()

    if label == "positive":
        return "positive"
    elif label == "negative":
        return "negative"
    else:
        return "neutral"