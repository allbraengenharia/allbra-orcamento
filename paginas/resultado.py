import pandas as pd
import streamlit as st

from orcamento import arvore as arv
from orcamento import calculo, db
from orcamento.quantitativos import calcular

ss = st.session_state
st.title("Orçamento")

if not ss.get("escolhas"):
    st.info("Responda primeiro o jogo de seleção em **Novo orçamento**.")
    st.stop()

emp = db.empresa()
arvore = arv.carregar()
itens = calcular(ss["escolhas"], ss["valores"])
bdi = st.sidebar.number_input("BDI (%)", value=float(emp["bdi_pct"]), step=0.5)
df = calculo.montar(itens, bdi)
area = float(ss["valores"].get("area_construida", 0) or 0)

st.caption(f"{ss.get('nome_obra') or 'Obra sem nome'} · {ss['escolhas'].get('subtipologia', '')} · "
           f"{ss['escolhas'].get('municipio', '')} · {area:g} m² · BDI {bdi:g}%")

sem_preco = df["preco_unit"].isna().sum()
total = df["total_bdi"].sum()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Serviços", len(df))
c2.metric("Sem preço vinculado", int(sem_preco))
c3.metric("Total com BDI", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
c4.metric("Custo por m²", f"R$ {total / area:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if area else "—")
if sem_preco:
    st.warning(f"{sem_preco} serviço(s) ainda sem composição vinculada. Use **Vínculos de composições** para ligá-los "
               "a uma tabela de preço (SINAPI, GOINFRA ou própria).")

outros = {k: v for k, v in ss.get("outros", {}).items() if ss["escolhas"].get(k) == arv.OUTRO}
if outros:
    st.info("Itens descritos como 'Outro' (orçar manualmente): " + "; ".join(outros.values()))

aba1, aba2, aba3, aba4 = st.tabs(["Analítico", "Resumo por etapa", "Curva ABC", "Premissas"])
with aba1:
    mostrar = df[["eap", "etapa", "descricao", "unidade", "quantidade", "origem", "memoria", "fonte", "codigo",
                  "preco_unit", "preco_unit_bdi", "total_bdi"]]
    st.dataframe(mostrar, hide_index=True, use_container_width=True, height=560,
                 column_config={"eap": "Item", "etapa": None, "descricao": "Serviço", "unidade": "Un",
                                "quantidade": st.column_config.NumberColumn("Quant.", format="%.2f"),
                                "origem": "Origem", "memoria": "Memória de cálculo", "fonte": "Base",
                                "codigo": "Código",
                                "preco_unit": st.column_config.NumberColumn("P. unit.", format="R$ %.2f"),
                                "preco_unit_bdi": st.column_config.NumberColumn("P. unit. c/ BDI", format="R$ %.2f"),
                                "total_bdi": st.column_config.NumberColumn("Total", format="R$ %.2f")})
    st.caption("Origem: **digitada** = informada por você · **calculada** = geometria · "
               "**paramétrica** = estimada por índice (sem projeto complementar).")
etapas = calculo.resumo_etapas(df)
with aba2:
    st.dataframe(etapas, hide_index=True, use_container_width=True,
                 column_config={"etapa": "Etapa", "itens": "Itens",
                                "custo_direto": st.column_config.NumberColumn("Custo direto", format="R$ %.2f"),
                                "total_bdi": st.column_config.NumberColumn("Total c/ BDI", format="R$ %.2f"),
                                "pct": st.column_config.NumberColumn("%", format="%.2f%%")})
abc = calculo.curva_abc(df)
with aba3:
    if abc.empty:
        st.info("A curva ABC aparece quando houver serviços com preço vinculado.")
    else:
        st.bar_chart(abc.set_index("descricao")["pct_acumulado"], horizontal=False)
        st.dataframe(abc, hide_index=True, use_container_width=True)
premissas = pd.DataFrame(arv.premissas(arvore, ss["escolhas"], ss["valores"], ss.get("outros", {})))
with aba4:
    st.dataframe(premissas, hide_index=True, use_container_width=True)

st.divider()
c1, c2 = st.columns(2)
nome = c1.text_input("Nome para salvar", ss.get("nome_obra") or "Orçamento")
if c1.button("Salvar orçamento", type="primary"):
    ss["orcamento_id"] = db.salvar_orcamento(nome, {"escolhas": ss["escolhas"], "valores": ss["valores"],
                                                    "outros": ss.get("outros", {}), "nome_obra": nome},
                                             ss.get("orcamento_id"))
    st.success(f"Salvo como orçamento #{ss['orcamento_id']}.")
cab = {"Empresa": emp["razao_social"], "CNPJ": emp["cnpj"], "Responsável técnico": emp["responsavel_tecnico"],
       "Obra": ss.get("nome_obra", ""), "Município": ss["escolhas"].get("municipio", ""),
       "Área construída (m²)": area, "BDI (%)": bdi, "Total com BDI (R$)": round(total, 2)}
c2.download_button("Baixar Excel", calculo.excel(df, etapas, abc, cab, premissas),
                   file_name=f"orcamento_{nome}.xlsx".replace(" ", "_"),
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
ss["ultimo_orcamento"] = df[["servico", "descricao", "unidade"]].to_dict("records")
