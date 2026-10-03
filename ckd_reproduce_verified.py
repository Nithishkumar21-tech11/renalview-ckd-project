# ==============================================================================
# REPRODUCIBLE EXPERIMENT: CHRONIC KIDNEY DISEASE PREDICTION (RANDOM FOREST)
# Configuration: Authentic UCI CKD Dataset (400 records), 13 Clinical Features,
#                70:30 Stratified Split, Leak-Free Preprocessing, seed=42
# ==============================================================================

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from ucimlrepo import fetch_ucirepo
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

def run_experiment():
    print("1. Fetching raw UCI Chronic Kidney Disease Dataset (ID: 336)...")
    ckd = fetch_ucirepo(id=336)
    X_raw = ckd.data.features.copy()
    y_raw = ckd.data.targets.copy()

    # Clean target column (strip whitespace and handle typos like ckd\t)
    y_clean = y_raw['class'].astype(str).str.strip()
    y = (y_clean == 'ckd').astype(int)  # 1 = CKD, 0 = Non-CKD

    # 13 clinical features corresponding exactly to ckd_app.py
    features_13 = [
        'bp', 'sg', 'al', 'su', 'rbc', 'bu', 'sc', 'sod', 'pot', 'hemo', 'wbcc', 'rbcc', 'htn'
    ]
    X = X_raw[features_13].copy()

    # Clean whitespace and null tokens in categorical columns
    for col in ['rbc', 'htn']:
        X[col] = X[col].astype(str).str.strip().replace({'nan': np.nan, 'None': np.nan, '?': np.nan})

    # --------------------------------------------------------------------------
    # DATA LEAKAGE PREVENTION CHECK 1: TRAIN-TEST SPLIT OCCURS BEFORE PREPROCESSING
    # --------------------------------------------------------------------------
    print("2. Performing 70:30 Stratified Train-Test Split (seed=42)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y
    )

    # --------------------------------------------------------------------------
    # DATA LEAKAGE PREVENTION CHECK 2: PREPROCESSORS FIT EXCLUSIVELY ON X_TRAIN
    # --------------------------------------------------------------------------
    num_cols = ['bp', 'sg', 'al', 'su', 'bu', 'sc', 'sod', 'pot', 'hemo', 'wbcc', 'rbcc']
    cat_cols = ['rbc', 'htn']

    imp_num = SimpleImputer(strategy='median')
    imp_cat = SimpleImputer(strategy='most_frequent')

    # Fit ONLY on training partition
    imp_num.fit(X_train[num_cols])
    imp_cat.fit(X_train[cat_cols])

    # Transform train and test partitions independently
    X_train_num = pd.DataFrame(imp_num.transform(X_train[num_cols]), columns=num_cols, index=X_train.index)
    X_train_cat = pd.DataFrame(imp_cat.transform(X_train[cat_cols]), columns=cat_cols, index=X_train.index)

    X_test_num = pd.DataFrame(imp_num.transform(X_test[num_cols]), columns=num_cols, index=X_test.index)
    X_test_cat = pd.DataFrame(imp_cat.transform(X_test[cat_cols]), columns=cat_cols, index=X_test.index)

    # Encode categorical features strictly based on training mapping
    for col in cat_cols:
        mapping = {val: i for i, val in enumerate(np.sort(X_train_cat[col].unique()))}
        X_train_cat[col] = X_train_cat[col].map(mapping)
        X_test_cat[col] = X_test_cat[col].map(mapping)

    X_train_clean = pd.concat([X_train_num, X_train_cat], axis=1)[features_13]
    X_test_clean = pd.concat([X_test_num, X_test_cat], axis=1)[features_13]

    # --------------------------------------------------------------------------
    # MODEL TRAINING: RANDOM FOREST CLASSIFIER
    # --------------------------------------------------------------------------
    print("3. Training RandomForestClassifier(n_estimators=100, criterion='gini', random_state=42)...")
    rf = RandomForestClassifier(n_estimators=100, criterion='gini', random_state=42)
    rf.fit(X_train_clean, y_train)

    # --------------------------------------------------------------------------
    # PREDICTION & EVALUATION ON TEST SET (N=120)
    # --------------------------------------------------------------------------
    print("4. Generating test predictions and metrics...")
    y_pred = rf.predict(X_test_clean)
    y_proba = rf.predict_proba(X_test_clean)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, pos_label=1)
    rec = recall_score(y_test, y_pred, pos_label=1)
    f1 = f1_score(y_test, y_pred, pos_label=1)
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    cr_text = classification_report(y_test, y_pred, digits=4, target_names=['Non-CKD (0)', 'CKD (1)'])

    print(f"Accuracy: {acc*100:.4f}%")
    print(f"Precision: {prec*100:.4f}%")
    print(f"Recall: {rec*100:.4f}%")
    print(f"F1-score: {f1*100:.4f}%")
    print("Confusion Matrix:\n", cm)
    print("\nClassification Report:\n", cr_text)

    # --------------------------------------------------------------------------
    # SAVE TEST PREDICTIONS TABLE (ckd_test_predictions.csv)
    # --------------------------------------------------------------------------
    pred_df = pd.DataFrame({
        'test_sample_id': range(1, len(y_test) + 1),
        'original_dataset_index': X_test.index,
        'actual_label': y_test.values,
        'actual_class_name': ['CKD' if y == 1 else 'Non-CKD' for y in y_test],
        'predicted_label': y_pred,
        'predicted_class_name': ['CKD' if p == 1 else 'Non-CKD' for p in y_pred],
        'probability_non_ckd_class_0': np.round(y_proba[:, 0], 4),
        'probability_ckd_class_1': np.round(y_proba[:, 1], 4),
        'prediction_status': ['CORRECT' if y == p else 'INCORRECT' for y, p in zip(y_test, y_pred)]
    })
    pred_df.to_csv('ckd_test_predictions.csv', index=False)
    print("Saved: ckd_test_predictions.csv")

    # --------------------------------------------------------------------------
    # SAVE CLASSIFICATION REPORT (ckd_classification_report.txt)
    # --------------------------------------------------------------------------
    with open('ckd_classification_report.txt', 'w') as f:
        f.write("==============================================================================\n")
        f.write("CHRONIC KIDNEY DISEASE PREDICTION: RANDOM FOREST CLASSIFICATION REPORT\n")
        f.write("==============================================================================\n\n")
        f.write(f"Dataset: UCI Chronic Kidney Disease (ID: 336)\n")
        f.write(f"Total Records: 400 | Features: 13 | Split: 70:30 Stratified\n")
        f.write(f"Train Samples: {len(X_train)} | Test Samples: {len(X_test)}\n")
        f.write(f"Random State: 42 | Classifier: RandomForestClassifier(n_estimators=100, criterion='gini')\n\n")
        f.write(f"Accuracy: {acc*100:.4f}% ({tp + tn}/{len(y_test)} correct predictions)\n")
        f.write(f"Precision (CKD): {prec*100:.4f}%\n")
        f.write(f"Recall (CKD): {rec*100:.4f}%\n")
        f.write(f"F1-score (CKD): {f1*100:.4f}%\n\n")
        f.write("Confusion Matrix (TN, FP / FN, TP):\n")
        f.write(f"[[{tn}, {fp}],\n [{fn}, {tp}]]\n\n")
        f.write("Detailed Breakdown:\n")
        f.write(f"True Negatives (TN): {tn}\n")
        f.write(f"False Positives (FP): {fp}\n")
        f.write(f"False Negatives (FN): {fn}\n")
        f.write(f"True Positives (TP): {tp}\n\n")
        f.write("Scikit-Learn Classification Report:\n")
        f.write(cr_text)
    print("Saved: ckd_classification_report.txt")

    # --------------------------------------------------------------------------
    # SAVE CONFUSION MATRIX PLOT (ckd_confusion_matrix.png)
    # --------------------------------------------------------------------------
    plt.figure(figsize=(7, 6))
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Blues', cbar=False,
        xticklabels=['Predicted Non-CKD (0)', 'Predicted CKD (1)'],
        yticklabels=['Actual Non-CKD (0)', 'Actual CKD (1)'],
        annot_kws={'size': 16, 'weight': 'bold'}
    )
    plt.title(f"CKD Random Forest Confusion Matrix (N=120)\nAccuracy: {acc*100:.2f}% ({tp + tn}/{len(y_test)} Correct)", fontsize=13, weight='bold', pad=15)
    plt.xlabel("Predicted Label", fontsize=11, weight='bold')
    plt.ylabel("Actual True Label", fontsize=11, weight='bold')
    plt.tight_layout()
    plt.savefig('ckd_confusion_matrix.png', dpi=300)
    plt.close()
    print("Saved: ckd_confusion_matrix.png")

if __name__ == '__main__':
    run_experiment()
