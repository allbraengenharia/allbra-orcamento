import streamlit as st

from orcamento import db

emp = db.empresa()
st.title("Allbra Orçamento")
st.caption(f"{emp['razao_social']} · CNPJ {emp['cnpj']} · {emp['cidade']}/{emp['uf']}")

st.markdown(
    """
Programa de orçamento de obras guiado por perguntas de seleção.

**Como usar nesta versão (fase 0):**
1. Em **Tabelas de preço**, importe a planilha do SINAPI-GO e/ou da GOINFRA (ou cadastre sua tabela própria).
2. Em **Novo orçamento**, responda o jogo de seleção da residência térrea / MCMV.
3. Em **Orçamento**, veja os quantitativos, a origem de cada número e o resumo por etapa.
4. Em **Vínculos de composições**, ligue cada serviço a uma composição da tabela. O vínculo fica salvo e vale para os próximos orçamentos.
"""
)

bases = db.resumo_bases()
c1, c2, c3 = st.columns(3)
c1.metric("Itens de preço importados", int(bases["itens"].sum()) if not bases.empty else 0)
c2.metric("Serviços vinculados", len(db.vinculos()))
c3.metric("Orçamentos salvos", len(db.listar_orcamentos()))

orcs = db.listar_orcamentos()
if not orcs.empty:
    st.subheader("Orçamentos salvos")
    escolha = st.selectbox("Abrir orçamento", orcs["id"], format_func=lambda i: f"#{i} · {orcs.set_index('id').loc[i, 'nome']}")
    if st.button("Abrir"):
        dados = db.carregar_orcamento(int(escolha))
        st.session_state.update(escolhas=dados["escolhas"], valores=dados["valores"], outros=dados.get("outros", {}),
                                nome_obra=dados.get("nome_obra", ""), orcamento_id=int(escolha), passo=0)
        st.switch_page("paginas/resultado.py")
