import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")
st.title("📊 Consulta Inteligente ITBI")

# =========================
# LIMPEZA NUMÉRICA
# =========================
def limpar_numero(coluna):
    return (
        coluna.astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )

# =========================
# CARREGAR DADOS
# =========================
@st.cache_data(ttl=3600)
def carregar_dados():
    url = "http://www.leandrofreitas.com/planilha2025.csv"

    df = pd.read_csv(url, sep=";", encoding="utf-8", on_bad_lines="skip", low_memory=False)

    df.columns = df.columns.str.strip()

    df.rename(columns={
        "Área Construída (m2)": "AREA",
        "Área Construída (m²)": "AREA",
        "Valor de Transação (declarado pelo contribuinte)": "VALOR",
        "Nome do Logradouro": "LOGRADOURO",
        "Número": "NUMERO",
        "Bairro": "BAIRRO",
        "Data de Transação": "DATA",
        "Descrição do uso (IPTU)": "TIPO"
    }, inplace=True)

    df["VALOR"] = pd.to_numeric(limpar_numero(df["VALOR"]), errors="coerce")
    df["AREA"] = pd.to_numeric(limpar_numero(df["AREA"]), errors="coerce")

    df["ENDERECO"] = df["LOGRADOURO"].astype(str) + ", " + df["NUMERO"].astype(str)

    df["PRECO_M2"] = df["VALOR"] / df["AREA"]
    df["PRECO_M2"] = df["PRECO_M2"].replace([float("inf"), -float("inf")], None)

    return df

df = carregar_dados()

# =========================
# FILTROS
# =========================
st.sidebar.header("🔎 Filtros")

bairro = st.sidebar.text_input("Bairro")

df_filtrado = df.copy()

if bairro:
    df_filtrado = df_filtrado[df_filtrado["BAIRRO"].str.contains(bairro, case=False, na=False)]

# =========================
# 📊 MÉTRICAS
# =========================
st.subheader("📊 Indicadores de Mercado")

col1, col2, col3, col4 = st.columns(4)

media_valor = df_filtrado["VALOR"].mean()
mediana_valor = df_filtrado["VALOR"].median()
media_m2 = df_filtrado["PRECO_M2"].mean()
total = len(df_filtrado)

col1.metric("💰 Média", f"R$ {media_valor:,.0f}")
col2.metric("📉 Mediana", f"R$ {mediana_valor:,.0f}")
col3.metric("📐 Média m²", f"R$ {media_m2:,.0f}")
col4.metric("📊 Total vendas", total)

# =========================
# 📍 ANÁLISE POR BAIRRO
# =========================
st.subheader("📍 Ranking de Bairros")

ranking = (
    df.groupby("BAIRRO")["PRECO_M2"]
    .mean()
    .sort_values(ascending=False)
    .head(10)
)

st.bar_chart(ranking)

# =========================
# 🧠 COMPARADOR DE IMÓVEL
# =========================
st.subheader("🧠 Comparar Imóvel")

col1, col2 = st.columns(2)

valor_input = col1.number_input("Valor do imóvel", value=500000)
area_input = col2.number_input("Área do imóvel", value=50)

if area_input > 0:
    preco_m2_input = valor_input / area_input
    media_mercado = df_filtrado["PRECO_M2"].mean()

    st.write(f"Preço/m² do imóvel: R$ {preco_m2_input:,.0f}")
    st.write(f"Média da região: R$ {media_mercado:,.0f}")

    if preco_m2_input < media_mercado * 0.9:
        st.success("🟢 Abaixo do mercado (boa oportunidade)")
    elif preco_m2_input > media_mercado * 1.1:
        st.error("🔴 Acima do mercado")
    else:
        st.warning("🟡 Dentro da média")

# =========================
# 📋 TABELA
# =========================
st.subheader("📋 Dados")

st.dataframe(df_filtrado.head(200), use_container_width=True)
