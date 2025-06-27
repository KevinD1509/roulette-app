
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
    st.markdown("## 🔒 Accès Sécurisé")
    with st.form("login_form"):
        pw = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("Accéder"):
            if pw == PASSWORD:
                st.session_state["auth_ok"] = True
                st.experimental_rerun()
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

    color_cnt = Counter()
    par_cnt   = Counter()
    doz_cnt   = Counter()
    num_cnt   = Counter()

    for i,num in enumerate(spins[::-1]):  # oldest -> newest
        weight = w[i]
        if num == 0:
            color_cnt["Vert"] += weight
            par_cnt["Zéro"]   += weight
            doz_cnt["Zéro"]   += weight
        else:
            color_cnt["Rouge" if num in RED else "Noir"] += weight
            par_cnt["Pair" if num %2==0 else "Impair"]  += weight
            doz_cnt[str(1+(num-1)//12)] += weight
        num_cnt[num] += weight

    # run-length bonus couleur
    def streak(seq, func):
        run = 1
        for i in range(1,len(seq)):
            if func(seq[-i]) == func(seq[-i-1]):
                run += 1
            else:
                break
        return run
    def col(n): return "Vert" if n==0 else ("Rouge" if n in RED else "Noir")
    color_cnt[col(spins[-1])] *= 1 + 0.04 * streak(spins,col)**2

    # neighbour bonus
    nb = Counter()
    for num in spins[-5:]:
        idx = POS[num]
        for k in (-2,-1,0,1,2):
            nb[ WHEEL[(idx+k)%37] ] += np.exp(-(k*k)/8)
    denom_nb = max(nb.values()) if nb else 1

    scores = {n: num_cnt[n] + 0.4*(nb[n]/denom_nb) for n in range(37)}
    total_score = sum(scores.values()) or 1
    top5 = sorted(scores.items(), key=lambda x:-x[1])[:5]
    top5_prob = [(n, round(s/total_score*100,2)) for n,s in top5]

    # normalize categories to percentage
    for d in (color_cnt, par_cnt, doz_cnt):
        s = sum(d.values()) or 1
        for k in d:
            d[k] = round(100*d[k]/s, 2)

    # convert dozens key to readable
    doz_read = {}
    for k,v in doz_cnt.items():
        if k == "Zéro":
            doz_read["Zéro"] = v
        elif k == "1": doz_read["1-12"] = v
        elif k == "2": doz_read["13-24"] = v
        elif k == "3": doz_read["25-36"] = v
    return color_cnt, par_cnt, doz_read, top5_prob

# ---------- UI ----------
st.title("🎯 Algo Roulette – Prédictions")

with st.form("input_form"):
    user_numbers = st.text_area("Entrez les numéros (≥10) séparés par virgules, espaces ou tirets", height=120)
    submitted = st.form_submit_button("Calculer")

if submitted:
    spins = list(map(int, re.findall(r"\d+", user_numbers)))
    if len(spins) < 10 or any(n > 36 for n in spins):
        st.warning("Veuillez entrer au moins 10 numéros compris entre 0 et 36.")
    else:
        color_prob, parity_prob, dozen_prob, top5 = analyse(spins)

        # sort dictionaries descending
        color_df = pd.DataFrame(sorted(color_prob.items(), key=lambda x:-x[1]), columns=["Catégorie","Probabilité (%)"])
        parity_df = pd.DataFrame(sorted(parity_prob.items(), key=lambda x:-x[1]), columns=["Catégorie","Probabilité (%)"])
        dozen_df = pd.DataFrame(sorted(dozen_prob.items(), key=lambda x:-x[1]), columns=["Catégorie","Probabilité (%)"])

        col1,col2,col3 = st.columns(3)
        col1.subheader("Couleur (%)")
        col1.dataframe(color_df, hide_index=True, use_container_width=True)
        col2.subheader("Pair / Impair (%)")
        col2.dataframe(parity_df, hide_index=True, use_container_width=True)
        col3.subheader("Douzaines (%)")
        col3.dataframe(dozen_df, hide_index=True, use_container_width=True)

        st.markdown("### 🔢 Top 5 numéros")
        df_top = pd.DataFrame({"Numéro":[str(n) for n,_ in top5], "Probabilité (%)":[p for _,p in top5]})
        st.dataframe(df_top, hide_index=True, use_container_width=True)

        # -------- Top probas block --------
        best_color = max(color_prob.items(), key=lambda x:x[1])
        best_parity = max(parity_prob.items(), key=lambda x:x[1])
        best_dozen = max(dozen_prob.items(), key=lambda x:x[1])
        best_num = top5[0]

        top_rows = [
            {"Catégorie":"Couleur","Valeur":best_color[0],"Probabilité (%)":best_color[1]},
            {"Catégorie":"Pair/Impair","Valeur":best_parity[0],"Probabilité (%)":best_parity[1]},
            {"Catégorie":"Douzaine","Valeur":best_dozen[0],"Probabilité (%)":best_dozen[1]},
            {"Catégorie":"Numéro","Valeur":str(best_num[0]),"Probabilité (%)":best_num[1]},
        ]
        top_df = pd.DataFrame(top_rows).sort_values("Probabilité (%)", ascending=False).reset_index(drop=True)

        def highlight_max(s):
            max_val = s["Probabilité (%)"].max()
            return ['background-color: #4FC3F7' if v==max_val else '' for v in s["Probabilité (%)"]]

        st.markdown("### ⭐ Top probas")
        st.dataframe(top_df.style.apply(lambda x: ['background-color: #4FC3F7' if v==top_df['Probabilité (%)'].max() else '' for v in x['Probabilité (%)']], axis=1), hide_index=True, use_container_width=True)
