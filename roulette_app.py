import streamlit as st
import pandas as pd
import numpy as np
import re
from collections import Counter

PASSWORD = "1928"

# -------- Authentification ----------
if "auth_ok" not in st.session_state:
    st.session_state["auth_ok"] = False

if not st.session_state["auth_ok"]:
    st.markdown("## 🔒 Accès Sécurisé")
    with st.form("login_form"):
        pw = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("Accéder"):
            if pw == PASSWORD:
                st.session_state["auth_ok"] = True
                st.rerun()  # recharge proprement
            else:
                st.error("Mot de passe incorrect.")
    st.stop()

# ---------- Constantes ----------
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

    for i, num in enumerate(spins[::-1]):  # oldest → newest
        weight = w[i]
        if num == 0:
            color_cnt["Vert"] += weight
            par_cnt["Zéro"]   += weight
            doz_cnt["Zéro"]   += weight
        else:
            color_cnt["Rouge" if num in RED else "Noir"] += weight
            par_cnt["Pair" if num % 2 == 0 else "Impair"] += weight
            doz_cnt[str(1+(num-1)//12)] += weight
        num_cnt[num] += weight

    # Bonus run-length sur la couleur
    def col(n): return "Vert" if n==0 else ("Rouge" if n in RED else "Noir")
    def streak(seq):
        r = 1
        for i in range(1,len(seq)):
            if col(seq[-i]) == col(seq[-i-1]): r += 1
            else: break
        return r
    color_cnt[col(spins[-1])] *= 1 + 0.04 * streak(spins)**2

    # Bonus voisinage roue (±2 cases sur les 5 derniers)
    nb = Counter()
    for num in spins[-5:]:
        idx = POS[num]
        for k in (-2,-1,0,1,2):
            nb[ WHEEL[(idx+k)%37] ] += np.exp(-(k*k)/8)
    denom_nb = max(nb.values()) or 1

    scores = {n: num_cnt[n] + 0.4*(nb[n]/denom_nb) for n in range(37)}
    total_score = sum(scores.values()) or 1
    top5 = [(n, round(s/total_score*100,2)) for n,s in sorted(scores.items(), key=lambda x:-x[1])[:5]]

    # Normalisation en %
    for d in (color_cnt, par_cnt, doz_cnt):
        s = sum(d.values()) or 1
        for k in d: d[k] = round(100*d[k]/s,2)

    doz_read = {}
    for k,v in doz_cnt.items():
        if k=="Zéro": doz_read["Zéro"] = v
        elif k=="1":  doz_read["1-12"] = v
        elif k=="2":  doz_read["13-24"] = v
        elif k=="3":  doz_read["25-36"] = v

    return color_cnt, par_cnt, doz_read, top5

# ---------- Interface ----------
st.title("🎯 Algo Roulette – Prédictions")

with st.form("input"):
    user_numbers = st.text_area("Entrez les numéros (≥10) séparés par virgules, espaces ou tirets", height=120)
    submitted = st.form_submit_button("Calculer")

if submitted:
    spins = list(map(int, re.findall(r"\\d+", user_numbers)))
    if len(spins) < 10 or any(n > 36 for n in spins):
        st.warning("Veuillez entrer au moins 10 numéros compris entre 0 et 36.")
    else:
        color_p, parity_p, dozen_p, top5 = analyse(spins)

        col1,col2,col3 = st.columns(3)
        col1.subheader("Couleur (%)")
        col1.dataframe(pd.DataFrame(color_p.items(), columns=["Catégorie","Probabilité (%)"]).sort_values("Probabilité (%)", ascending=False),
                       hide_index=True, use_container_width=True)

        col2.subheader("Pair / Impair (%)")
        col2.dataframe(pd.DataFrame(parity_p.items(), columns=["Catégorie","Probabilité (%)"]).sort_values("Probabilité (%)", ascending=False),
                       hide_index=True, use_container_width=True)

        col3.subheader("Douzaines (%)")
        col3.dataframe(pd.DataFrame(dozen_p.items(), columns=["Catégorie","Probabilité (%)"]).sort_values("Probabilité (%)", ascending=False),
                       hide_index=True, use_container_width=True)

        st.markdown("### 🔢 Top 5 numéros")
        df_top = pd.DataFrame(top5, columns=["Numéro","Probabilité (%)"])
        st.dataframe(df_top, hide_index=True, use_container_width=True)

        # ------------ Top probas ------------
        st.markdown("### ⭐ Top probas")
        bests = [
            ("Couleur",  max(color_p,  key=color_p.get),  max(color_p.values())),
            ("Pair/Impair", max(parity_p, key=parity_p.get), max(parity_p.values())),
            ("Douzaine", max(dozen_p,  key=dozen_p.get),  max(dozen_p.values())),
            ("Numéro",  str(top5[0][0]), top5[0][1])
        ]
        top_df = pd.DataFrame(bests, columns=["Catégorie","Valeur","Probabilité (%)"]).sort_values("Probabilité (%)", ascending=False)

        def highlight_max(row):
            if row["Probabilité (%)"] == top_df["Probabilité (%)"].max():
                return ['background-color: #4FC3F7']*3
            return ['']*3

        st.dataframe(top_df.style.apply(highlight_max, axis=1), hide_index=True, use_container_width=True)
