from transformers import pipeline
import numpy as np
import csv
import os

# Explicitly specify the model
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")

CSV_FILE = os.path.join('data', 'block_inputs.csv')

def analyze_sentiment(text):
    result = sentiment_analyzer(text)[0]
    sentiment = result['label']
    score = result['score']

    # Convert to numerical impact
    if sentiment == 'POSITIVE':
        impact = min(20, int(score * 20))  # Increase legitimacy
    elif sentiment == 'NEGATIVE':
        impact = -min(20, int(score * 20))  # Decrease legitimacy
    else:
        impact = 0  # Neutral

    return impact

def predict_legitimacy(product_data):
    base_score = 80  # Default bias towards 80
    if isinstance(product_data, dict):
        notes = product_data.get('notes', '')
    else:
        notes = product_data  # Assume it's already a string

    sentiment_impact = analyze_sentiment(notes)
    legitimacy_score = max(0, min(100, base_score + sentiment_impact))
    return legitimacy_score

def get_average_legitimacy(product_id):
    """
    Reads CSV file and averages legitimacy scores for the given product_id.
    """
    if not os.path.exists(CSV_FILE):
        return None  # No previous records

    legitimacy_scores = []
    
    with open(CSV_FILE, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['productId'] == product_id and 'legitimacyScore' in row:
                legitimacy_scores.append(float(row['legitimacyScore']))

    if legitimacy_scores:
        return round(sum(legitimacy_scores) / len(legitimacy_scores), 2)  # Average score
    else:
        return None  # No scores found
