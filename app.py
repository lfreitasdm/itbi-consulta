
import pandas as pd
import streamlit as st

# =========================
# CONFIGURAÇÃO
# =========================
st.set_page_config(layout="wide")
st.title("📊 Consulta de Transações ITBI")

# =========================
# CARREGAR DADOS
# =========================
@st.cache_data(ttl=3600)
def carregar_dados():
    try:
        url = "http://www.leandrofreitas.com/planilha2025.csv"

        # 🔥 Leitura robusta para CSV brasileiro
        df = pd.read_csv(
            url,
            sep=";",                # separador padrão BR
            encoding="utf-8",
            on_bad_lines="skip",   # ignora linhas com erro
            low_memory=False
        )

        # =========================
        # TRATAMENTO DE DADOS
        # =========================

        # Converter colunas numéricas
        df["AREA"] = pd.to_numeric(df["Área Construída (m2)"], errors="coerce")
        df["VALOR"] = pd.to_numeric(df["Valor de Transação (declarado pelo contribuinte)"], errors="coerce")

        # Criar endereço completo
        df["ENDERECO"] = df["Nome do Logradouro"].astype(str) + ", " + df["Número"].astype(str)

        # 🔥 Evitar divisão por zero
        df["PRECO_M2"] = df["VALOR"] / df["AREA"]
        df["PRECO_M2"] = df["PRECO_M2"].replace([float("inf"), -float("inf")], None)

        return df

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# =========================
# EXECUÇÃO
# =========================
df = carregar_dados()

if df.empty:
    st.warning("Nenhum dado carregado.")
    st.stop()

# =========================
# FILTROS
# =========================
st.sidebar.header("🔎 Filtros")

busca = st.sidebar.text_input("Endereço ou rua")
bairro = st.sidebar.text_input("Bairro")

valor_min = st.sidebar.number_input("Valor mínimo", value=0)
valor_max = st.sidebar.number_input("Valor máximo", value=10000000)

area_min = st.sidebar.number_input("Área mínima", value=0)
area_max = st.sidebar.number_input("Área máxima", value=1000)

# Tipo de imóvel (se existir)
if "Descrição do uso (IPTU)" in df.columns:
    tipos = ["Todos"] + sorted(df["Descrição do uso (IPTU)"].dropna().unique())
else:
    tipos = ["Todos"]

tipo = st.sidebar.selectbox("Tipo de imóvel", tipos)

# =========================
# APLICAR FILTROS
# =========================
df_filtrado = df.copy()

if busca:
    df_filtrado = df_filtrado[
        df_filtrado["ENDERECO"].str.contains(busca, case=False, na=False)
    ]

if bairro and "Bairro" in df.columns:
    df_filtrado = df_filtrado[
        df_filtrado["Bairro"].str.contains(bairro, case=False, na=False)
    ]

df_filtrado = df_filtrado[
    (df_filtrado["VALOR"] >= valor_min) &
    (df_filtrado["VALOR"] <= valor_max)
]

df_filtrado = df_filtrado[
    (df_filtrado["AREA"] >= area_min) &
    (df_filtrado["AREA"] <= area_max)
]

if tipo != "Todos" and "Descrição do uso (IPTU)" in df.columns:
    df_filtrado = df_filtrado[
        df_filtrado["Descrição do uso (IPTU)"] == tipo
    ]

# =========================
# RESULTADOS
# =========================
st.subheader("📋 Resultados")

st.write(f"Total encontrado: {len(df_filtrado)} registros")

colunas = [
    "Data de Transação" if "Data de Transação" in df.columns else None,
    "ENDERECO",
    "Bairro" if "Bairro" in df.columns else None,
    "VALOR",
    "AREA",
    "PRECO_M2"
]

colunas = [c for c in colunas if c is not None]

st.dataframe(
    df_filtrado[colunas].sort_values(by="VALOR", ascending=False),
    use_container_width=True
)
