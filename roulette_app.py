
import streamlit as st
import numpy as np
import pandas as pd
from collections import Counter
import re

PASSWORD = "1928"

# -------------- Auth -----------------
if "auth_ok" not in st.session_state:
    st.session_state["auth_ok"] = False

if not st.session_state["auth_ok"]:
    pw = st.text_input("Mot de passe", type="password")
    if pw == PASSWORD:
        st.session_state["auth_ok"] = True
        st.experimental_rerun()
    else:
        st.stop()

# -------------- Constantes -----------
RED   = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}

# -------------- Analyse --------------
def analyse(history):
    recent = history[-30:] if len(history) >= 30 else history

    total = len(recent)
    reds   = sum(1 for x in recent if x in RED)
    blacks = sum(1 for x in recent if x in BLACK)
    greens = recent.count(0)

    color_prob = {
        "Rouge": round(100*reds/total, 2),
        "Noir": round(100*blacks/total, 2),
        "Vert": round(100*greens/total, 2)
    }

    evens = sum(1 for x in recent if x != 0 and x % 2 == 0)
    odds  = sum(1 for x in recent if x != 0 and x % 2 == 1)
    pair_impair = {
        "Pair": round(100*evens/total, 2),
        "Impair": round(100*odds/total, 2)
    }

    dozens = {"1-12":0, "13-24":0, "25-36":0}
    for x in recent:
        if 1 <= x <= 12: dozens["1-12"] += 1
        elif 13 <= x <= 24: dozens["13-24"] += 1
        elif 25 <= x <= 36: dozens["25-36"] += 1
    dozens = {k: round(100*v/total, 2) for k,v in dozens.items()}

    freq = Counter(recent).most_common(5)

    return color_prob, pair_impair, dozens, freq

# -------------- Interface ------------
st.title("🎯 Algo Roulette – Prédictions")

with st.form("input_form"):
    user_numbers = st.text_area("Entrez les numéros (≥10) séparés par , ou espace", height=120)
    submitted = st.form_submit_button("Calculer")

if submitted:
    nums = list(map(int, re.findall(r"\d+", user_numbers)))
    if len(nums) < 10:
        st.warning("Veuillez entrer au moins 10 numéros.")
    else:
        color_prob, pair_impair, dozens, top5 = analyse(nums)

        # Affichage
        col1,col2,col3 = st.columns(3)

        col1.subheader("Couleur (%)")
        col1.dataframe(pd.DataFrame(color_prob.items(), columns=["Catégorie","Probabilité"]), hide_index=True)

        col2.subheader("Pair / Impair (%)")
        col2.dataframe(pd.DataFrame(pair_impair.items(), columns=["Catégorie","Probabilité"]), hide_index=True)

        col3.subheader("Douzaines (%)")
        col3.dataframe(pd.DataFrame(dozens.items(), columns=["Catégorie","Probabilité"]), hide_index=True)

        st.markdown("### 🔢 Top 5 numéros")
        st.dataframe(pd.DataFrame(top5, columns=["Numéro","Occurrences"]), hide_index=True)
