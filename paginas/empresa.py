import streamlit as st

from orcamento import db

st.title("Empresa")
emp = db.empresa()
with st.form("empresa"):
    c1, c2 = st.columns(2)
    emp["nome_fantasia"] = c1.text_input("Nome fantasia", emp["nome_fantasia"])
    emp["razao_social"] = c2.text_input("Razão social", emp["razao_social"])
    emp["cnpj"] = c1.text_input("CNPJ", emp["cnpj"])
    emp["responsavel_tecnico"] = c2.text_input("Responsável técnico", emp["responsavel_tecnico"])
    emp["cidade"] = c1.text_input("Cidade da sede", emp["cidade"])
    emp["uf"] = c2.text_input("UF", emp["uf"])
    emp["regime_tributario"] = c1.selectbox("Regime tributário", ["Simples Nacional", "Lucro Presumido", "Lucro Real"],
                                            index=["Simples Nacional", "Lucro Presumido", "Lucro Real"].index(emp["regime_tributario"]))
    opcoes_enc = ["INSS padrão (SINAPI-GO não desonerado)", "SINAPI-GO desonerado", "Simples Nacional Anexo IV", "Personalizado"]
    emp["regime_encargos"] = c2.selectbox("Encargos sociais", opcoes_enc, index=opcoes_enc.index(emp["regime_encargos"])
                                          if emp["regime_encargos"] in opcoes_enc else 0)
    emp["bdi_pct"] = c1.number_input("BDI padrão (%)", value=float(emp["bdi_pct"]), step=0.5)
    emp["distancia_obra_fora_km"] = c2.number_input("Distância a partir da qual a obra é 'fora da cidade' (km)",
                                                    value=float(emp["distancia_obra_fora_km"]), step=5.0)
    if st.form_submit_button("Salvar", type="primary"):
        db.salvar_empresa(emp)
        st.success("Dados da empresa salvos.")
