
import streamlit as st
import pandas as pd
import numpy as np
import re
from collections import Counter

PASSWORD = "1928"

# ---------- Authentication ----------
if "auth_ok" not in st.session_state:
    st.session_state["auth_ok"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "main"

def login_page():
    st.markdown("## 🔒 Accès Sécurisé")
    with st.form("login_form"):
        pw = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("Accéder"):
            if pw == PASSWORD:
                st.session_state["auth_ok"] = True
                st.experimental_rerun()
            else:
                st.error("Mot de passe incorrect.")

if not st.session_state["auth_ok"]:
    login_page()
    st.stop()

# ---------- Constants ----------
RED   = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}

# ---------- Algo Roulette Def ----------
import math
LAMBDA = 0.12
WHEEL  = [0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,
          10,5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26]
POS    = {n:i for i,n in enumerate(WHEEL)}

def analyse(spins):
    n=len(spins)
    w=np.exp(-LAMBDA*np.arange(n)[::-1]); w/=w.sum()
    color=Counter(); par=Counter(); doz=Counter(); num=Counter()
    for i,x in enumerate(spins[::-1]):  # oldest→newest
        weight=w[i]
        if x==0: color["Vert"]+=weight; par["Zéro"]+=weight; doz["Zéro"]+=weight
        else:
            color["Rouge" if x in RED else "Noir"]+=weight
            par["Pair" if x%2==0 else "Impair"]+=weight
            doz[str(1+(x-1)//12)]+=weight
        num[x]+=weight
    # neighbour bonus
    nb=Counter()
    for x in spins[-5:]:
        idx=POS[x]
        for k in (-2,-1,0,1,2):
            nb[WHEEL[(idx+k)%37]]+=math.exp(-(k*k)/8)
    denom=max(nb.values()) or 1
    total_score=0
    scores={}
    for n_,v in num.items():
        s=v+0.4*(nb[n_]/denom)
        scores[n_]=s
        total_score+=s
    top5=sorted(scores.items(), key=lambda x:-x[1])[:5]
    top5=[(n_, round(s/total_score*100,2)) for n_,s in top5]
    # normalize
    for d in (color,par,doz):
        s=sum(d.values()) or 1
        for k in d: d[k]=round(100*d[k]/s,2)
    doz_read={}
    for k,v in doz.items():
        if k=="Zéro": doz_read["Zéro"]=v
        elif k=="1": doz_read["1-12"]=v
        elif k=="2": doz_read["13-24"]=v
        elif k=="3": doz_read["25-36"]=v
    return color,par,doz_read,top5

# ---------- Graph trend helper ----------
def trend_data(spins):
    if len(spins)<2: return None
    color_series=[]; parity_series=[]; dozen_series=[]
    colors=["Rouge","Noir","Vert"]; parities=["Pair","Impair"]; dozens=["1-12","13-24","25-36"]
    for i in range(2,len(spins)+1):
        sub=spins[:i]
        c,p,d,_=analyse(sub)
        color_series.append([i]+[c.get(cname,0) for cname in colors])
        parity_series.append([i]+[p.get(pn,0) for pn in parities])
        dozen_series.append([i]+[d.get(dn,0) for dn in dozens])
    color_df=pd.DataFrame(color_series, columns=["Index"]+colors).set_index("Index")
    parity_df=pd.DataFrame(parity_series, columns=["Index"]+parities).set_index("Index")
    dozen_df=pd.DataFrame(dozen_series, columns=["Index"]+dozens).set_index("Index")
    return color_df, parity_df, dozen_df

# ---------- Switch pages ----------
if st.session_state["page"]=="graph":
    # need stored spins history
    spins_str=st.session_state.get("spins_raw","")
    spins=list(map(int,re.findall(r"\d+", spins_str))) if spins_str else []
    st.button("← Retour", on_click=lambda: st.session_state.update(page="main"))
    st.markdown("## 📈 Graphique de tendances")
    if len(spins)<10:
        st.info("Entrez au moins 10 numéros puis appuyez sur Calculer pour voir le graphique.")
    else:
        color_df, parity_df, dozen_df=trend_data(spins)
        st.subheader("Tendance Couleurs")
        st.line_chart(color_df)
        st.subheader("Tendance Pair / Impair")
        st.line_chart(parity_df)
        st.subheader("Tendance Douzaines")
        st.line_chart(dozen_df)
    st.stop()

# ---------- Main Page ----------
st.title("🎯 Algo Roulette – Prédictions")
with st.form("input_form"):
    user_numbers = st.text_area("Entrez les numéros (≥10) séparés par virgules, espaces ou tirets", height=120, value=st.session_state.get("spins_raw",""))
    submitted=st.form_submit_button("Calculer")
    st.session_state["spins_raw"]=user_numbers

if submitted:
    spins = list(map(int, re.findall(r"\d+", st.session_state["spins_raw"])))
    if len(spins)<10 or any(n>36 for n in spins):
        st.warning("Veuillez entrer au moins 10 numéros compris entre 0 et 36.")
    else:
        color_prob, parity_prob, dozen_prob, top5 = analyse(spins)

        col1,col2,col3 = st.columns(3)
        col1.subheader("Couleur (%)")
        col1.dataframe(pd.DataFrame(color_prob.items(), columns=["Catégorie","Probabilité (%)"]), hide_index=True)
        col2.subheader("Pair / Impair (%)")
        col2.dataframe(pd.DataFrame(parity_prob.items(), columns=["Catégorie","Probabilité (%)"]), hide_index=True)
        col3.subheader("Douzaines (%)")
        col3.dataframe(pd.DataFrame(dozen_prob.items(), columns=["Catégorie","Probabilité (%)"]), hide_index=True)

        st.markdown("### 🔢 Top 5 numéros")
        df_top=pd.DataFrame({"Numéro":[str(n) for n,_ in top5], "Probabilité (%)":[p for _,p in top5]})
        st.dataframe(df_top, hide_index=True)

st.button("📈 Graphique", on_click=lambda: st.session_state.update(page="graph"))
