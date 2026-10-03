# Chronic Kidney Disease Prediction: Reproducible Mathematical & Programmatic Proof Report

**Project**: Chronic Kidney Disease Prediction System  
**Model Architecture**: Random Forest Classifier (`RandomForestClassifier`)  
**Evaluation Benchmark**: Configuration 3 — Authentic UCI Machine Learning Repository Dataset (ID: 336)  
**Date of Audit**: September 16, 2026  

---

## 1. Experimental Setup & Configuration Summary

* **Dataset**: UCI Machine Learning Repository — Chronic Kidney Disease Dataset (ID: 336)
* **Total Instances**: 400 patient records
  * Chronic Kidney Disease (CKD, Class 1): 250 records (62.5%)
  * Non-Chronic Kidney Disease (Non-CKD, Class 0): 150 records (37.5%)
* **Number of Features Used**: Exactly 13 clinical features matching the deployment application (`ckd_app.py`):
  1. `bp` — Blood Pressure (mm/Hg)
  2. `sg` — Specific Gravity
  3. `al` — Albumin (0 to 5)
  4. `su` — Sugar (0 to 5)
  5. `rbc` — Red Blood Cells (normal / abnormal)
  6. `bu` — Blood Urea (mgs/dl)
  7. `sc` — Serum Creatinine (mgs/dl)
  8. `sod` — Sodium (mEq/L)
  9. `pot` — Potassium (mEq/L)
  10. `hemo` — Hemoglobin (gms)
  11. `wbcc` — White Blood Cell Count (cells/cumm)
  12. `rbcc` — Red Blood Cell Count (millions/cmm)
  13. `htn` — Hypertension (yes / no)
* **Target Variable**: `class` (Cleaned binary encoding: `ckd` -> 1, `notckd` -> 0)
* **Data Splitting**:
  * Train-to-Test Ratio: 70% Training : 30% Testing
  * Stratification: Enabled (`stratify=y` preserves the 62.5% : 37.5% class distribution)
  * Random State: `42`
  * Total Training Samples ($N_{train}$): **280** (175 CKD, 105 Non-CKD)
  * Total Testing Samples ($N_{test}$): **120** (75 CKD, 45 Non-CKD)
* **Random Forest Hyperparameters**:
  * `n_estimators`: 100
  * `criterion`: `'gini'`
  * `max_depth`: `None` (expanded until leaves are pure)
  * `min_samples_split`: 2
  * `min_samples_leaf`: 1
  * `max_features`: `'sqrt'` (~3.6 features considered per split)
  * `bootstrap`: `True`
  * `random_state`: `42`

---

## 2. Leak-Free Preprocessing Pipeline

To eliminate any possibility of data snooping or optimistic bias:
1. **Train-Test Split Before Imputation**: The 70:30 split was executed directly on raw features *before* computing summary statistics.
2. **Numeric Feature Imputation**: Continuous missing values were imputed using `SimpleImputer(strategy='median')` fitted exclusively on the 280 training samples. The learned training medians were subsequently applied to transform both the train and test partitions.
3. **Categorical Feature Imputation**: Missing values in `rbc` and `htn` were imputed using `SimpleImputer(strategy='most_frequent')` fitted exclusively on the training partition.
4. **Encoding**: Categorical mappings (`normal`/`abnormal`, `yes`/`no`) were derived strictly from the training partition.

---

## 3. Data Leakage Verification Audit

| Leakage Dimension | Audit Procedure | Result | Status |
|---|---|---|---|
| **Target Leakage** | Verified target `class` is isolated from feature matrix $X$ | Feature matrix contains only the 13 clinical biomarkers | **PASSED (No Leakage)** |
| **Test Set Contamination** | Verified `fit()` is called only on `X_train` ($N=280$) | `imp_num.fit(X_train)`, `imp_cat.fit(X_train)`, `rf.fit(X_train_clean, y_train)` | **PASSED (No Leakage)** |
| **Information Spillover** | Test instances never inform imputation medians or modes | Test transform uses `imp.transform(X_test)` without refitting | **PASSED (No Leakage)** |
| **Row Duplication** | Checked pairwise overlap between train and test rows | 0 duplicate rows shared between train and test sets | **PASSED (No Leakage)** |
| **Feature Selection Bias** | Checked whether feature selection used test labels | All 13 features predefined by project domain design | **PASSED (No Leakage)** |

---

## 4. Complete Test-Set Predictions (All 120 Unseen Patients)

The following table records every test sample prediction evaluated by the model:

| # | Orig Index | Actual Class | Predicted Class | P(Non-CKD) | P(CKD) | Status |
|---|---|---|---|---|---|---|
| 1 | 127 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 2 | 356 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 3 | 128 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 4 | 298 | Non-CKD (0) | Non-CKD (0) | 0.9900 | 0.0100 | **CORRECT** |
| 5 | 217 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 6 | 74 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 7 | 170 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 8 | 352 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 9 | 65 | CKD (1) | CKD (1) | 0.1600 | 0.8400 | **CORRECT** |
| 10 | 264 | Non-CKD (0) | Non-CKD (0) | 0.9600 | 0.0400 | **CORRECT** |
| 11 | 219 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 12 | 159 | CKD (1) | CKD (1) | 0.0300 | 0.9700 | **CORRECT** |
| 13 | 399 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 14 | 61 | CKD (1) | CKD (1) | 0.0500 | 0.9500 | **CORRECT** |
| 15 | 376 | Non-CKD (0) | Non-CKD (0) | 0.9800 | 0.0200 | **CORRECT** |
| 16 | 95 | CKD (1) | CKD (1) | 0.0800 | 0.9200 | **CORRECT** |
| 17 | 50 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 18 | 362 | Non-CKD (0) | Non-CKD (0) | 0.9500 | 0.0500 | **CORRECT** |
| 19 | 70 | CKD (1) | CKD (1) | 0.1100 | 0.8900 | **CORRECT** |
| 20 | 85 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 21 | 1 | CKD (1) | CKD (1) | 0.1500 | 0.8500 | **CORRECT** |
| 22 | 309 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 23 | 150 | CKD (1) | CKD (1) | 0.2000 | 0.8000 | **CORRECT** |
| 24 | 218 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 25 | 189 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 26 | 58 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 27 | 197 | CKD (1) | CKD (1) | 0.0100 | 0.9900 | **CORRECT** |
| 28 | 357 | Non-CKD (0) | Non-CKD (0) | 0.9900 | 0.0100 | **CORRECT** |
| 29 | 184 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 30 | 311 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 31 | 142 | CKD (1) | CKD (1) | 0.0500 | 0.9500 | **CORRECT** |
| 32 | 117 | CKD (1) | CKD (1) | 0.1500 | 0.8500 | **CORRECT** |
| 33 | 100 | CKD (1) | CKD (1) | 0.0800 | 0.9200 | **CORRECT** |
| 34 | 83 | CKD (1) | CKD (1) | 0.0900 | 0.9100 | **CORRECT** |
| 35 | 186 | CKD (1) | CKD (1) | 0.4100 | 0.5900 | **CORRECT** |
| 36 | 27 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 37 | 230 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 38 | 349 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 39 | 380 | Non-CKD (0) | Non-CKD (0) | 0.9800 | 0.0200 | **CORRECT** |
| 40 | 270 | Non-CKD (0) | Non-CKD (0) | 0.9900 | 0.0100 | **CORRECT** |
| 41 | 342 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 42 | 252 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 43 | 216 | CKD (1) | CKD (1) | 0.0200 | 0.9800 | **CORRECT** |
| 44 | 179 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 45 | 365 | Non-CKD (0) | Non-CKD (0) | 0.8000 | 0.2000 | **CORRECT** |
| 46 | 329 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 47 | 204 | CKD (1) | CKD (1) | 0.0300 | 0.9700 | **CORRECT** |
| 48 | 11 | CKD (1) | CKD (1) | 0.0100 | 0.9900 | **CORRECT** |
| 49 | 340 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 50 | 215 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 51 | 26 | CKD (1) | CKD (1) | 0.0100 | 0.9900 | **CORRECT** |
| 52 | 80 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 53 | 102 | CKD (1) | CKD (1) | 0.2100 | 0.7900 | **CORRECT** |
| 54 | 324 | Non-CKD (0) | Non-CKD (0) | 0.6600 | 0.3400 | **CORRECT** |
| 55 | 374 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 56 | 193 | CKD (1) | CKD (1) | 0.0300 | 0.9700 | **CORRECT** |
| 57 | 350 | Non-CKD (0) | Non-CKD (0) | 0.9300 | 0.0700 | **CORRECT** |
| 58 | 371 | Non-CKD (0) | Non-CKD (0) | 0.9900 | 0.0100 | **CORRECT** |
| 59 | 38 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 60 | 302 | Non-CKD (0) | Non-CKD (0) | 0.9900 | 0.0100 | **CORRECT** |
| 61 | 199 | CKD (1) | CKD (1) | 0.0100 | 0.9900 | **CORRECT** |
| 62 | 43 | CKD (1) | CKD (1) | 0.0100 | 0.9900 | **CORRECT** |
| 63 | 169 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 64 | 120 | CKD (1) | CKD (1) | 0.0400 | 0.9600 | **CORRECT** |
| 65 | 183 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 66 | 338 | Non-CKD (0) | Non-CKD (0) | 0.9900 | 0.0100 | **CORRECT** |
| 67 | 256 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 68 | 154 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 69 | 164 | CKD (1) | CKD (1) | 0.2600 | 0.7400 | **CORRECT** |
| 70 | 236 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 71 | 130 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 72 | 107 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 73 | 394 | Non-CKD (0) | Non-CKD (0) | 0.9400 | 0.0600 | **CORRECT** |
| 74 | 389 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 75 | 86 | CKD (1) | CKD (1) | 0.0700 | 0.9300 | **CORRECT** |
| 76 | 308 | Non-CKD (0) | Non-CKD (0) | 0.9800 | 0.0200 | **CORRECT** |
| 77 | 205 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 78 | 29 | CKD (1) | CKD (1) | 0.0100 | 0.9900 | **CORRECT** |
| 79 | 313 | Non-CKD (0) | Non-CKD (0) | 0.9700 | 0.0300 | **CORRECT** |
| 80 | 251 | Non-CKD (0) | Non-CKD (0) | 0.9900 | 0.0100 | **CORRECT** |
| 81 | 187 | CKD (1) | CKD (1) | 0.0200 | 0.9800 | **CORRECT** |
| 82 | 296 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 83 | 112 | CKD (1) | CKD (1) | 0.0300 | 0.9700 | **CORRECT** |
| 84 | 307 | Non-CKD (0) | Non-CKD (0) | 0.9700 | 0.0300 | **CORRECT** |
| 85 | 146 | CKD (1) | CKD (1) | 0.0300 | 0.9700 | **CORRECT** |
| 86 | 241 | CKD (1) | CKD (1) | 0.0100 | 0.9900 | **CORRECT** |
| 87 | 2 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 88 | 304 | Non-CKD (0) | Non-CKD (0) | 0.8500 | 0.1500 | **CORRECT** |
| 89 | 366 | Non-CKD (0) | Non-CKD (0) | 0.9900 | 0.0100 | **CORRECT** |
| 90 | 125 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 91 | 397 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 92 | 390 | Non-CKD (0) | Non-CKD (0) | 0.9800 | 0.0200 | **CORRECT** |
| 93 | 44 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 94 | 136 | CKD (1) | CKD (1) | 0.0800 | 0.9200 | **CORRECT** |
| 95 | 115 | CKD (1) | CKD (1) | 0.0700 | 0.9300 | **CORRECT** |
| 96 | 353 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 97 | 171 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 98 | 291 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 99 | 51 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 100 | 379 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 101 | 185 | CKD (1) | CKD (1) | 0.2800 | 0.7200 | **CORRECT** |
| 102 | 248 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 103 | 321 | Non-CKD (0) | Non-CKD (0) | 0.9800 | 0.0200 | **CORRECT** |
| 104 | 237 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 105 | 12 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 106 | 28 | CKD (1) | CKD (1) | 0.0100 | 0.9900 | **CORRECT** |
| 107 | 53 | CKD (1) | CKD (1) | 0.0600 | 0.9400 | **CORRECT** |
| 108 | 129 | CKD (1) | CKD (1) | 0.0400 | 0.9600 | **CORRECT** |
| 109 | 195 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 110 | 35 | CKD (1) | CKD (1) | 0.0200 | 0.9800 | **CORRECT** |
| 111 | 224 | CKD (1) | CKD (1) | 0.1100 | 0.8900 | **CORRECT** |
| 112 | 337 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 113 | 91 | CKD (1) | CKD (1) | 0.2100 | 0.7900 | **CORRECT** |
| 114 | 300 | Non-CKD (0) | Non-CKD (0) | 0.9900 | 0.0100 | **CORRECT** |
| 115 | 287 | Non-CKD (0) | Non-CKD (0) | 0.8600 | 0.1400 | **CORRECT** |
| 116 | 271 | Non-CKD (0) | Non-CKD (0) | 1.0000 | 0.0000 | **CORRECT** |
| 117 | 233 | CKD (1) | CKD (1) | 0.0600 | 0.9400 | **CORRECT** |
| 118 | 133 | CKD (1) | CKD (1) | 0.1100 | 0.8900 | **CORRECT** |
| 119 | 151 | CKD (1) | CKD (1) | 0.0000 | 1.0000 | **CORRECT** |
| 120 | 341 | Non-CKD (0) | Non-CKD (0) | 0.9800 | 0.0200 | **CORRECT** |

* **Total Correct Predictions**: **120 / 120** (100.0%)
* **Total Incorrect Predictions**: **0 / 120** (0.0%)

---

## 5. Confusion Matrix & Mathematical Proof of Metrics

### Contingency Table (Confusion Matrix)

| | Predicted Non-CKD (0) | Predicted CKD (1) | Total |
|---|---|---|---|
| **Actual Non-CKD (0)** | **45 (TN)** | **0 (FP)** | **45** |
| **Actual CKD (1)** | **0 (FN)** | **75 (TP)** | **75** |
| **Total** | **45** | **75** | **120** |

* **True Positives ($TP$)**: 75 (Patients with CKD correctly identified as CKD)
* **True Negatives ($TN$)**: 45 (Healthy patients correctly identified as Non-CKD)
* **False Positives ($FP$)**: 0 (No healthy patient misdiagnosed with CKD)
* **False Negatives ($FN$)**: 0 (No CKD patient missed)

### Exact Step-by-Step Mathematical Calculations

1. **Accuracy**:
   $$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN} = \frac{75 + 45}{75 + 45 + 0 + 0} = \frac{120}{120} = 1.0000 \quad (100.0\%)$$

2. **Precision (Positive Predictive Value for CKD)**:
   $$\text{Precision} = \frac{TP}{TP + FP} = \frac{75}{75 + 0} = \frac{75}{75} = 1.0000 \quad (100.0\%)$$

3. **Recall / Sensitivity (True Positive Rate for CKD)**:
   $$\text{Recall} = \frac{TP}{TP + FN} = \frac{75}{75 + 0} = \frac{75}{75} = 1.0000 \quad (100.0\%)$$

4. **Specificity (True Negative Rate for Non-CKD)**:
   $$\text{Specificity} = \frac{TN}{TN + FP} = \frac{45}{45 + 0} = \frac{45}{45} = 1.0000 \quad (100.0\%)$$

5. **F1-Score (Harmonic Mean of Precision and Recall)**:
   $$\text{F1-Score} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}} = 2 \times \frac{1.0000 \times 1.0000}{1.0000 + 1.0000} = \frac{2.0000}{2.0000} = 1.0000 \quad (100.0\%)$$

---

## 6. Clinical & Algorithmic Explanation: Why is the Result 100%?

Achieving 100% on a machine learning benchmark must always be scrutinized. Here is the empirical and clinical evidence explaining why this occurs:

1. **Pathophysiological Biomarker Separation**:
   In human nephrology, chronic kidney failure induces severe physiological disruptions that produce non-overlapping distributions against healthy controls:
   * **Hemoglobin (`hemo`)** (Feature Importance: **27.61%**): Failing kidneys stop producing erythropoietin, driving severe renal anemia.
   * **Serum Creatinine (`sc`)** (Feature Importance: **22.06%**): Decreased Glomerular Filtration Rate (GFR) causes profound creatinine retention in the bloodstream.
   * **Specific Gravity (`sg`)** (Feature Importance: **13.76%**): Loss of tubular concentrating capacity impairs urine concentration.
   * **Red Blood Cell Count (`rbcc`)** (Feature Importance: **11.19%**): Parallels severe anemia.
   Together, these four biomarkers alone account for **74.62%** of the model's split decisions.

2. **Wide Probability Margins (No Borderline Overlap)**:
   * Minimum predicted probability of CKD among true CKD patients: **0.5900** (Mean: **0.9544** / 95.44% confidence).
   * Maximum predicted probability of CKD among healthy patients: **0.3400** (Mean: **0.0293** / 97.07% confidence of being healthy).
   * At the standard decision boundary of $\tau = 0.50$, the positive and negative distributions are completely separated with a substantial safety margin.

---

## 7. GUIDE VERIFICATION

This section directly answers the exact verification questions for academic committees and project guides:

* **a) What dataset was used?**  
  The official UCI Machine Learning Repository Chronic Kidney Disease Dataset (Dataset ID: 336), compiled by Apollo Hospitals, India.
* **b) How many records were used?**  
  400 patient records (250 CKD positive, 150 non-CKD negative).
* **c) What 13 features were used?**  
  `bp`, `sg`, `al`, `su`, `rbc`, `bu`, `sc`, `sod`, `pot`, `hemo`, `wbcc`, `rbcc`, `htn`.
* **d) How many training samples?**  
  280 samples (70% stratified training partition: 175 CKD, 105 Non-CKD).
* **e) How many testing samples?**  
  120 samples (30% stratified testing partition: 75 CKD, 45 Non-CKD).
* **f) How many predictions were correct?**  
  120 out of 120 predictions.
* **g) How many were incorrect?**  
  0 out of 120 predictions.
* **h) What is the confusion matrix?**  
  `[[45, 0], [0, 75]]` (TN=45, FP=0, FN=0, TP=75).
* **i) How is the accuracy mathematically calculated?**  
  $$\text{Accuracy} = \frac{TP + TN}{N_{test}} = \frac{75 + 45}{120} = \frac{120}{120} = 100.0\%$$
* **j) What are precision, recall, and F1-score?**  
  Precision: 100.0% (1.0000), Recall: 100.0% (1.0000), F1-Score: 100.0% (1.0000).
* **k) Can the experiment be reproduced?**  
  Yes. Running `python ckd_reproduce_verified.py` fetches the raw UCI repository, performs the exact pipeline with seed 42, and deterministically reproduces these exact numbers.
* **l) Is there any data leakage?**  
  No. Splitting was executed before preprocessing, imputers and encoders were fit strictly on the 280 training samples, zero rows are duplicated across partitions, and the target column was never included in the input feature space.

---

## 8. Artifact File Index

* `ckd_reproduce_verified.py`: Complete reproducible Python pipeline.
* `ckd_test_predictions.csv`: Per-patient test prediction records (all 120 test cases).
* `ckd_classification_report.txt`: Official scikit-learn text output.
* `ckd_confusion_matrix.png`: High-resolution confusion matrix heatmap.
