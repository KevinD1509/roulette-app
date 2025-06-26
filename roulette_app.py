
import streamlit as st
import numpy as np
import pandas as pd
from collections import Counter
from datetime import datetime

# --- Authentification simple ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "1928":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Mot de passe", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Mot de passe", type="password", on_change=password_entered, key="password")
        st.error("Mot de passe incorrect.")
        return False
    else:
        return True

# --- Analyse principale ---
def analyse_roulette(history):
    N = len(history)
    if N < 10:
        return "Entrez au moins 10 tirages", {}

    history = [int(n) for n in history if n.isdigit()]
    recent = history[-30:] if N >= 30 else history

    # Probabilité couleur
    red = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
    black = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}
    reds = sum(1 for x in recent if x in red)
    blacks = sum(1 for x in recent if x in black)
    color_prob = {
        "Rouge": round(100 * reds / len(recent), 2),
        "Noir": round(100 * blacks / len(recent), 2),
        "Vert (0)": round(100 * recent.count(0) / len(recent), 2)
    }

    # Paires/impaire
    evens = sum(1 for x in recent if x != 0 and x % 2 == 0)
    odds = sum(1 for x in recent if x != 0 and x % 2 == 1)
    pair_impair = {
        "Pair": round(100 * evens / len(recent), 2),
        "Impair": round(100 * odds / len(recent), 2)
    }

    # Douzaines
    dozens = {"1-12": 0, "13-24": 0, "25-36": 0}
    for x in recent:
        if 1 <= x <= 12:
            dozens["1-12"] += 1
        elif 13 <= x <= 24:
            dozens["13-24"] += 1
        elif 25 <= x <= 36:
            dozens["25-36"] += 1
    dozens = {k: round(100 * v / len(recent), 2) for k, v in dozens.items()}

    # Cinq numéros les plus probables (fréquence simple)
    freq = Counter(recent)
    top_numbers = [n for n, _ in freq.most_common(5)]

    results = {
        "Probabilités couleur (%)": color_prob,
        "Pair / Impair (%)": pair_impair,
        "Douzaines (%)": dozens,
        "Top 5 numéros les plus fréquents": top_numbers
    }

    return None, results

# --- Affichage ---
if check_password():
    st.title("🎰 Prédicteur Roulette – Algo Roulette")
    st.markdown("Entrez entre 10 et ∞ derniers tirages (ex: `1, 4, 23, ...`)")

    user_input = st.text_area("Historique des tirages", height=150)
    history = [x.strip() for x in user_input.split(",") if x.strip().isdigit()]

    if len(history) >= 10:
        err, result = analyse_roulette(history)
        if err:
            st.warning(err)
        else:
            for section, val in result.items():
                st.subheader(section)
                if isinstance(val, dict):
                    st.write(pd.DataFrame(val.items(), columns=["Catégorie", "Probabilité (%)"]))
                else:
                    st.write(", ".join(map(str, val)))
