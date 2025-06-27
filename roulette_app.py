
import streamlit as st
import pandas as pd
import numpy as np
import re
from collections import Counter

PASSWORD = "1928"

# -------- Authentication ----------
if "auth_ok" not in st.session_state:
    st.session_state["auth_ok"] = False

if not st.session_state["auth_ok"]:
    st.markdown("## 🔒 Accès Sécurisé")
    with st.form("login_form"):
        pw = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("Accéder"):
            if pw == PASSWORD:
                st.session_state['auth_ok'] = True
                st.rerun() if hasattr(st,'rerun') else st.experimental_rerun()
            else:
                st.error("Mot de passe incorrect.")
    st.stop()

# -------- Constants ----------
RED   = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}
WHEEL = [0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,
         10,5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26]
POS   = {n:i for i,n in enumerate(WHEEL)}
LAMBDA = 0.12

# -------- Algo Roulette Def ----------
def analyse(spins):
    n=len(spins)
    w=np.exp(-LAMBDA*np.arange(n)[::-1]); w/=w.sum()

    color=Counter(); parity=Counter(); dozen=Counter(); num=Counter()
    for i,x in enumerate(spins[::-1]):  # oldest→newest
        weight=w[i]
        if x==0:
            color["Vert"]+=weight; parity["Zéro"]+=weight; dozen["Zéro"]+=weight
        else:
            color["Rouge" if x in RED else "Noir"] += weight
            parity["Pair" if x%2==0 else "Impair"] += weight
            dozen[str(1+(x-1)//12)] += weight
        num[x]+=weight

    # run length bonus on color
    def col(n): return "Vert" if n==0 else ("Rouge" if n in RED else "Noir")
    run=1
    for i in range(1,len(spins)):
        if col(spins[-i])==col(spins[-i-1]): run+=1
        else: break
    color[col(spins[-1])] *= 1 + 0.04*run**2

    # neighbour bonus
    nb=Counter()
    for x in spins[-5:]:
        idx=POS[x]
        for k in (-2,-1,0,1,2):
            nb[ WHEEL[(idx+k)%37] ] += np.exp(-(k*k)/8)
    denom=max(nb.values()) or 1

    scores={}
    for n_,v in num.items():
        scores[n_] = v + 0.4*(nb[n_]/denom)
    total_score=sum(scores.values()) or 1
    top5 = sorted(scores.items(), key=lambda x:-x[1])[:5]
    top5=[(n_, round(s/total_score*100,2)) for n_,s in top5]

    # normalize percentages
    for d in (color, parity, dozen):
        s=sum(d.values()) or 1
        for k in d: d[k]=round(100*d[k]/s,2)

    dozen_read={}
    for k,v in dozen.items():
        if k=="Zéro": dozen_read["Zéro"]=v
        elif k=="1": dozen_read["1-12"]=v
        elif k=="2": dozen_read["13-24"]=v
        elif k=="3": dozen_read["25-36"]=v

    return color, parity, dozen_read, top5

# -------- UI ----------
st.title("🎯 Algo Roulette – Prédictions")

with st.form("input_form"):
    raw = st.text_area("Entrez les numéros (≥10) séparés par virgules, espaces ou tirets", height=120)
    calc = st.form_submit_button("Calculer")

if calc:
    spins = list(map(int, re.findall(r"\d+", raw)))
    if len(spins)<10 or any(x>36 for x in spins):
        st.warning("Veuillez entrer au moins 10 numéros compris entre 0 et 36.")
    else:
        color_p, parity_p, dozen_p, top5 = analyse(spins)

        c1,c2,c3 = st.columns(3)
        c1.subheader("Couleur (%)")
        c1.dataframe(pd.DataFrame(color_p.items(), columns=["Catégorie","Probabilité (%)"]), hide_index=True)
        c2.subheader("Pair / Impair (%)")
        c2.dataframe(pd.DataFrame(parity_p.items(), columns=["Catégorie","Probabilité (%)"]), hide_index=True)
        c3.subheader("Douzaines (%)")
        c3.dataframe(pd.DataFrame(dozen_p.items(), columns=["Catégorie","Probabilité (%)"]), hide_index=True)

        st.markdown("### 🔢 Top 5 numéros")
        df_top=pd.DataFrame({"Numéro":[str(n) for n,_ in top5], "Probabilité (%)":[p for _,p in top5]})
        st.dataframe(df_top, hide_index=True)

        # ----- Best odds block -----
        st.markdown("### ⭐ Meilleures probas")
        bests=[]
        bests.append(("Couleur", max(color_p, key=color_p.get), color_p[max(color_p,key=color_p.get)]))
        bests.append(("Pair/Impair", max(parity_p, key=parity_p.get), parity_p[max(parity_p,key=parity_p.get)]))
        bests.append(("Douzaine", max(dozen_p, key=dozen_p.get), dozen_p[max(dozen_p,key=dozen_p.get)]))
        bests.append(("Numéro seul", str(top5[0][0]), top5[0][1]))

        best_value = max(v for _,_,v in bests)
        table=pd.DataFrame(bests, columns=["Catégorie","Valeur","Probabilité (%)"])
        def highlight(row):
            return ['background-color: #ffe599' if row["Probabilité (%)"]==best_value else '' for _ in row]
        st.dataframe(table.style.apply(highlight, axis=1), hide_index=True)
