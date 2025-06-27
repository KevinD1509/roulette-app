
import streamlit as st
import pandas as pd
import re
from collections import Counter

PASSWORD = "1928"

# -------- Authentication ----------
if "auth_ok" not in st.session_state or not st.session_state.get("auth_ok"):
    st.markdown("## 🔒 Accès Sécurisé")
    with st.form("login"):
        pw = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Accéder")
        if submit:
            if pw == PASSWORD:
                st.session_state["auth_ok"] = True
                # force clean page after login
                if hasattr(st, "rerun"):
                    st.rerun()
                elif hasattr(st, "experimental_rerun"):
                    st.experimental_rerun()
            else:
                st.error("Mot de passe incorrect.")
    st.stop()

# ---------- Constants -------------
RED   = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}

def analyse(history):
    recent = history[-30:] if len(history) >= 30 else history
    total  = len(recent)
    color_prob = {
        "Rouge": round(100*sum(x in RED for x in recent)/total,2),
        "Noir":  round(100*sum(x in BLACK for x in recent)/total,2),
        "Vert":  round(100*recent.count(0)/total,2)
    }
    parity_prob = {
        "Pair":   round(100*sum(x!=0 and x%2==0 for x in recent)/total,2),
        "Impair": round(100*sum(x%2==1 for x in recent)/total,2)
    }
    dozens = {"1-12":0,"13-24":0,"25-36":0}
    for x in recent:
        if 1<=x<=12: dozens["1-12"]+=1
        elif 13<=x<=24: dozens["13-24"]+=1
        elif 25<=x<=36: dozens["25-36"]+=1
    dozens = {k:round(100*v/total,2) for k,v in dozens.items()}
    freq = Counter(recent)
    top5 = [(n, round(c/total*100,2)) for n,c in freq.most_common(5)]
    return color_prob, parity_prob, dozens, top5

# ---------- UI ----------
st.title("🎯 Algo Roulette – Prédictions")

with st.form("input"):
    user_numbers = st.text_area("Entrez les numéros (≥10) séparés par virgules, espaces ou tirets", height=120)
    ok = st.form_submit_button("Calculer")

if ok:
    nums = list(map(int, re.findall(r"\d+", user_numbers)))
    if len(nums) < 10 or any(n > 36 for n in nums):
        st.warning("Veuillez entrer au moins 10 numéros compris entre 0 et 36.")
    else:
        color_prob, parity_prob, dozens_prob, top5 = analyse(nums)

        col1,col2,col3 = st.columns(3)

        col1.subheader("Couleur (%)")
        col1.dataframe(pd.DataFrame(color_prob.items(), columns=["Catégorie","Probabilité (%)"]), hide_index=True)

        col2.subheader("Pair / Impair (%)")
        col2.dataframe(pd.DataFrame(parity_prob.items(), columns=["Catégorie","Probabilité (%)"]), hide_index=True)

        col3.subheader("Douzaines (%)")
        col3.dataframe(pd.DataFrame(dozens_prob.items(), columns=["Catégorie","Probabilité (%)"]), hide_index=True)

        st.markdown("### 🔢 Top 5 numéros")
        df_top = pd.DataFrame({"Numéro":[str(n) for n,_ in top5], "Probabilité (%)":[p for _,p in top5]})
        st.dataframe(df_top, hide_index=True)
