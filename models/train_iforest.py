"""
اسکریپت آموزش مدل IsolationForest
====================

این فایل یک مدل IsolationForest را روی دادهٔ تصادفی یا دادهٔ موجود در فایل CSV آموزش می‌دهد و آن را در مسیر مشخص‌شده ذخیره می‌کند. اگر فایل داده‌ای با نام `train_data.csv` در پوشهٔ `models/` وجود داشته باشد، از آن استفاده می‌شود؛ در غیر این صورت دادهٔ تصادفی تولید می‌شود.
"""

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib


def main():
    model_path = os.environ.get("MODEL_PATH", "models/iforest_model.pkl")
    data_file = os.path.join(os.path.dirname(__file__), "train_data.csv")

    if os.path.exists(data_file):
        print(f"Loading training data from {data_file}")
        df = pd.read_csv(data_file)
        X = df.select_dtypes(include=[np.number]).values
    else:
        print("No training data found, generating random data...")
        # دادهٔ تصادفی با 3 ویژگی
        X = np.random.randn(1000, 3)

    print("Training IsolationForest model...")
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(X)

    # ذخیره مدل
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")


if __name__ == "__main__":
    main()