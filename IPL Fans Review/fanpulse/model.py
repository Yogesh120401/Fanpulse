from transformers import pipeline
import re

# Load pretrained sentiment pipeline once at module level
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment"
)

def clean_text(text):
    text = re.sub(r"http\S+", "", text)       # Remove URLs
    text = re.sub(r"@\w+", "", text)           # Remove mentions
    text = re.sub(r"#", "", text)              # Remove hashtag symbol
    text = re.sub(r"[^A-Za-z\s]", "", text)   # Keep only letters + spaces
    return text.lower().strip()

def analyze_sentiment(text):
    cleaned = clean_text(text)

    # ✅ FIX 7: Raise early if cleaning leaves nothing (e.g. emoji-only tweets)
    if not cleaned:
        raise ValueError("Tweet is empty after cleaning — likely emoji/link-only content.")

    result = sentiment_pipeline(cleaned[:512])[0]  # ✅ Also cap at 512 tokens (model limit)

    label = result["label"]
    score = round(result["score"], 2)

    sentiment_map = {
        "LABEL_0": "Negative",
        "LABEL_1": "Neutral",
        "LABEL_2": "Positive",
    }

    return sentiment_map[label], score