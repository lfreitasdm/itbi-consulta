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

        df = pd.read_csv(
            url,
            sep=";",                # CSV brasileiro
            encoding="utf-8",
            on_bad_lines="skip",
            low_memory=False
        )

        # =========================
        # PADRONIZAR COLUNAS
        # =========================
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

        # =========================
        # TRATAMENTO DE DADOS
        # =========================
# =========================
# LIMPEZA DE NÚMEROS (BR)
# =========================

def limpar_numero(coluna):
    return (
        coluna.astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )

# Aplicar limpeza
df["VALOR"] = pd.to_numeric(limpar_numero(df.get("VALOR")), errors="coerce")
df["AREA"] = pd.to_numeric(limpar_numero(df.get("AREA")), errors="coerce")

        df["ENDERECO"] = df.get("LOGRADOURO", "").astype(str) + ", " + df.get("NUMERO", "").astype(str)

        # Evitar divisão por zero
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

# Tipo de imóvel
if "TIPO" in df.columns:
    tipos = ["Todos"] + sorted(df["TIPO"].dropna().unique())
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

if bairro and "BAIRRO" in df.columns:
    df_filtrado = df_filtrado[
        df_filtrado["BAIRRO"].str.contains(bairro, case=False, na=False)
    ]

df_filtrado = df_filtrado[
    (df_filtrado["VALOR"].fillna(0) >= valor_min) &
    (df_filtrado["VALOR"].fillna(0) <= valor_max)
]

df_filtrado = df_filtrado[
    (df_filtrado["AREA"].fillna(0) >= area_min) &
    (df_filtrado["AREA"].fillna(0) <= area_max)
]

if tipo != "Todos" and "TIPO" in df.columns:
    df_filtrado = df_filtrado[
        df_filtrado["TIPO"] == tipo
    ]

# =========================
# RESULTADOS
# =========================
st.subheader("📋 Resultados")

st.write(f"Total encontrado: {len(df_filtrado)} registros")

colunas = [
    "DATA" if "DATA" in df.columns else None,
    "ENDERECO",
    "BAIRRO" if "BAIRRO" in df.columns else None,
    "VALOR",
    "AREA",
    "PRECO_M2"
]

colunas = [c for c in colunas if c is not None]

st.dataframe(
    df_filtrado[colunas].sort_values(by="VALOR", ascending=False),
    use_container_width=True
)
