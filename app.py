import streamlit as st

st.set_page_config(page_title="Allbra Orçamento", page_icon="🏗️", layout="wide")

paginas = [
    st.Page("paginas/inicio.py", title="Início", icon="🏠", default=True),
    st.Page("paginas/jogo.py", title="Novo orçamento", icon="🧩"),
    st.Page("paginas/resultado.py", title="Orçamento", icon="📊"),
    st.Page("paginas/vinculos.py", title="Vínculos de composições", icon="🔗"),
    st.Page("paginas/bases.py", title="Tabelas de preço", icon="📚"),
    st.Page("paginas/empresa.py", title="Empresa", icon="🏢"),
]
st.navigation(paginas).run()
