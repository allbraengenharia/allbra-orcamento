# Allbra Orçamento

Programa de orçamento de obras da **Allbra Engenharia** (Aparecida de Goiânia/GO), guiado por um jogo de perguntas
com sugestões. Roteiro completo do produto: [docs/roteiro-programa-orcamento.md](docs/roteiro-programa-orcamento.md).

## Estado atual: fase 0
- Jogo de seleção da tipologia **Residencial** (térrea e MCMV): 23 perguntas com 5 sugestões cada + "Outro".
- Motor de quantitativos com origem de cada número (digitada, calculada, paramétrica) e memória de cálculo.
- Importação de tabelas de preço gratuitas (SINAPI, GOINFRA) e tabela própria, com detecção do cabeçalho.
- Vínculo serviço → composição, salvo para os próximos orçamentos.
- Orçamento analítico, resumo por etapa, curva ABC, premissas e exportação para Excel.
- Cadastro da empresa (Simples Nacional, encargos com INSS padrão, BDI).

## Rodar no computador
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Estrutura
- `app.py` · navegação entre as telas
- `paginas/` · telas (jogo, orçamento, vínculos, tabelas de preço, empresa)
- `orcamento/quantitativos.py` · regras de quantitativo por etapa
- `orcamento/importador.py` · leitura de planilhas SINAPI/GOINFRA/própria
- `orcamento/db.py` · banco SQLite local (`dados/allbra.db`)
- `dados/arvore_residencial_terrea.json` · perguntas, sugestões e campos (editável sem programar)

## Observação sobre hospedagem gratuita
No Streamlit Community Cloud o arquivo `dados/allbra.db` é apagado quando o app reinicia. Na próxima fase o banco
passa para um PostgreSQL gratuito (Supabase) para guardar tabelas, vínculos e orçamentos de forma permanente.
