from datetime import date

import pandas as pd
import streamlit as st

from orcamento import db, importador

st.title("Tabelas de preço")
st.caption("Bases gratuitas: SINAPI (Caixa) e GOINFRA, mais a tabela própria da empresa.")

resumo = db.resumo_bases()
if not resumo.empty:
    st.subheader("Bases importadas")
    st.dataframe(resumo, hide_index=True, use_container_width=True)

aba1, aba2 = st.tabs(["Importar planilha", "Tabela própria"])
with aba1:
    st.markdown("Baixe a planilha no site oficial (SINAPI: caixa.gov.br/sinapi · GOINFRA: goinfra.go.gov.br) "
                "e envie aqui. Pode ser .xlsx, .xls ou .csv.")
    arq = st.file_uploader("Planilha de preços", type=["xlsx", "xls", "csv"])
    if arq:
        c1, c2, c3 = st.columns(3)
        fonte = c1.selectbox("Base", ["SINAPI", "GOINFRA", "PRÓPRIA"])
        uf = c2.text_input("UF", "GO")
        data_base = c3.text_input("Data-base (AAAA-MM)", date.today().strftime("%Y-%m"))
        c4, c5, c6 = st.columns(3)
        regime = c4.selectbox("Encargos", ["não desonerado", "desonerado", "—"])
        tipo = c5.selectbox("Tipo", ["composição", "insumo"])
        aba = c6.selectbox("Aba da planilha", importador.abas(arq))
        df = importador.ler(arq, aba)
        st.caption(f"{len(df)} linhas lidas. Confira as colunas sugeridas:")
        sug = importador.sugerir_colunas(list(df.columns), uf)
        cols = list(df.columns)
        m1, m2, m3, m4 = st.columns(4)
        mapa = {
            "codigo": m1.selectbox("Código", cols, index=cols.index(sug["codigo"]) if sug["codigo"] else 0),
            "descricao": m2.selectbox("Descrição", cols, index=cols.index(sug["descricao"]) if sug["descricao"] else 0),
            "unidade": m3.selectbox("Unidade", cols, index=cols.index(sug["unidade"]) if sug["unidade"] else 0),
            "preco": m4.selectbox("Preço / custo", cols, index=cols.index(sug["preco"]) if sug["preco"] else 0),
        }
        pronto = importador.preparar(df, mapa)
        st.dataframe(pronto.head(15), hide_index=True, use_container_width=True)
        st.caption(f"{len(pronto)} itens com código e preço válidos.")
        if st.button("Importar", type="primary", disabled=pronto.empty):
            n = db.importar_precos(pronto, fonte, uf.upper(), data_base, regime, tipo)
            st.success(f"{n} itens importados para {fonte} {uf.upper()} {data_base}.")
            st.rerun()

with aba2:
    st.markdown("Cadastre preços próprios (fornecedores, mão de obra por diária ou mês, serviços empreitados).")
    base = pd.DataFrame([{"codigo": "", "descricao": "", "unidade": "", "preco": 0.0}])
    editado = st.data_editor(base, num_rows="dynamic", use_container_width=True, hide_index=True,
                             column_config={"codigo": "Código", "descricao": "Descrição", "unidade": "Unidade",
                                            "preco": st.column_config.NumberColumn("Preço (R$)", format="%.2f")})
    data_base = st.text_input("Data-base", date.today().strftime("%Y-%m"), key="db_propria")
    if st.button("Salvar na tabela própria", type="primary"):
        validos = editado[(editado["codigo"].astype(str).str.strip() != "") & (editado["preco"] > 0)]
        n = db.importar_precos(validos, "PRÓPRIA", "GO", data_base, "—", "composição")
        st.success(f"{n} itens salvos na tabela própria.")
