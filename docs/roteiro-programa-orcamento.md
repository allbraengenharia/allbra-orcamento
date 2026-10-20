# Roteiro de desenvolvimento: programa de orçamento de obras com IA

**Versão 1.1 · 20/10/2026** (abertura pela planta baixa, inventário de projetos, regimes, remuneração dos operários, tipologias, bases gratuitas, alternativas de desenvolvimento)
Documento-base para orientar o desenvolvimento, do PDF do projeto até o orçamento detalhado com cronograma, curva ABC e histograma de mão de obra.

---

## 0. Empresa usuária

| Dado | Valor (consulta pública de CNPJ, confirmado pelo usuário) |
|---|---|
| Nome fantasia | Allbra Engenharia |
| Razão social | Allbra Construtora e Incorporadora Ltda |
| CNPJ | 28.481.350/0001-36 |
| Sede | Aparecida de Goiânia (GO) |
| Atividade principal | CNAE 4120-4/00 · Construção de edifícios |
| Situação | ativa desde 23/08/2017 |
| Regime tributário | Simples Nacional (informado pelo usuário) |
| Responsável técnico | Octtávio de Morais Lopes (informado pelo usuário) |

**Simples Nacional no orçamento:** construção de edifícios se enquadra no Anexo IV, em que a contribuição previdenciária patronal (CPP, 20 % sobre a folha) é recolhida à parte, fora do DAS. **Decisão do usuário:** adotar como padrão os **encargos sociais com INSS padrão** (tabela de encargos do SINAPI-GO, não desonerada), deixando a opção de editar depois. O cadastro da empresa terá um campo "regime de encargos" (padrão SINAPI · Simples Anexo IV · personalizado) e o BDI terá o campo de alíquota efetiva do DAS, ambos editáveis, para ajuste futuro com o contador.

**Como isso entra no programa:**
- **Preços de referência:** SINAPI de Goiás (os preços do SINAPI são coletados na capital, Goiânia, vizinha à sede) e tabela GOINFRA, ambas já como padrão.
- **Obra local ou fora da cidade (Etapa 11):** a sede em Aparecida de Goiânia é o ponto de partida. Obras na região metropolitana de Goiânia contam como locais; acima de uma distância configurável (ex.: 80 km), o programa ativa alojamento, alimentação, deslocamento e mobilização.
- **Conferência de custo/m²:** CUB do Sinduscon-GO.
- **BDI e tributos:** regime tributário da empresa e ISS do município da obra, configuráveis no cadastro da empresa.
- **Relatórios:** cabeçalho com logomarca, razão social, CNPJ e responsável técnico da Allbra.
- **Tabela própria:** preços de fornecedores e de mão de obra praticados pela Allbra na região, cadastrados pela própria empresa.

## 1. Visão em uma frase

O operador (técnico em edificações) envia o projeto arquitetônico em PDF. A IA lê o que conseguir, propõe respostas e conduz um **jogo de seleção**: a cada pergunta mostra **5 sugestões** (mais "outro / informar valor"), o operador escolhe ou corrige, e cada escolha filtra as perguntas seguintes. No fim, o sistema monta o orçamento com composições de custo de referência (SINAPI e outras), BDI, encargos, custos de canteiro e logística, e gera cronograma semanal, curva ABC e histograma de operários.

**Princípio central:** a IA sugere, o técnico decide. Toda quantidade e toda escolha ficam rastreáveis (de onde veio: leitura do PDF, regra paramétrica ou digitação do operador).

---

## 2. Fluxo geral (do PDF ao orçamento)

```
 PDF do projeto
     │
     ▼
[1] Leitura e extração (IA)  ──► ambientes, áreas, cotas, pé-direito, legendas, quadros de esquadrias
     │
     ▼
[2] Jogo de seleção (perguntas com 5 sugestões, em árvore)
     │   tipologia → terreno → infraestrutura → estrutura → vedações → cobertura
     │   → instalações → esquadrias → acabamentos → equipamentos → canteiro/logística
     ▼
[3] Motor de quantitativos  ──► quantidades por serviço (m², m³, kg, un, m)
     │
     ▼
[4] Vinculação a composições ──► SINAPI / TCPO / SICRO / base própria
     │
     ▼
[5] Custo direto + encargos + custos de canteiro/logística + BDI
     │
     ▼
[6] Planejamento ──► cronograma semanal (estilo Project), histograma de mão de obra
     │
     ▼
[7] Saídas ──► orçamento sintético/analítico, curva ABC, cronograma físico-financeiro,
               tabela semanal de operários, exportação Excel/PDF/MS Project (XML)
```

---

## 3. O "jogo de seleção": como funciona cada pergunta

Cada pergunta é um **nó** de uma árvore de decisão. Estrutura de um nó:

| Campo | Exemplo |
|---|---|
| Etapa | Fundação |
| Pergunta | "Qual o tipo de fundação?" |
| 5 sugestões (ordenadas pela IA) | Sapata isolada · Radier · Estaca broca + baldrame · Estaca hélice contínua · Sapata corrida |
| Opção extra | "Outro" (texto livre) e "Não se aplica" |
| Justificativa da IA | "Sugeri radier em 1º por ser residência térrea de padrão popular em terreno plano (lido no PDF)" |
| Campos numéricos ligados | Profundidade média (m), fck do concreto (MPa), taxa de aço (kg/m³) |
| Condição de exibição | só aparece se tipologia ≠ "reforma sem intervenção estrutural" |
| Efeito | ativa composições do grupo FUNDAÇÃO e as perguntas filhas (ex.: "diâmetro da estaca?") |

**Como a IA escolhe as 5 sugestões:** combinação de (a) o que leu no PDF, (b) regras técnicas por tipologia/porte/região e (c) com o tempo, o histórico de escolhas dos próprios orçamentos salvos. A ordem expressa a probabilidade; a 1ª vem pré-marcada mas nunca é aceita sem clique.

**Campos variáveis que o operador preenche** (sem padrão fixo, como você pediu): pé-direito, espessura de laje, espessura de parede, altura de platibanda, profundidade de fundação, inclinação de telhado, cotas de corte/aterro, distâncias de transporte, etc. A IA pode **pré-preencher** com o valor lido no PDF, sinalizando em cor diferente o que foi lido e o que foi digitado.

**Seleção múltipla por ambiente:** para acabamentos, o jogo pergunta ambiente a ambiente (ou por grupos: "áreas molhadas", "áreas secas", "externas"), permitindo "aplicar a todos os semelhantes".

---

## 4. Mapa completo das perguntas (árvore de decisão)

### Etapa de abertura · Planta baixa e inventário de projetos
O programa começa pedindo **somente a planta baixa** (PDF). Depois de lê-la e conhecer a obra (ambientes, áreas, nº de pavimentos), pergunta quais outros projetos o operador possui, numa lista de caixas de seleção:

| Projeto / documento | Possui? | Se possuir | Se não possuir |
|---|---|---|---|
| Cortes | sim / não | lê pé-direito, laje, cobertura | pergunta pé-direito e espessura de laje |
| Fachadas (vistas) | sim / não | lê platibanda, esquadrias, revestimento externo | pergunta por seleção |
| Planta de cobertura | sim / não | lê tipo de telha, caimentos, calhas | sugere pela tipologia e pergunta inclinação |
| Planta de situação / implantação | sim / não | lê recuos, muros, calçadas | pergunta dimensões do terreno |
| Levantamento topográfico | sim / não | lê cotas, calcula corte/aterro | pergunta tipo de topografia |
| Sondagem (SPT) | sim / não | apoia escolha da fundação | sugere fundação conservadora e alerta |
| Estrutural | sim / não | lê fundação, pilares, vigas, lajes, taxas | usa índices paramétricos |
| Hidráulico (água fria/quente) | sim / não | lê pontos e tubulações | estima pontos por ambiente |
| Esgoto e pluvial | sim / não | lê caixas, ramais, destino | estima por pontos e área de cobertura |
| Elétrico | sim / não | lê pontos, circuitos, quadro | estima pontos por ambiente (NBR 5410) |
| Quadro de esquadrias | sim / não | lê tipos, medidas, quantidades | identifica vãos na planta e pergunta o material |
| Memorial descritivo | sim / não | lê especificações de acabamento | pergunta acabamento por ambiente |
| Outros (gás, incêndio, SPDA, climatização) | sim / não | lê o que houver | estima conforme tipologia |

Cada projeto enviado reduz o número de perguntas seguintes. Cada "não" ativa estimativas paramétricas, e os itens resultantes ficam marcados como **estimados** no orçamento. Os projetos podem ser enviados a qualquer momento: o sistema relê e atualiza as respostas, mostrando ao operador o que mudou.

### Etapa 0 · Enquadramento do empreendimento
- **Tipologia e subtipologia:** a IA rastreia a tipologia a partir da planta baixa e propõe as 5 mais prováveis. Depois identifica a compartimentação (ambiente a ambiente), e é ela que ativa as perguntas e os equipamentos específicos. Catálogo inicial:

| Tipologia | Subtipologias |
|---|---|
| Residencial | MCMV (habitação de interesse social) · térrea · sobrado · vertical (multifamiliar) |
| Comercial | galpão · mezanino · loja · restaurante · escritório · lava-jato |
| Industrial | galpão · armazém · escritório · restaurante · lava-jato · ambiente específico |
| Hospitalar / saúde | apartamentos (internação) · posto de enfermagem · restaurante · ambiente específico |
| Outro | texto livre, a IA monta as perguntas a partir dos ambientes identificados |

  Uma obra pode combinar subtipologias (ex.: galpão industrial + escritório + restaurante). Cada **ambiente** recebe sua própria subtipologia, e cada uma traz um "pacote" de sugestões: acabamentos, pontos de instalação e equipamentos típicos (ex.: lava-jato → piso de alta resistência, caixa separadora de água e óleo, rampa/elevador automotivo, pontos de água e ar comprimido; restaurante → coifa, caixa de gordura, revestimento lavável; posto de enfermagem → pia de assepsia, gases medicinais, pontos de rede). "Ambiente específico" abre uma lista de perguntas livres guiada pela IA.

  Os pacotes ficam cadastrados em tabelas editáveis, para que novas tipologias entrem sem reprogramação.
- **Natureza:** construção nova · ampliação · reforma · retrofit.
- **Porte:** área construída (lida do PDF, editável); classificação pequeno / médio / grande.
- **Padrão de acabamento** (alinhado à NBR 12721 / CUB): baixo · normal · alto.
- **Complexidade:** baixa · média · alta (influencia produtividade e BDI).
- **Regime de contratação:** empreitada global (material + mão de obra) · empreitada de mão de obra (material fornecido pelo contratante) · empreitada por preço unitário · administração (custo + taxa) · tarefa · obra pública (Lei 14.133/2021) ou privada.
  - Na **empreitada de mão de obra**, o orçamento separa os materiais numa lista de compras do contratante (com quantidades e preços de referência) e o preço do contrato cobre só mão de obra, equipamentos, canteiro e BDI.
- **Forma de remuneração dos operários** (por profissão, podendo misturar): mensal (CLT, com encargos) · diária · por hora · por produção/empreita (R$ por m², m³, ponto, etc.). Campos: valor por profissão (pedreiro, servente, armador, carpinteiro, eletricista, encanador, pintor...), dias trabalhados, e se os encargos sociais incidem ou não. O sistema converte tudo para custo por hora e aplica nas composições, no lugar do salário de referência do SINAPI quando o operador preferir.
- **Desoneração da folha:** onerado ou desonerado (muda encargos sociais, como no SINAPI).
- **Localização:** UF e município (define a tabela de preços) · dentro da cidade-sede ou fora (ativa logística).

### Etapa 1 · Terreno e serviços preliminares
- Características do solo: argiloso · arenoso · rochoso · misto · aterro existente · (laudo de sondagem SPT disponível? sim/não).
- Topografia: plano · aclive leve · aclive acentuado · declive leve · declive acentuado.
- Terraplanagem: não precisa · só corte · só aterro · corte + aterro (volumes) · com bota-fora (distância em km).
- Contenção: não precisa · muro de arrimo em alvenaria · muro de concreto armado · gabião · cortina de estacas.
- Limpeza do terreno, demolições, locação da obra, tapume, placa de obra.
- Cercamento definitivo: muro de bloco · alambrado · gradil · cerca de concreto · nenhum (perímetro em m e altura).
- Ligações provisórias e definitivas: água (concessionária ou poço), energia (padrão mono/bi/trifásico, entrada aérea ou subterrânea), esgoto (rede pública · fossa + sumidouro · fossa + filtro · ETE compacta).

### Etapa 2 · Infraestrutura (fundação)
Sapata isolada · sapata corrida · radier · estaca broca · estaca escavada · hélice contínua · estaca pré-moldada · tubulão. Campos: profundidade, fck, taxa de aço, vigas baldrame, impermeabilização do baldrame.

### Etapa 3 · Superestrutura
- Sistema: concreto armado moldado in loco · alvenaria estrutural · pré-moldado · estrutura metálica · steel frame · wood frame.
- Laje: maciça · treliçada (EPS/cerâmica) · nervurada · alveolar · steel deck.
- Campos: espessura da laje, vão médio, nº de pavimentos, pé-direito por pavimento, taxa de aço e de forma (ou estimativa paramétrica).

### Etapa 4 · Vedações
Bloco cerâmico · bloco de concreto · tijolo maciço · drywall · painéis. Campos: espessura, altura, descontos de vãos (regra de desconto configurável).

### Etapa 5 · Cobertura
Telha cerâmica · fibrocimento · metálica (simples/termoacústica) · laje impermeabilizada · telhado verde. Estrutura: madeira · metálica. Campos: inclinação, beiral, rufos, calhas, condutores.

### Etapa 6 · Impermeabilizações
Áreas molhadas, lajes, reservatórios, baldrames: manta asfáltica · argamassa polimérica · membrana acrílica.

### Etapa 7 · Instalações (dependem da tipologia)
- Hidrossanitárias: água fria, água quente (solar · gás · elétrico), esgoto, águas pluviais, reservatório (volume).
- Elétricas: nº de pontos estimados por ambiente (padrão da NBR 5410 como sugestão), quadro, SPDA.
- Gás, telefonia/dados, CFTV, climatização, prevenção e combate a incêndio (extintores, hidrantes, sprinkler conforme tipologia).
- **Equipamentos da tipologia:** ex.: escola (cozinha industrial, bebedouros), clínica (gases medicinais), galpão (piso industrial, pontes rolantes), multifamiliar (elevador, bombas, gerador).

### Etapa 8 · Esquadrias
Lidas do quadro de esquadrias do PDF quando existir. Material: madeira · alumínio · PVC · aço · vidro temperado. Portas internas/externas, janelas, portões, guarda-corpos, ferragens.

### Etapa 9 · Revestimentos e acabamentos (por ambiente)
Contrapiso, piso (cerâmico · porcelanato · vinílico · cimentado · laminado), rodapé, chapisco/emboço/reboco, revestimento de parede, forro (gesso · PVC · laje aparente), pintura (látex · acrílica · textura · epóxi), soleiras, peitoris, bancadas, louças e metais.

### Etapa 10 · Serviços complementares
Paisagismo, calçadas, pavimentação externa, limpeza final, as built, ligações definitivas.

### Etapa 11 · Canteiro, logística e equipe
- Prazo estimado: em **dias corridos** e/ou **dias trabalhados** (o sistema converte usando calendário com sábados, feriados e chuvas configuráveis).
- Jornada: horas/dia, dias/semana.
- Quantidade média de colaboradores previstos (o sistema também calcula e compara com o histograma).
- Obra local ou fora da cidade.
- **Alojamento:** casa alugada (valor mensal + mobília + contas) · hotel (diária × pessoas × dias) · não aplicável.
- **Alimentação:** café da manhã · almoço · lanche · jantar (marcar quais e o custo unitário de cada).
- Transporte de equipe, viagens de mobilização/desmobilização.
- Administração local: engenheiro, mestre, encarregado, almoxarife, vigia (em % do tempo).
- Canteiro: barracão, banheiros, refeitório (NR-18), consumo de água/energia, equipamentos alugados (betoneira, andaimes, guincho, container).

**Fórmulas de exemplo (todas editáveis):**
- Alimentação = Σ (refeições marcadas × custo unitário) × colaboradores × dias trabalhados.
- Hotel = diária × nº de quartos (colaboradores ÷ pessoas por quarto) × dias corridos.
- Casa alugada = aluguel mensal × meses + caução + contas estimadas.

---

## 5. Leitura do PDF pela IA (o que é realista)

| Tipo de PDF | O que dá para extrair | Confiabilidade |
|---|---|---|
| PDF vetorial exportado do CAD/BIM | textos, cotas, nomes e áreas dos ambientes, quadros de esquadrias, escala | boa |
| PDF escaneado (imagem) | textos via OCR, ambientes por visão computacional | média/baixa |
| Projeto "básico" (só planta) | ambientes, áreas, perímetros aproximados | média, exige mais perguntas |
| Projeto "completo" (cortes, fachadas, memorial) | pé-direito, cobertura, especificações de acabamento | boa, menos perguntas |

**Estratégia recomendada em camadas:**
1. Extrair texto e vetores do PDF (bibliotecas como PyMuPDF/pdfplumber).
2. Modelo multimodal (Claude) interpreta cada prancha: identifica ambientes, quadro de áreas, legendas, quadro de esquadrias, cortes.
3. Calibração de escala: o operador confirma uma cota conhecida.
4. Tudo que a IA leu vira **pré-preenchimento** do jogo de seleção, nunca valor final.

Quando o projeto for só arquitetônico (sem estrutural/instalações), o sistema usa **estimativas paramétricas** (taxas de aço, forma, pontos elétricos por m², etc.) e marca o item como "estimado".

---

## 6. Motor de quantitativos

Quatro origens de quantidade, sempre registradas:
1. **Lida** do PDF (ex.: área do quarto = 12,40 m²).
2. **Calculada** por regra (ex.: alvenaria = perímetro × pé-direito − vãos).
3. **Paramétrica** por índice (ex.: aço = volume de concreto × 80 kg/m³).
4. **Digitada** pelo operador (prevalece sobre as demais).

Regras de cálculo ficam em uma tabela editável (não no código), para o técnico ajustar sem programar. Exemplo: "descontar vãos maiores que 2 m² na alvenaria".

---

## 7. Bases de custo (referências do mercado brasileiro)

| Base | Quem mantém | Uso no programa |
|---|---|---|
**Decisão do usuário: só bases gratuitas.** As três bases do programa são:

| Base | Quem mantém | Uso no programa |
|---|---|---|
| **SINAPI** (gratuita) | Caixa + IBGE | base principal de composições e insumos, mensal, por UF, onerado e desonerado; obrigatória como referência em obras com recursos federais. Desde 2022 publica também composições **paramétricas** (úteis na fase de viabilidade). |
| **GOINFRA** (gratuita) | Agência Goiana de Infraestrutura e Transportes | tabela de preços de Goiás para edificações e infraestrutura; complementa serviços que o SINAPI não cobre e regionaliza os preços. |
| **Tabela própria** | o usuário | composições, preços de fornecedores e valores de mão de obra reais (mensal/diária), que com o tempo calibram o sistema. |

Em cada item do orçamento o operador escolhe a base (ou o sistema propõe a mais barata/mais adequada), e o relatório mostra o código e a base de origem, como fazem os softwares de mercado.

Referências apenas para conferência (sem embutir no programa): **CUB/m²** dos Sinduscons (gratuito, NBR 12721) para comparar o custo/m² final; **SICRO/DNIT** (gratuito) se houver terraplanagem pesada ou pavimentação. TCPO e outras bases pagas ficam de fora.

**Composição de preço unitário:** insumos (material + mão de obra + equipamento) × coeficientes. A mão de obra de cada composição tem **coeficiente em h/unidade por profissão** (pedreiro, servente, armador, carpinteiro, eletricista...), e é isso que alimenta o histograma de operários.

**Encargos sociais:** usar a tabela do SINAPI (horista/mensalista, onerado/desonerado, por UF) como padrão, editável.

**BDI:** calculadora com administração central, seguros, garantias, riscos, despesas financeiras, lucro e tributos (PIS, COFINS, ISS, CPRB quando desonerado). Para obra pública, faixas de referência do **Acórdão TCU 2622/2013** por tipo de obra, com alerta quando ficar fora da faixa.

---

## 8. Saídas do programa

1. **Orçamento sintético** (por etapa/serviço: código, descrição, unidade, quantidade, preço unitário, total) e **analítico** (com as composições abertas).
2. **Orçamento compacto**: uma página com resumo por etapa, custo/m², comparação com CUB, BDI e total.
3. **Curva ABC de serviços e de insumos**: ordena por valor, acumula %, classifica (padrão A = até 50 %, B = 50–80 %, C = 80–100 %, faixas configuráveis), com gráfico de Pareto.
4. **Cronograma semanal estilo MS Project**: EAP (estrutura analítica), tarefas com duração, predecessoras (TI, II, TT), caminho crítico, gráfico de Gantt por semana; exportação em **XML do MS Project** e Excel.
5. **Cronograma físico-financeiro**: % e R$ por semana e por mês, desembolso acumulado (curva S).
6. **Tabela/histograma de mão de obra por semana**: para cada serviço e semana, nº de profissionais e auxiliares.
   - Homem-hora do serviço = quantidade × coeficiente (h/un) da composição, por profissão.
   - Operários na semana = HH distribuídas na semana ÷ (horas/dia × dias trabalhados na semana), arredondando para cima.
   - Totais por profissão e por semana, pico de equipe e média (comparada à média informada na Etapa 11, com alerta se divergir muito).
7. **Memorial de premissas**: todas as respostas do jogo de seleção, com origem (lida, calculada, paramétrica, digitada). Serve como memória de cálculo e defesa do orçamento.

---

### 8.1 Técnicas do Sienge adotadas (decisão do usuário)
O programa segue a lógica de orçamento e planejamento usada no Sienge, recriada com bases gratuitas:
- **EAP em níveis**: obra → unidade construtiva (bloco, pavimento, casa) → etapa → subetapa → serviço, com códigos hierárquicos (ex.: 03.02.005).
- **Insumos agrupados** por tipo (material, mão de obra, equipamento, serviço de terceiros) e por grupo de compra, gerando a lista de insumos consolidada da obra.
- **Orçamento analítico e sintético** a partir da mesma base, com código e fonte (SINAPI, GOINFRA, própria) em cada item.
- **Versões do orçamento** (estimativa, básico, executivo, revisões), com comparação entre versões.
- **Planejamento vinculado ao orçamento**: cada tarefa do cronograma aponta para serviços da EAP, de modo que o cronograma físico-financeiro e o desembolso saem automaticamente.
- **Curva ABC de insumos e de serviços** com filtros por etapa.
- **Preparação para controle de obra** (fase futura): medição de avanço físico e comparação orçado × realizado.

## 9. Duração das tarefas (como o cronograma é gerado)

- Duração de cada serviço = HH total ÷ (tamanho da equipe × horas/dia).
- O sistema sugere equipes-padrão por serviço (ex.: alvenaria = 2 pedreiros + 1 servente) e o operador ajusta.
- Precedências padrão por tipologia (ex.: fundação → estrutura → alvenaria → cobertura → instalações embutidas → revestimentos → pintura), editáveis.
- Se o prazo informado na Etapa 11 for menor que o calculado, o sistema propõe aumentar equipes nas tarefas do caminho crítico e mostra o impacto no pico de operários e no custo de canteiro.

---

## 10. Como construir sem saber programar (alternativas)

| Alternativa | Como funciona | Custo | Prós | Contras |
|---|---|---|---|---|
| **A. Claude desenvolve o código, hospedagem gratuita** (recomendada) | Claude escreve e mantém o programa num repositório GitHub gratuito; ele roda online em hospedagem gratuita (ex.: Streamlit Community Cloud ou Vercel + Supabase plano grátis). Você testa no navegador e pede ajustes em português aqui no projeto. | R$ 0 de software e hospedagem; só o uso da IA (ver abaixo) | sem limite de complexidade; o código é seu; atende tudo do roteiro | depende de seguir pedindo ajustes ao Claude; planos gratuitos têm limites de uso |
| **B. Planilha Google + Apps Script** | Planilhas com as bases e o orçamento; formulários e menus em script | grátis | familiar para quem usa Excel | leitura de PDF por IA e cronograma estilo Project ficam muito limitados; cresce mal com muitas tipologias |
| **C. Plataformas no-code** (Bubble, FlutterFlow, Glide, Softr) | Montar telas arrastando blocos | planos úteis são pagos (em dólar) | visual, sem código | cálculo pesado, PDF e IA ficam difíceis; você fica preso à plataforma |
| **D. Contratar desenvolvedor freelancer** | Entregar este roteiro a um programador | alto (projeto de meses) | alguém dedicado | custo; manutenção depende dele |

**Sobre "nada pago":** software, bases e hospedagem podem ser 100 % gratuitos. A única parte com custo variável é a **IA online** que lê o PDF e gera as sugestões: cobra por uso (centavos a poucos reais por projeto lido, conforme o tamanho). Há alternativas com cota gratuita limitada, e o programa pode funcionar também em modo "sem IA" (o jogo de seleção com sugestões por regras), usando IA só na leitura da planta.

**Recomendação:** alternativa A, começando com Streamlit (Python), porque é a forma mais simples de ter um programa online gratuito com tabelas, gráficos, upload de PDF e exportação para Excel. Se o produto crescer (vários usuários, venda para outros técnicos), migra-se a interface para uma aplicação web completa sem perder as regras e as bases.

**Para começar a alternativa A você precisa apenas:** criar uma conta gratuita no GitHub e conectá-la a este projeto; o restante Claude configura e explica passo a passo.

### Arquitetura técnica (alternativa A)

| Camada | Sugestão | Motivo |
|---|---|---|
| Interface | Streamlit no início (web, abre no celular/tablet); aplicação web completa depois | o técnico usa no escritório e na obra |
| Cálculo | Python | boas bibliotecas de PDF, dados e cálculo |
| Banco de dados | SQLite no início, PostgreSQL gratuito (Supabase) depois | composições, insumos, preços mensais por UF, orçamentos |
| IA | API do Claude (leitura multimodal do PDF e geração das sugestões) | interpreta pranchas e justifica sugestões |
| Árvore de perguntas | definida em dados (JSON/tabela), não fixa no código | permite incluir perguntas e tipologias sem reprogramar |
| Importação de bases | rotina mensal de importação das planilhas do SINAPI e da GOINFRA; tela de cadastro da tabela própria | preços sempre atualizados |
| Exportações | Excel (openpyxl), PDF, XML do MS Project | formatos usados no mercado |

**Modelo de dados principal (simplificado):**
`Projeto` → `Respostas do jogo` → `Ambientes` → `Itens do orçamento` (serviço, quantidade, origem) → `Composição` (insumos e coeficientes) → `Preço` (base, UF, mês, onerado/desonerado) · `Tarefas` (duração, predecessoras, equipe) · `Parâmetros de canteiro/logística` · `BDI`.

---

## 11. Fases de desenvolvimento

| Fase | Entrega | Critério de pronto |
|---|---|---|
| **0. Fundamentos** | Importação do SINAPI (uma UF) e cadastro de composições; árvore de perguntas para **uma tipologia** (residencial unifamiliar térrea) | orçamento manual de uma casa conferido contra planilha do técnico |
| **1. Jogo de seleção (sem IA)** | Perguntas com 5 sugestões fixas por regra, campos variáveis, motor de quantitativos com áreas digitadas | um orçamento completo gerado só por cliques e digitação |
| **2. Saídas** | Orçamento sintético/analítico/compacto, curva ABC, BDI, encargos, canteiro e logística | relatórios batem com cálculo manual |
| **3. Planejamento** | Cronograma semanal, Gantt, exportação MS Project, histograma semanal de operários | arquivo abre no MS Project; histograma confere com HH das composições |
| **4. IA na leitura do PDF** | Extração de ambientes, áreas, pé-direito, quadro de esquadrias, pré-preenchimento | em PDFs vetoriais de teste, erro de área abaixo de uma tolerância combinada (ex.: 5 %) |
| **5. IA nas sugestões** | Ordenação e justificativa das 5 sugestões com base no PDF e no histórico | operador aceita a 1ª sugestão na maioria das perguntas |
| **6. Expansão** | Outras tipologias (multifamiliar, comercial, galpão), outras UFs, TCPO/SICRO, base própria | — |

Começar estreito (uma tipologia, uma UF) e validar com orçamentos reais já feitos pelo operador é o que garante a assertividade.

---

## 12. O que já existe no mercado (para se diferenciar)

- **OrçaFascio**: orçamento em nuvem com várias bases (SINAPI e estaduais), integração BIM (OrçaBIM, Revit) e assistente de IA.
- **Sienge / Construmanager**: ERP de construtoras; o Construmanager anuncia levantamento de quantitativos por IA a partir de plantas 2D. **Modelo de referência escolhido pelo usuário**: os relatórios do programa (orçamento por etapa com código/base, analítico com composições, curva ABC, cronograma físico-financeiro) seguem a organização usada no Sienge, adaptada; o Sienge em si é pago e não será usado.
- **Volare / TCPO (PINI)**: orçamento e planejamento com a base TCPO.
- **MS Project, Primavera, Prevision**: planejamento e cronograma.
- **Ferramentas internacionais de takeoff com IA** (ex.: Togal.AI, Kreo, PlanSwift): leitura automática de plantas para quantitativos.

**O diferencial do seu programa:** nenhuma dessas une, num só fluxo guiado, (1) leitura do PDF, (2) um jogo de perguntas com sugestões que o técnico entende e controla, (3) custos de logística/canteiro detalhados (alojamento, refeições, obra fora da cidade) e (4) saída integrada de orçamento + cronograma semanal + histograma de operários por serviço.

---

## 13. Riscos e cuidados

- **IA errando com aparência de certeza:** toda leitura do PDF é sugestão, com origem visível e confirmação do operador.
- **Projetos incompletos:** usar paramétricos e marcar itens "estimados", com percentual de contingência sugerido.
- **Licenças de bases:** SINAPI é público; TCPO e outras são pagas. Verificar termos antes de embutir no sistema.
- **Atualização mensal dos preços:** prever rotina de importação e registrar a data-base de cada orçamento.
- **Responsabilidade técnica:** o programa é ferramenta de apoio; o orçamento final é assinado por profissional habilitado.
- **Conferência global:** comparar sempre custo/m² com o CUB da região e alertar desvios grandes.

---

## 14. Decisões em aberto (para você definir)

Já decidido: bases gratuitas (SINAPI, GOINFRA, tabela própria) · plataforma online · relatórios no modelo Sienge · catálogo de tipologias da Etapa 0.

1. **Tipologia do primeiro piloto:** sugestão é residencial térrea/MCMV; as demais entram nas fases seguintes, já previstas na estrutura.
2. **Público:** uso próprio, da sua empresa, ou produto para vender a outros técnicos (muda login, planos, hospedagem).
3. **Forma de desenvolver:** alternativa A da seção 10 (recomendada) ou outra.
4. **Projetos de teste:** 3 a 5 PDFs reais com orçamentos já feitos, para calibrar e medir acerto.

---

## Referências consultadas

- Caixa · SINAPI (metodologia, composições, paramétricas): https://www.caixa.gov.br/poder-publico/modernizacao-gestao/sinapi/paginas/default.aspx
- IBGE · SINAPI: https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9270-sistema-nacional-de-pesquisa-de-custos-e-indices-da-construcao-civil.html
- Caixa · Diálogos SINAPI (aferição das composições): https://sicepot2.task.com.br/Publicacoes/DialogosReg_SINAPI.pdf
- Sienge · Construmanager IA quantitativa: https://sienge.com.br/construmanager-ia-quantitativa/
- OrçaFascio · IA para orçamento de obras, aplicações e cuidados: https://www.orcafascio.com/papodeengenheiro/ia-para-orcamento-de-obras
- CONTECC 2024 (Confea) · Orçamento de obras utilizando processo BIM: https://www.confea.org.br/midias/uploads-imce/contecc%202024/CIV/OR%C3%87AMENTO_DE_OBRAS_UTILIZANDO_PROCESSO_BIM__AN%C3%81LISE_DA_INTEGRA%C3%87%C3%83O_ENTRE_SOFTWARES.pdf
- Cadastro público da Allbra Construtora e Incorporadora Ltda (CNPJ 28.481.350/0001-36): https://guiapj.com.br/en/company/28481350000136
- Normas e marcos citados (consultar versões vigentes): NBR 12721 (CUB), NBR 5410, NBR 15575, NR-18, Lei 14.133/2021, Acórdão TCU 2622/2013 (BDI).
