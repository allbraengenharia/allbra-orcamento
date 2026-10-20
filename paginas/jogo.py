import streamlit as st

from orcamento import arvore as arv

arvore = arv.carregar()
ss = st.session_state
ss.setdefault("escolhas", {})
ss.setdefault("valores", {})
ss.setdefault("outros", {})
ss.setdefault("passo", 0)
ss.setdefault("nome_obra", "")

st.title("Novo orçamento")

with st.expander("Dados da obra e planta baixa", expanded=ss["passo"] == 0):
    c1, c2 = st.columns(2)
    ss["nome_obra"] = c1.text_input("Nome da obra", ss["nome_obra"], placeholder="Ex.: Residência João - Lote 12")
    ss["escolhas"]["municipio"] = c2.text_input("Município da obra", ss["escolhas"].get("municipio", "Aparecida de Goiânia"))
    c3, c4 = st.columns(2)
    tipologias = ["Residencial", "Comercial (em breve)", "Industrial (em breve)", "Hospitalar (em breve)"]
    c3.selectbox("Tipologia", tipologias, index=0, disabled=True,
                 help="Nesta fase está disponível a tipologia residencial. As demais entram nas próximas fases.")
    subs = arvore["ativas"]
    atual = ss["escolhas"].get("subtipologia", subs[0])
    ss["escolhas"]["subtipologia"] = c4.selectbox("Subtipologia", subs, index=subs.index(atual) if atual in subs else 0)
    pdf = st.file_uploader("Planta baixa (PDF)", type=["pdf"],
                           help="A leitura automática pela IA entra na fase 4. Por enquanto o PDF serve de referência.")
    if pdf:
        ss["pdf_nome"] = pdf.name
        st.caption(f"Arquivo recebido: {pdf.name}. Confira as medidas nas perguntas seguintes.")

visiveis = [p for p in arvore["perguntas"] if arv.visivel(p, ss["escolhas"])]
ss["passo"] = min(ss["passo"], len(visiveis) - 1)
p = visiveis[ss["passo"]]

st.progress((ss["passo"] + 1) / len(visiveis), text=f"Pergunta {ss['passo'] + 1} de {len(visiveis)} · {p['etapa']}")
st.subheader(p["pergunta"])
if p.get("ajuda"):
    st.caption(p["ajuda"])

escolha = None
if p["opcoes"]:
    rotulos = {o["valor"]: o["rotulo"] for o in p["opcoes"]}
    if p.get("multipla"):
        padrao = ss["escolhas"].get(p["id"], [])
        escolha = [o["valor"] for o in p["opcoes"]
                   if st.checkbox(o["rotulo"], value=o["valor"] in padrao, key=f"chk_{p['id']}_{o['valor']}")]
    else:
        valores_op = list(rotulos) + [arv.OUTRO]
        atual = ss["escolhas"].get(p["id"], valores_op[0])
        escolha = st.radio("Sugestões", valores_op, index=valores_op.index(atual) if atual in valores_op else 0,
                           format_func=lambda x: "Outro (descrever)" if x == arv.OUTRO else rotulos[x],
                           key=f"radio_{p['id']}", label_visibility="collapsed")
        if escolha == arv.OUTRO:
            ss["outros"][p["id"]] = st.text_input("Descreva", ss["outros"].get(p["id"], ""), key=f"outro_{p['id']}")
            st.info("Itens marcados como 'Outro' ficam listados no orçamento para preenchimento manual.")
    ss["escolhas"][p["id"]] = escolha

campos = arv.campos_ativos(p, escolha)
if campos:
    cols = st.columns(2)
    for i, c in enumerate(campos):
        inteiro = c.get("inteiro", False)
        atual = ss["valores"].get(c["id"], c["padrao"])
        rotulo = c["rotulo"] + (" · índice" if c.get("parametrico") else "")
        val = cols[i % 2].number_input(rotulo, value=int(atual) if inteiro else float(atual), min_value=0 if inteiro else 0.0,
                                       step=int(c["passo"]) if inteiro else float(c["passo"]), help=c.get("ajuda"),
                                       key=f"num_{c['id']}", format=None if inteiro else "%.3f")
        ss["valores"][c["id"]] = val

st.divider()
b1, b2, b3 = st.columns([1, 1, 3])
if b1.button("◀ Anterior", disabled=ss["passo"] == 0, use_container_width=True):
    ss["passo"] -= 1
    st.rerun()
if ss["passo"] < len(visiveis) - 1:
    if b2.button("Próxima ▶", type="primary", use_container_width=True):
        ss["passo"] += 1
        st.rerun()
else:
    if b2.button("Gerar orçamento ✔", type="primary", use_container_width=True):
        st.switch_page("paginas/resultado.py")
if b3.button("Recomeçar do zero"):
    for k in ("escolhas", "valores", "outros", "passo", "nome_obra", "orcamento_id"):
        ss.pop(k, None)
    st.rerun()

with st.sidebar:
    st.markdown("**Etapas**")
    for i, q in enumerate(visiveis):
        marca = "✅" if q["id"] in ss["escolhas"] or (not q["opcoes"] and i < ss["passo"]) else "▫️"
        if st.button(f"{marca} {i + 1}. {q['pergunta'][:38]}", key=f"ir_{i}", use_container_width=True):
            ss["passo"] = i
            st.rerun()
