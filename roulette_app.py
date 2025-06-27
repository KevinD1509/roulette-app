
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
                st.rerun() if hasattr(st, "rerun") else st.experimental_rerun()
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

def analyse(spins):
    n=len(spins)
    weights=np.exp(-LAMBDA*np.arange(n)[::-1]); weights/=weights.sum()
    color,parity,dozen,num=Counter(),Counter(),Counter(),Counter()
    for i,num_val in enumerate(spins[::-1]):
        w=weights[i]
        if num_val==0:
            color["Vert"]+=w; parity["Zéro"]+=w; dozen["Zéro"]+=w
        else:
            color["Rouge" if num_val in RED else "Noir"]+=w
            parity["Pair" if num_val%2==0 else "Impair"]+=w
            dozen[str(1+(num_val-1)//12)]+=w
        num[num_val]+=w
    # run-length bonus
    def streak(seq,f):
        r=1
        for i in range(1,len(seq)):
            if f(seq[-i])==f(seq[-i-1]): r+=1
            else: break
        return r
    col=lambda x: "Vert" if x==0 else ("Rouge" if x in RED else "Noir")
    color[col(spins[-1])]*=1+0.04*streak(spins,col)**2
    # neighbour bonus
    neigh=Counter()
    for v in spins[-5:]:
        idx=POS[v]
        for k in (-2,-1,0,1,2):
            neigh[WHEEL[(idx+k)%37]]+=np.exp(-(k*k)/8)
    denom=max(neigh.values()) or 1
    scores={n:num[n]+0.4*(neigh[n]/denom) for n in range(37)}
    tot_score=sum(scores.values()) or 1
    top5=sorted(scores.items(),key=lambda x:-x[1])[:5]
    top5_prob=[(n,round(s/tot_score*100,2)) for n,s in top5]
    # Normalize categories
    for d in (color,parity,dozen):
        s=sum(d.values()) or 1
        for k in d: d[k]=round(100*d[k]/s,2)
    dozen_read={}
    for k,v in dozen.items():
        dozen_read["Zéro" if k=="Zéro" else ("1-12" if k=="1" else "13-24" if k=="2" else "25-36" if k=="3" else k)]=v
    return color,parity,dozen_read,top5_prob

st.title("🎯 Algo Roulette – Prédictions")

with st.form("input_form"):
    user_text=st.text_area("Entrez les numéros (≥10) séparés par virgules, espaces ou tirets",height=120)
    submitted=st.form_submit_button("Calculer")

if submitted:
    spins=list(map(int,re.findall(r"\d+",user_text)))
    if len(spins)<10 or any(n>36 for n in spins):
        st.warning("Veuillez entrer au moins 10 numéros compris entre 0 et 36.")
    else:
        color_p,parity_p,dozen_p,top5=analyse(spins)
        # sort dicts
        color_df=pd.DataFrame(sorted(color_p.items(), key=lambda x:-x[1]),columns=["Catégorie","Probabilité (%)"])
        parity_df=pd.DataFrame(sorted(parity_p.items(), key=lambda x:-x[1]),columns=["Catégorie","Probabilité (%)"])
        dozen_df=pd.DataFrame(sorted(dozen_p.items(), key=lambda x:-x[1]),columns=["Catégorie","Probabilité (%)"])
        col1,col2,col3=st.columns(3)
        col1.subheader("Couleur (%)"); col1.dataframe(color_df,hide_index=True,use_container_width=True)
        col2.subheader("Pair / Impair (%)"); col2.dataframe(parity_df,hide_index=True,use_container_width=True)
        col3.subheader("Douzaines (%)"); col3.dataframe(dozen_df,hide_index=True,use_container_width=True)
        st.markdown("### 🔢 Top 5 numéros")
        top_df=pd.DataFrame({"Numéro":[str(n) for n,_ in top5],"Probabilité (%)":[p for _,p in top5]})
        st.dataframe(top_df,hide_index=True,use_container_width=True)
        # Top probas block
        bests={
            "Couleur":color_df.iloc[0]["Probabilité (%)"],
            "Pair/Impair":parity_df.iloc[0]["Probabilité (%)"],
            "Douzaine":dozen_df.iloc[0]["Probabilité (%)"],
            "Numéro":top_df.iloc[0]["Probabilité (%)"]
        }
        max_val=max(bests.values())
        st.markdown("### ⭐ Top probas")
        best_df=pd.DataFrame(
            {"Catégorie":bests.keys(),"Probabilité (%)":[round(v,2) for v in bests.values()]}
        ).sort_values("Probabilité (%)",ascending=False,ignore_index=True)
        def highlight(row):
            return ["background-color:#FFD54F" if row["Probabilité (%)"]==max_val else "" for _ in row]
        st.dataframe(best_df.style.apply(highlight,axis=1),hide_index=True,use_container_width=True)
