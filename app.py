import pandas as pd
import streamlit as st

st.title("Consulta ITBI")

@st.cache_data
def carregar_dados():
    url = "http://www.leandrofreitas.com/planilha2025.xlsx"
    
    df = pd.read_excel(url, sheet_name=None)
    df = pd.concat(df.values(), ignore_index=True)

    df["ENDERECO"] = df["Nome do Logradouro"].astype(str) + ", " + df["Número"].astype(str)
    df["VALOR"] = df["Valor de Transação (declarado pelo contribuinte)"]
    df["AREA"] = df["Área Construída (m2)"]
    df["PRECO_M2"] = df["VALOR"] / df["AREA"]

    return df

df = carregar_dados()

st.write(df.head())
