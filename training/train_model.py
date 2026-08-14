"""
Train the XGBoost fraud detection model.

Usage:
  pip install pandas numpy scikit-learn xgboost imbalanced-learn
  python train_model.py

Downloads the Kaggle dataset automatically if kaggle CLI is configured,
or you can place 'Fraudulent_E-Commerce_Transaction_Data.csv' in this folder.
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier

DATA_FILE = "Fraudulent_E-Commerce_Transaction_Data.csv"
MODEL_DIR = "model"
MODEL_PATH = os.path.join(MODEL_DIR, "fraud_model.pkl")

os.makedirs(MODEL_DIR, exist_ok=True)


def load_data():
    if not os.path.exists(DATA_FILE):
        print(f"Dataset not found. Trying Kaggle download...")
        os.system("kaggle datasets download -d shriyashjagtap/fraudulent-e-commerce-transactions --unzip")
    df = pd.read_csv(DATA_FILE)
    print(f"Loaded {len(df):,} rows, {df.shape[1]} columns")
    return df


def engineer_features(df):
    df = df.copy()

    # Rename columns to standard names (handle various CSV formats)
    rename_map = {}
    col_lower = {c.lower().replace(" ", "_"): c for c in df.columns}

    col_mapping = {
        "transaction_amount": ["transaction_amount", "amount", "transactionamount"],
        "account_age_days":   ["account_age_days", "account_age", "accountagedays"],
        "num_transactions_today": ["num_transactions_today", "transactions_per_day", "numtransactionstoday"],
        "distance_from_home_km":  ["distance_from_home_km", "distance_from_home", "distancefromhome"],
        "hour_of_day":  ["hour_of_day", "transaction_hour", "hourofday"],
        "is_weekend":   ["is_weekend", "weekend"],
        "is_international": ["is_international", "international", "isinternational"],
        "payment_method":   ["payment_method", "paymentmethod"],
        "device_type":  ["device_type", "devicetype"],
        "failed_attempts":  ["failed_attempts", "failed_login_attempts", "failedattempts"],
        "is_fraud": ["is_fraud", "fraud", "fraudulent", "label"],
    }

    for std_name, aliases in col_mapping.items():
        for alias in aliases:
            if alias in col_lower:
                rename_map[col_lower[alias]] = std_name
                break

    df.rename(columns=rename_map, inplace=True)

    # Encode categoricals
    for col in ["payment_method", "device_type"]:
        if col in df.columns and df[col].dtype == object:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))

    # Select features
    FEATURES = [
        "transaction_amount", "account_age_days", "num_transactions_today",
        "distance_from_home_km", "hour_of_day", "is_weekend", "is_international",
        "payment_method", "device_type", "failed_attempts",
    ]

    available = [f for f in FEATURES if f in df.columns]
    missing = [f for f in FEATURES if f not in df.columns]
    if missing:
        print(f"Warning: missing features {missing} — filling with 0")
        for m in missing:
            df[m] = 0

    X = df[FEATURES].fillna(0)
    y = df["is_fraud"].astype(int)
    return X, y


def train(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Class balance before SMOTE: {y_train.value_counts().to_dict()}")
    sm = SMOTE(random_state=42)
    X_res, y_res = sm.fit_resample(X_train, y_train)
    print(f"Class balance after SMOTE:  {pd.Series(y_res).value_counts().to_dict()}")

    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_res, y_res, eval_set=[(X_test, y_test)], verbose=50)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}")

    return model


def main():
    df = load_data()
    X, y = engineer_features(df)
    model = train(X, y)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print(f"\nModel saved to {MODEL_PATH}")
    print("Now run: python app.py")


if __name__ == "__main__":
    main()
