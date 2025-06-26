
import streamlit as st
import numpy as np
import pandas as pd
import re
from collections import Counter

# ---------------- AUTH -----------------
PASSWORD = "1928"
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    with st.form("login_form"):
        pw = st.text_input("Mot de passe", type="password")
        ok = st.form_submit_button("Accéder")
        if ok:
            if pw == PASSWORD:
                st.session_state["auth"] = True
            else:
                st.error("Mot de passe incorrect.")
    st.stop()

# ------------- CONSTANTS ---------------
RED   = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}
WHEEL = [0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,
         10,5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26]
POS   = {n:i for i,n in enumerate(WHEEL)}

# ------------- ALGO --------------------
def algo_scores(history, lam=0.12):
    n = len(history)
    w = np.exp(-lam*np.arange(n)[::-1]); w /= w.sum()

    # base weighted frequency
    score = {i:0.0 for i in range(37)}
    for i, num in enumerate(history[::-1]):  # oldest→newest
        score[num] += w[i]

    # neighbour bonus on wheel (last 5)
    nb = Counter()
    for num in history[-5:]:
        idx = POS[num]
        for k in (-2,-1,0,1,2):
            nb[ WHEEL[(idx+k)%37] ] += np.exp(-(k*k)/8)
    if nb:
        max_nb = max(nb.values())
        for n in score:
            score[n] += 0.4 * (nb[n]/max_nb)

    return score

def analyse(history):
    total = len(history)
    recent = history[-30:] if total>30 else history

    reds   = sum(1 for x in recent if x in RED)
    blacks = sum(1 for x in recent if x in BLACK)
    greens = recent.count(0)
    color_prob = {"Rouge":round(100*reds/len(recent),2),
                  "Noir": round(100*blacks/len(recent),2),
                  "Vert": round(100*greens/len(recent),2)}

    evens = sum(1 for x in recent if x!=0 and x%2==0)
    odds  = sum(1 for x in recent if x!=0 and x%2==1)
    pair_impair = {"Pair":round(100*evens/len(recent),2),
                   "Impair":round(100*odds/len(recent),2)}

    dozens = {"1-12":0,"13-24":0,"25-36":0}
    for x in recent:
        if 1<=x<=12: dozens["1-12"]+=1
        elif 13<=x<=24: dozens["13-24"]+=1
        elif 25<=x<=36: dozens["25-36"]+=1
    dozens = {k:round(100*v/len(recent),2) for k,v in dozens.items()}

    # score per number
    scores = algo_scores(history)
    total_score = sum(scores.values()) or 1
    sorted_nums = sorted(scores.items(), key=lambda x:-x[1])[:5]
    top5 = [(n, round(100*s/total_score,2)) for n,s in sorted_nums]

    return color_prob, pair_impair, dozens, top5

# ------------- UI ----------------------
st.title("🎲 Algo Roulette – Analyse en direct")

with st.form("numbers_form"):
    user_input = st.text_area("Entrez au moins 10 numéros (séparés par virgules, espaces ou tirets) :", height=100)
    go = st.form_submit_button("Calculer")

if go:
    numbers = list(map(int, re.findall(r"\d+", user_input)))
    if len(numbers) < 10:
        st.warning("Veuillez saisir au moins 10 numéros valides (0-36).")
    else:
        col_prob, par_prob, doz_prob, top5 = analyse(numbers)

        col1,col2,col3 = st.columns(3)
        col1.subheader("Couleur (%)")
        col1.dataframe(pd.DataFrame(col_prob.items(), columns=["Catégorie","Probabilité"]), hide_index=True, use_container_width=True)

        col2.subheader("Pair / Impair (%)")
        col2.dataframe(pd.DataFrame(par_prob.items(), columns=["Catégorie","Probabilité"]), hide_index=True, use_container_width=True)

        col3.subheader("Douzaines (%)")
        col3.dataframe(pd.DataFrame(doz_prob.items(), columns=["Catégorie","Probabilité"]), hide_index=True, use_container_width=True)

        st.markdown("### 🔢 Top 5 numéros")
        st.dataframe(pd.DataFrame(top5, columns=["Numéro","Probabilité (%)"]), hide_index=True, use_container_width=True)
