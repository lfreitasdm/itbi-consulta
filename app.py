import pandas as pd
import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import tempfile

# =========================
# CONFIGURAÇÃO
# =========================
st.set_page_config(layout="wide")
st.title("📊 Consulta Inteligente ITBI + Laudo")

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

    df = pd.read_csv(
        url,
        sep=";",
        encoding="utf-8",
        on_bad_lines="skip",
        low_memory=False
    )

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

# =========================
# GERAR LAUDO TEXTO
# =========================
def gerar_laudo(df_filtrado, valor_input=None, area_input=None):
    media = df_filtrado["PRECO_M2"].mean()
    mediana = df_filtrado["PRECO_M2"].median()
    total = len(df_filtrado)

    texto = f"""
Estudo de Mercado Imobiliário

Foram analisadas {total} transações reais registradas via ITBI.

O valor médio do metro quadrado na região é de R$ {media:,.0f},
enquanto a mediana está em R$ {mediana:,.0f}.
"""

    if valor_input and area_input and area_input > 0:
        preco_m2 = valor_input / area_input

        if preco_m2 < media * 0.9:
            texto += "\nO imóvel está abaixo do valor médio de mercado, indicando potencial de valorização."
        elif preco_m2 > media * 1.1:
            texto += "\nO imóvel está acima da média da região, podendo ter maior tempo de venda."
        else:
            texto += "\nO imóvel está dentro da média praticada na região."

    return texto

# =========================
# GERAR PDF
# =========================
def gerar_pdf(texto):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    doc = SimpleDocTemplate(temp_file.name)
    styles = getSampleStyleSheet()

    content = []

    for linha in texto.split("\n"):
        content.append(Paragraph(linha, styles["Normal"]))
        content.append(Spacer(1, 10))

    doc.build(content)

    return temp_file.name

# =========================
# EXECUÇÃO
# =========================
df = carregar_dados()

# =========================
# FILTROS
# =========================
st.sidebar.header("🔎 Filtros")

bairro = st.sidebar.text_input("Bairro")

df_filtrado = df.copy()

if bairro:
    df_filtrado = df_filtrado[
        df_filtrado["BAIRRO"].str.contains(bairro, case=False, na=False)
    ]

# =========================
# MÉTRICAS
# =========================
st.subheader("📊 Indicadores de Mercado")

col1, col2, col3, col4 = st.columns(4)

col1.metric("💰 Média", f"R$ {df_filtrado['VALOR'].mean():,.0f}")
col2.metric("📉 Mediana", f"R$ {df_filtrado['VALOR'].median():,.0f}")
col3.metric("📐 Média m²", f"R$ {df_filtrado['PRECO_M2'].mean():,.0f}")
col4.metric("📊 Total vendas", len(df_filtrado))

# =========================
# RANKING
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
# COMPARADOR
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
        st.success("🟢 Abaixo do mercado")
    elif preco_m2_input > media_mercado * 1.1:
        st.error("🔴 Acima do mercado")
    else:
        st.warning("🟡 Dentro da média")

# =========================
# LAUDO + PDF
# =========================
st.subheader("📄 Gerar Laudo de Mercado")

if st.button("Gerar Laudo"):
    laudo = gerar_laudo(df_filtrado, valor_input, area_input)

    st.text_area("Laudo gerado:", laudo, height=300)

    pdf_path = gerar_pdf(laudo)

    with open(pdf_path, "rb") as f:
        st.download_button(
            "📥 Baixar PDF",
            f,
            file_name="laudo_mercado.pdf"
        )

# =========================
# TABELA
# =========================
st.subheader("📋 Dados")

st.dataframe(df_filtrado.head(200), use_container_width=True)
