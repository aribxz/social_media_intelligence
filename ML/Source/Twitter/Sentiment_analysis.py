from pathlib import Path
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[3]
analyzer = SentimentIntensityAnalyzer()
twitter = pd.read_csv(BASE_DIR / "Data/Processed/Twitter_clean.csv")

test_rows = twitter.loc[
    twitter["text"].str.contains(r"<U\+", regex=True),
    ["text", "text_clean"]
].head(10)

for _, row in test_rows.iterrows():
    print("TEXT:")
    print(row["text"])

    print("\nCLEAN:")
    print(row["text_clean"])

    print("\nVADER:")
    print(analyzer.polarity_scores(row["text_clean"]))

    print("=" * 100)