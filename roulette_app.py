import streamlit as st
import pandas as pd
import numpy as np
import re
from collections import Counter

PASSWORD = "1928"

# ---------- Authentication ----------
if "auth_ok" not in st.session_state:
    st.session_state["auth_ok"] = False

if not st.session_state["auth_ok"]:
    st.markdown("## 🔒 Accès Sécurisé")
    with st.form("login_form"):
        pw = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("Accéder"):
            if pw == PASSWORD:
                st.session_state["auth_ok"] = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect.")
    st.stop()

# ---------- Constants ----------
RED   = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}
WHEEL = [0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,
         10,5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26]
POS = {n:i for i,n in enumerate(WHEEL)}
LAMBDA = 0.12

# ---------- Algo Roulette Def ----------
def analyse(spins):
    n = len(spins)
    w = np.exp(-LAMBDA * np.arange(n)[::-1])
    w /= w.sum()
    color_cnt, par_cnt, doz_cnt, num_cnt = Counter(), Counter(), Counter(), Counter()

    for i, num in enumerate(spins[::-1]):  # oldest→newest
        weight = w[i]
        if num == 0:
            color_cnt["Zéro"] += weight
            par_cnt["Zéro"]   += weight
            doz_cnt["Zéro"]   += weight
        else:
            color_cnt["Rouge" if num in RED else "Noir"] += weight
            par_cnt["Pair" if num % 2 == 0 else "Impair"] += weight
            doz_cnt[str(1 + (num-1)//12)] += weight
        num_cnt[num] += weight

    # run‐length bonus couleur
    def col(x): return "Zéro" if x == 0 else ("Rouge" if x in RED else "Noir")
    run = 1
    for i in range(1, len(spins)):
        if col(spins[-i]) == col(spins[-i-1]):
            run += 1
        else:
            break
    color_cnt[col(spins[-1])] *= 1 + 0.04 * run**2

    # voisinage roue
    nb = Counter()
    for num in spins[-5:]:
        idx = POS[num]
        for k in (-2,-1,0,1,2):
            nb[WHEEL[(idx+k)%37]] += np.exp(-(k*k)/8)
    denom = max(nb.values()) if nb else 1

    scores = {n: num_cnt[n] + 0.4*(nb[n]/denom) for n in range(37)}
    total_score = sum(scores.values()) or 1

    # normalise catégories
    for d in (color_cnt, par_cnt, doz_cnt):
        s = sum(d.values()) or 1
        for k in d:
            d[k] = round(100 * d[k] / s, 2)

    doz_map = {"1":"1-12", "2":"13-24", "3":"25-36"}
    dozen_prob = {doz_map.get(k, k): v for k, v in doz_cnt.items() if k != "Zéro"}

    top5 = sorted(scores.items(), key=lambda x: -x[1])[:5]
    top5_prob = [(n, round(s/total_score * 100, 2)) for n, s in top5]

    return color_cnt, par_cnt, dozen_prob, top5_prob

# ---------- UI ----------
st.title("🎯 Algo Roulette – Prédictions")

with st.form("input_form"):
    user_numbers = st.text_area(
        "Entrez au moins 10 numéros séparés par virgules, espaces ou tirets",
        height=120
    )
    submitted = st.form_submit_button("Calculer")

if submitted:
    spins = list(map(int, re.findall(r"\d+", user_numbers)))
    if len(spins) < 10 or any(n > 36 for n in spins):
        st.warning("Veuillez entrer au moins 10 numéros compris entre 0 et 36.")
    else:
        color_prob, parity_prob, dozen_prob, top5 = analyse(spins)

        # DataFrames triés
        df_color = (
            pd.DataFrame(color_prob.items(), columns=["Catégorie","Probabilité (%)"])
            .sort_values("Probabilité (%)", ascending=False)
        )
        df_par = (
            pd.DataFrame(parity_prob.items(), columns=["Catégorie","Probabilité (%)"])
            .sort_values("Probabilité (%)", ascending=False)
        )
        df_doz = (
            pd.DataFrame(dozen_prob.items(), columns=["Catégorie","Probabilité (%)"])
            .sort_values("Probabilité (%)", ascending=False)
        )

        # Affichage tableaux
        col1, col2, col3 = st.columns(3)
        col1.subheader("Couleur")
        col1.dataframe(df_color, hide_index=True, use_container_width=True)
        col2.subheader("Pair / Impair")
        col2.dataframe(df_par, hide_index=True, use_container_width=True)
        col3.subheader("Douzaines")
        col3.dataframe(df_doz, hide_index=True, use_container_width=True)

        # Top 5 numéros
        st.subheader("🔢 Top 5 numéros")
        df_top = pd.DataFrame({
            "Numéro": [str(n) for n,_ in top5],
            "Probabilité (%)": [p for _,p in top5]
        })
        st.dataframe(df_top, hide_index=True, use_container_width=True)

        # --------- Top probas block -------------
        st.subheader("⭐ Top probas")

        # calculer toutes les égalités
        max_color = max(color_prob.values())
        val_colors = [k for k,v in color_prob.items() if v == max_color]
        max_par = max(parity_prob.values())
        val_par = [k for k,v in parity_prob.items() if v == max_par]
        max_doz = max(dozen_prob.values())
        val_doz = [k for k,v in dozen_prob.items() if v == max_doz]
        max_num = max(p for n,p in top5)
        val_nums = [str(n) for n,p in top5 if p == max_num]

        bests = {
            "Couleur":    (val_colors, max_color),
            "Pair/Impair":(val_par,   max_par),
            "Douzaine":   (val_doz,   max_doz),
            "Numéro":     (val_nums,  max_num)
        }

        top_df = (
            pd.DataFrame([
                {"Catégorie": k,
                 "Probabilité (%)": round(v[1],2),
                 "Valeur": ", ".join(v[0])}
                for k,v in bests.items()
            ])
            .sort_values("Probabilité (%)", ascending=False)
        )

        # Surlignage et alignements
        max_prob = top_df["Probabilité (%)"].max()
        def highlight_all(row):
            bg = 'background-color: #4FC3F7' if row["Probabilité (%)"] == max_prob else ''
            return [bg, bg, bg]  # color Catégorie, Probabilité & Valeur

        styled = (
            top_df.style
                  .format({"Probabilité (%)":"{:.2f}"})
                  .apply(highlight_all, axis=1)
                  .set_properties(subset=["Probabilité (%)"], **{"text-align":"center"})
                  .set_properties(subset=["Valeur"], **{"text-align":"right"})
        )

        st.dataframe(
            styled,
            hide_index=True,
            use_container_width=True
        )
