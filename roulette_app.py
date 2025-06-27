
import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
from datetime import datetime

# Mot de passe unique
PASSWORD = "1928"

# Authentification simple avec bouton
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("Accès sécurisé")
    pwd = st.text_input("Entrez le mot de passe", type="password")
    if st.button("Accéder"):
        if pwd == PASSWORD:
            st.session_state["authenticated"] = True
            st.experimental_rerun()
        else:
            st.error("Mot de passe incorrect.")
    st.stop()

# Interface principale
st.title("🎯 Algo Roulette - Analyse des prochains tirages")

user_input = st.text_input("Entrez les numéros précédents (séparés par des tirets)", value="")

if st.button("Calculer"):
    try:
        spins = [int(x) for x in user_input.strip().split("-") if x.strip() != ""]
    except ValueError:
        st.error("Veuillez entrer uniquement des nombres valides séparés par des tirets.")
        st.stop()

    if len(spins) < 10:
        st.error("Veuillez entrer au moins 10 numéros.")
        st.stop()

    if any(x > 36 for x in spins):
        st.error("Tous les numéros doivent être inférieurs ou égaux à 36.")
        st.stop()

    # ANALYSE
    reds = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
    blacks = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}
    greens = {0}

    last = spins[-1]
    recent_weights = np.linspace(1.0, 2.0, num=len(spins))

    def weighted_score(values):
        counts = Counter()
        for i, val in enumerate(spins):
            counts[val] += recent_weights[i]
        return dict(counts)

    weighted_counts = weighted_score(spins)
    sorted_nums = sorted(weighted_counts.items(), key=lambda x: -x[1])
    top_numbers = [num for num, _ in sorted_nums[:5]]

    total = sum(weighted_counts.values())
    color_probs = {
        "Rouge": sum(weighted_counts[n] for n in reds & weighted_counts.keys()) / total * 100,
        "Noir": sum(weighted_counts[n] for n in blacks & weighted_counts.keys()) / total * 100,
        "Vert (0)": sum(weighted_counts[n] for n in greens & weighted_counts.keys()) / total * 100,
    }

    parity_probs = {
        "Pair": sum(weighted_counts[n] for n in weighted_counts if n != 0 and n % 2 == 0) / total * 100,
        "Impair": sum(weighted_counts[n] for n in weighted_counts if n % 2 == 1) / total * 100,
        "Zéro": weighted_counts.get(0, 0) / total * 100,
    }

    dozen_probs = {
        "1ère douzaine (1–12)": sum(weighted_counts[n] for n in range(1,13)) / total * 100,
        "2e douzaine (13–24)": sum(weighted_counts[n] for n in range(13,25)) / total * 100,
        "3e douzaine (25–36)": sum(weighted_counts[n] for n in range(25,37)) / total * 100,
    }

    st.subheader("🎨 Probabilité par couleur")
    df_color = pd.DataFrame({
        "Catégorie": list(color_probs.keys()),
        "Probabilité (%)": list(color_probs.values())
    })
    st.dataframe(df_color)

    st.subheader("➗ Probabilité pair / impair")
    df_parity = pd.DataFrame({
        "Catégorie": list(parity_probs.keys()),
        "Probabilité (%)": list(parity_probs.values())
    })
    st.dataframe(df_parity)

    st.subheader("📊 Probabilité par douzaine")
    df_dozen = pd.DataFrame({
        "Catégorie": list(dozen_probs.keys()),
        "Probabilité (%)": list(dozen_probs.values())
    })
    st.dataframe(df_dozen)

    st.subheader("🎯 Top 5 numéros")
    df_top = pd.DataFrame({
        "Numéro": [str(n) for n in top_numbers],
        "Probabilité (%)": [round(weighted_counts[n] / total * 100, 2) for n in top_numbers]
    })
    st.dataframe(df_top)
