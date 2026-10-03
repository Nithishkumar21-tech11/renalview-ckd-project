
import streamlit as st
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(page_title="CKD Prediction", page_icon="💉", layout="centered")
st.title("Chronic Kidney Disease Prediction System")

# ================= Load Model =================
try:
    model = joblib.load("rf.pkl")
except:
    st.error("Model file rf.pkl not found. Please ensure it's in the same folder.")
    st.stop()

# ================= Input Fields =================
st.subheader("Enter Patient Details:")

Bp = st.number_input("Blood Pressure", 0.0, 200.0)
Sg = st.number_input("Specific Gravity", 1.0, 1.05, step=0.01)
Al = st.number_input("Albumin", 0.0, 5.0)
Su = st.number_input("Sugar", 0.0, 5.0)
Rbc = st.number_input("Red Blood Cells (0 or 1)", 0, 1)
Bu = st.number_input("Blood Urea", 0.0, 200.0)
Sc = st.number_input("Serum Creatinine", 0.0, 20.0)
Sod = st.number_input("Sodium", 100.0, 160.0)
Pot = st.number_input("Potassium", 2.0, 10.0)
Hemo = st.number_input("Hemoglobin", 0.0, 25.0)
Wbcc = st.number_input("White Blood Cell Count", 1000.0, 50000.0)
Rbcc = st.number_input("Red Blood Cell Count", 0.0, 10.0)
Htn = st.number_input("Hypertension (0/1)", 0, 1)

# ================= Prediction =================
if st.button("Predict"):
    sample = np.array([[Bp,Sg,Al,Su,Rbc,Bu,Sc,Sod,Pot,Hemo,Wbcc,Rbcc,Htn]])
    prediction = model.predict(sample)

    if prediction[0] == 1:
        st.error("⚠️ Patient is Affected by Chronic Kidney Disease")
    else:
        st.success("✅ Patient is Not Affected by Chronic Kidney Disease")
