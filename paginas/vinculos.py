import streamlit as st

from orcamento import db

st.title("Vínculos de composições")
st.caption("Ligue cada serviço do orçamento a uma composição ou insumo das tabelas importadas. "
           "O vínculo fica salvo e vale para todos os orçamentos.")

servicos = st.session_state.get("ultimo_orcamento")
if not servicos:
    st.info("Gere um orçamento primeiro (Novo orçamento → Gerar orçamento) para listar os serviços.")
    st.stop()
if db.resumo_bases().empty:
    st.warning("Nenhuma tabela de preço importada ainda. Importe em **Tabelas de preço**.")

vinc = db.vinculos()
so_pendentes = st.toggle("Mostrar só serviços sem vínculo", value=True)
fontes = ["(todas)"] + sorted(db.resumo_bases()["fonte"].unique().tolist())
for s in servicos:
    if so_pendentes and s["servico"] in vinc:
        continue
    atual = vinc.get(s["servico"])
    titulo = f"{'✅' if atual else '▫️'} {s['descricao']} ({s['unidade']})"
    with st.expander(titulo):
        if atual:
            st.write(f"Vinculado a **{atual[0]} {atual[1]}**")
            if st.button("Remover vínculo", key=f"rm_{s['servico']}"):
                db.remover_vinculo(s["servico"])
                st.rerun()
        c1, c2 = st.columns([3, 1])
        termo = c1.text_input("Buscar na tabela (palavras ou código)", " ".join(s["descricao"].split(" (")[0].split()[:3]),
                              key=f"busca_{s['servico']}")
        fonte = c2.selectbox("Base", fontes, key=f"fonte_{s['servico']}")
        res = db.buscar_precos(termo, None if fonte == "(todas)" else fonte)
        if res.empty:
            st.caption("Nada encontrado. Tente menos palavras ou o código.")
            continue
        res = res.drop_duplicates(subset=["fonte", "codigo"])
        opcoes = list(range(len(res)))
        sel = st.radio("Resultados", opcoes, key=f"res_{s['servico']}", label_visibility="collapsed",
                       format_func=lambda i: f"{res.iloc[i]['fonte']} {res.iloc[i]['codigo']} · "
                                             f"{res.iloc[i]['descricao'][:110]} · {res.iloc[i]['unidade']} · "
                                             f"R$ {res.iloc[i]['preco']:.2f}")
        if res.iloc[sel]["unidade"].strip().upper().replace("2", "²").replace("3", "³") != s["unidade"].upper():
            st.caption(f"Atenção: unidade da composição ({res.iloc[sel]['unidade']}) diferente da do serviço ({s['unidade']}).")
        if st.button("Vincular", key=f"ok_{s['servico']}", type="primary"):
            db.salvar_vinculo(s["servico"], res.iloc[sel]["fonte"], res.iloc[sel]["codigo"])
            st.rerun()
