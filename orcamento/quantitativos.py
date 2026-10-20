"""Motor de quantitativos: transforma as respostas do jogo de seleção em serviços com quantidade.

Cada item guarda a origem da quantidade (digitada, calculada ou paramétrica) e a memória de cálculo,
para que o técnico saiba de onde veio cada número.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, asdict

DIGITADA = "digitada"
CALCULADA = "calculada"
PARAMETRICA = "paramétrica"


@dataclass
class Item:
    eap: str
    etapa: str
    servico: str
    descricao: str
    unidade: str
    quantidade: float
    origem: str
    memoria: str

    def dict(self) -> dict:
        return asdict(self)


class _Lista:
    def __init__(self):
        self.itens: list[Item] = []
        self._cont: dict[str, int] = {}

    def add(self, etapa_cod: str, etapa: str, servico: str, descricao: str, unidade: str,
            quantidade: float, origem: str, memoria: str):
        if quantidade is None or quantidade <= 0:
            return
        n = self._cont.get(etapa_cod, 0) + 1
        self._cont[etapa_cod] = n
        self.itens.append(Item(f"{etapa_cod}.{n:03d}", etapa, servico, descricao, unidade,
                               round(quantidade, 2), origem,
                               re.sub(r"(\d)\.(\d)", r"\1,\2", memoria)))


def _f(v: dict, chave: str, padrao: float = 0.0) -> float:
    try:
        return float(v.get(chave, padrao) or 0)
    except (TypeError, ValueError):
        return padrao


def calcular(escolhas: dict, valores: dict) -> list[Item]:
    """escolhas: {id_pergunta: valor ou lista}; valores: {id_campo: número}."""
    e, v = escolhas, valores
    L = _Lista()
    projetos = set(e.get("projetos") or [])

    area = _f(v, "area_construida")
    area_util = _f(v, "area_util") or area * 0.88
    perim = _f(v, "perimetro_ext")
    internas = _f(v, "paredes_int")
    pd = _f(v, "pe_direito", 2.6)
    vaos_portas = _f(v, "portas_int") * 0.8 * 2.1 + _f(v, "portas_ext") * 0.9 * 2.1
    vaos_janelas = _f(v, "area_janelas")
    vaos = vaos_portas + vaos_janelas
    banheiros = _f(v, "banheiros", 1)

    # 01 Serviços preliminares
    et = ("01", "Serviços preliminares")
    L.add(*et, "limpeza_terreno", "Limpeza manual do terreno", "m²", _f(v, "area_terreno"), DIGITADA,
          "área do terreno")
    L.add(*et, "locacao_obra", "Locação da obra (gabarito)", "m²", area, CALCULADA, "área construída")
    L.add(*et, "barracao", "Barracão de obra / depósito", "un", 1, PARAMETRICA, "1 unidade por obra")
    L.add(*et, "tapume", "Tapume de chapa (h = 2,20 m)", "m²", _f(v, "frente_terreno") * 2.2, CALCULADA,
          "testada × 2,20 m")
    if "placa_obra" in (e.get("calcada") or []):
        L.add(*et, "placa_obra", "Placa de obra", "m²", 2.0, PARAMETRICA, "placa padrão 2,00 m²")

    # 02 Movimento de terra e terreno
    et = ("02", "Movimento de terra e terreno")
    L.add(*et, "corte", "Escavação / corte de terreno", "m³", _f(v, "corte_m3"), DIGITADA, "volume informado")
    L.add(*et, "aterro", "Aterro compactado", "m³", _f(v, "aterro_m3"), DIGITADA, "volume informado")
    muro = e.get("muro")
    if muro and muro != "nenhum":
        comp, alt = _f(v, "muro_comprimento"), _f(v, "muro_altura", 2.0)
        if muro in ("bloco", "ceramico"):
            nome = "bloco de concreto" if muro == "bloco" else "tijolo cerâmico"
            L.add(*et, f"muro_{muro}", f"Muro de {nome}", "m²", comp * alt, CALCULADA,
                  f"{comp:g} m × {alt:g} m")
            L.add(*et, "muro_fundacao", "Fundação do muro (broca + baldrame)", "m", comp, CALCULADA,
                  "comprimento do muro")
        else:
            L.add(*et, f"cerca_{muro}", "Alambrado" if muro == "alambrado" else "Gradil", "m²", comp * alt,
                  CALCULADA, f"{comp:g} m × {alt:g} m")

    # 03 Fundação
    et = ("03", "Fundação")
    fund = e.get("fundacao")
    org_fund = CALCULADA if "estrutural" in projetos else PARAMETRICA
    paredes = perim + internas
    if fund == "radier":
        esp = _f(v, "radier_esp", 0.10)
        L.add(*et, "radier_preparo", "Preparo e compactação de base + lona", "m²", area, CALCULADA,
              "área construída")
        L.add(*et, "radier_concreto", "Concreto do radier", "m³", area * esp, CALCULADA,
              f"{area:g} m² × {esp:g} m")
        L.add(*et, "radier_aco", "Armação do radier (tela/aço)", "kg", area * _f(v, "radier_aco", 3.5), org_fund,
              f"{area:g} m² × {_f(v, 'radier_aco', 3.5):g} kg/m²")
        L.add(*et, "radier_forma", "Forma lateral do radier", "m²", perim * (esp + 0.10), CALCULADA,
              "perímetro × (espessura + 0,10)")
    elif fund in ("broca_baldrame", "helice_baldrame", "sapata_baldrame"):
        b, h = _f(v, "baldrame_b", 0.15), _f(v, "baldrame_h", 0.30)
        if fund == "sapata_baldrame":
            qtd = _f(v, "sapata_qtd") or math.ceil(area / 12)
            vol = _f(v, "sapata_vol", 0.35)
            L.add(*et, "escavacao_sapata", "Escavação manual de sapatas", "m³", qtd * vol * 1.6, org_fund,
                  f"{qtd:g} sapatas × {vol:g} m³ × 1,6 (folga)")
            L.add(*et, "sapata_concreto", "Concreto de sapatas", "m³", qtd * vol, org_fund,
                  f"{qtd:g} × {vol:g} m³")
            conc_extra = qtd * vol
        else:
            esp_est = _f(v, "estaca_esp", 2.5)
            n = math.ceil(paredes / esp_est)
            prof = _f(v, "estaca_prof", 3.0)
            nome = "Estaca broca Ø 25 cm" if fund == "broca_baldrame" else "Estaca hélice contínua Ø 30 cm"
            L.add(*et, "estaca_" + fund.split("_")[0], nome, "m", n * prof, org_fund,
                  f"{n} estacas ({paredes:g} m ÷ {esp_est:g} m) × {prof:g} m")
            conc_extra = 0.0
        conc_bald = paredes * b * h
        L.add(*et, "escavacao_baldrame", "Escavação de valas para baldrame", "m³", paredes * (b + 0.2) * (h + 0.1),
              CALCULADA, f"{paredes:g} m × {(b + 0.2):g} × {(h + 0.1):g}")
        L.add(*et, "baldrame_forma", "Forma de viga baldrame", "m²", paredes * h * 2, CALCULADA,
              f"{paredes:g} m × {h:g} m × 2 faces")
        L.add(*et, "baldrame_concreto", "Concreto de viga baldrame", "m³", conc_bald, CALCULADA,
              f"{paredes:g} m × {b:g} × {h:g}")
        L.add(*et, "fundacao_aco", "Armação de baldrame/sapatas", "kg",
              (conc_bald + conc_extra) * _f(v, "fundacao_aco", 80), org_fund,
              f"{conc_bald + conc_extra:.2f} m³ × {_f(v, 'fundacao_aco', 80):g} kg/m³")
        L.add(*et, "impermeabilizacao_baldrame", "Impermeabilização de baldrame", "m²", paredes * (b + 2 * h),
              CALCULADA, f"{paredes:g} m × ({b:g} + 2 × {h:g})")
    elif fund == "sapata_corrida":
        L.add(*et, "escavacao_sapata_corrida", "Escavação de valas", "m³", paredes * 0.6 * 0.5, CALCULADA,
              f"{paredes:g} m × 0,60 × 0,50")
        conc = paredes * 0.4 * 0.2
        L.add(*et, "sapata_corrida_concreto", "Concreto de sapata corrida", "m³", conc, CALCULADA,
              f"{paredes:g} m × 0,40 × 0,20")
        L.add(*et, "fundacao_aco", "Armação de sapata corrida", "kg", conc * _f(v, "fundacao_aco", 80), org_fund,
              f"{conc:.2f} m³ × {_f(v, 'fundacao_aco', 80):g} kg/m³")

    # 04 Superestrutura
    et = ("04", "Superestrutura")
    est = e.get("estrutura")
    if est == "concreto_armado":
        conc = area * _f(v, "indice_concreto", 0.045)
        L.add(*et, "estrutura_concreto", "Concreto de pilares, vigas e cintas", "m³", conc, org_fund,
              f"{area:g} m² × {_f(v, 'indice_concreto', 0.045):g} m³/m²")
        L.add(*et, "estrutura_forma", "Forma de pilares, vigas e cintas", "m²", conc * _f(v, "estrutura_forma", 12),
              org_fund, f"{conc:.2f} m³ × {_f(v, 'estrutura_forma', 12):g} m²/m³")
        L.add(*et, "estrutura_aco", "Armação de pilares, vigas e cintas", "kg", conc * _f(v, "estrutura_aco", 90),
              org_fund, f"{conc:.2f} m³ × {_f(v, 'estrutura_aco', 90):g} kg/m³")
    elif est == "alvenaria_estrutural":
        L.add(*et, "graute", "Graute e armadura vertical (alvenaria estrutural)", "m³", area * 0.012, PARAMETRICA,
              "0,012 m³ por m² construído")
        L.add(*et, "cinta", "Cintas de amarração", "m", paredes * 2, CALCULADA, "paredes × 2 níveis")
    elif est in ("parede_concreto", "metalica", "steel_frame"):
        L.add(*et, f"sistema_{est}", {"parede_concreto": "Paredes de concreto (sistema completo)",
                                      "metalica": "Estrutura metálica", "steel_frame": "Steel frame"}[est],
              "m²", area, PARAMETRICA, "por m² construído (detalhar em fase futura)")

    laje = e.get("laje")
    if laje and laje != "sem_laje":
        esp = _f(v, "laje_esp", 0.12)
        nome = {"trelicada_eps": "Laje treliçada com EPS", "trelicada_ceramica": "Laje treliçada com lajota cerâmica",
                "macica": "Laje maciça", "pre_moldada": "Laje pré-moldada / alveolar"}[laje]
        if laje == "macica":
            L.add(*et, "laje_macica_concreto", f"{nome} - concreto", "m³", area * esp, CALCULADA,
                  f"{area:g} m² × {esp:g} m")
            L.add(*et, "laje_macica_forma", f"{nome} - forma", "m²", area, CALCULADA, "área construída")
            L.add(*et, "laje_macica_aco", f"{nome} - armação", "kg", area * esp * 80, PARAMETRICA,
                  "80 kg/m³")
        else:
            L.add(*et, f"laje_{laje}", f"{nome} (e = {esp:g} m)", "m²", area, CALCULADA, "área construída")

    # 05 Vedações
    et = ("05", "Vedações")
    ved = e.get("vedacao")
    area_parede = paredes * pd - vaos
    nomes_ved = {"ceramico_9": "Alvenaria de bloco cerâmico 9 cm", "ceramico_14": "Alvenaria de bloco cerâmico 14 cm",
                 "concreto_14": "Alvenaria de bloco de concreto 14 cm", "macico": "Alvenaria de tijolo maciço"}
    if ved in nomes_ved:
        L.add(*et, f"alvenaria_{ved}", nomes_ved[ved], "m²", area_parede, CALCULADA,
              f"({perim:g} + {internas:g}) m × {pd:g} m − {vaos:.2f} m² de vãos")
    elif ved == "drywall":
        L.add(*et, "alvenaria_ceramico_14", "Alvenaria externa de bloco cerâmico 14 cm", "m²",
              perim * pd - vaos_janelas - _f(v, "portas_ext") * 0.9 * 2.1, CALCULADA, "paredes externas − vãos")
        L.add(*et, "drywall", "Parede drywall interna", "m²", internas * pd - _f(v, "portas_int") * 0.8 * 2.1,
              CALCULADA, "paredes internas − portas")
    L.add(*et, "vergas", "Vergas e contravergas", "m", (_f(v, "portas_int") + _f(v, "portas_ext")) * 1.3
          + vaos_janelas / 1.2 * 2 * 1.6, PARAMETRICA, "vãos + 0,30 m de transpasse")

    # 06 Cobertura
    et = ("06", "Cobertura")
    cob = e.get("cobertura")
    if cob == "laje_impermeabilizada":
        L.add(*et, "impermeabilizacao_laje", "Impermeabilização de laje (manta)", "m²", area * 1.1, CALCULADA,
              "área + 10% de rodapés")
    elif cob:
        beiral = _f(v, "beiral", 0.6)
        inc = _f(v, "inclinacao", 35) / 100
        proj = area + perim * beiral + 4 * beiral * beiral
        real = proj * math.sqrt(1 + inc * inc)
        nomes_tel = {"ceramica": "Telhamento com telha cerâmica", "fibrocimento": "Telhamento com telha de fibrocimento",
                     "metalica": "Telhamento com telha metálica", "termoacustica": "Telhamento com telha termoacústica"}
        org_cob = CALCULADA if "cobertura" in projetos else PARAMETRICA
        L.add(*et, f"telhado_{cob}", nomes_tel[cob], "m²", real, org_cob,
              f"projeção {proj:.2f} m² × fator de inclinação {math.sqrt(1 + inc * inc):.3f}")
        etel = e.get("estrutura_telhado")
        if etel and etel != "existente":
            L.add(*et, f"estrutura_telhado_{etel}", f"Estrutura do telhado ({etel.replace('_', ' ')})", "m²", real,
                  org_cob, "mesma área do telhamento")
        L.add(*et, "cumeeira", "Cumeeira", "m", math.sqrt(area) * 1.2, PARAMETRICA, "≈ 1,2 × √área")
        L.add(*et, "rufos_calhas", "Rufos e calhas", "m", perim * 0.5, PARAMETRICA, "50% do perímetro")

    # 07 Instalações
    et = ("07", "Instalações")
    p_ele = _f(v, "pontos_eletricos") or math.ceil(area * 0.6)
    p_agua = _f(v, "pontos_agua") or banheiros * 5 + 3
    p_esg = _f(v, "pontos_esgoto") or banheiros * 4 + 2
    org_ele = DIGITADA if _f(v, "pontos_eletricos") else PARAMETRICA
    org_agua = DIGITADA if _f(v, "pontos_agua") else PARAMETRICA
    org_esg = DIGITADA if _f(v, "pontos_esgoto") else PARAMETRICA
    L.add(*et, "ponto_eletrico", "Ponto elétrico (tomada/iluminação) completo", "un", p_ele, org_ele,
          "informado" if org_ele == DIGITADA else f"0,6 × {area:g} m²")
    L.add(*et, "quadro_distribuicao", "Quadro de distribuição com disjuntores", "un", 1, PARAMETRICA, "1 por unidade")
    nomes_en = {"mono": "monofásico", "bi": "bifásico", "tri": "trifásico", "subterranea": "com entrada subterrânea"}
    if e.get("energia") in nomes_en:
        L.add(*et, "padrao_entrada", f"Padrão de entrada de energia {nomes_en[e['energia']]}", "un", 1, CALCULADA,
              "1 por unidade")
    L.add(*et, "ponto_agua", "Ponto de água fria completo", "un", p_agua, org_agua,
          "informado" if org_agua == DIGITADA else f"5 × {banheiros:g} banheiro(s) + 3")
    L.add(*et, "ponto_esgoto", "Ponto de esgoto completo", "un", p_esg, org_esg,
          "informado" if org_esg == DIGITADA else f"4 × {banheiros:g} banheiro(s) + 2")
    L.add(*et, "caixa_dagua", f"Caixa d'água {int(_f(v, 'caixa_dagua_l', 500))} L instalada", "un", 1, DIGITADA,
          "1 unidade")
    L.add(*et, "louca_vaso", "Vaso sanitário com caixa acoplada", "un", banheiros, CALCULADA, "1 por banheiro")
    L.add(*et, "louca_lavatorio", "Lavatório com torneira", "un", banheiros, CALCULADA, "1 por banheiro")
    L.add(*et, "pia_cozinha", "Bancada/pia de cozinha com torneira", "un", 1, PARAMETRICA, "1 por unidade")
    L.add(*et, "tanque", "Tanque de lavar com torneira", "un", 1, PARAMETRICA, "1 por unidade")
    esg = e.get("esgoto")
    if esg == "fossa_sumidouro":
        L.add(*et, "fossa_sumidouro", "Fossa séptica + sumidouro", "un", 1, CALCULADA, "1 conjunto")
    elif esg == "fossa_filtro":
        L.add(*et, "fossa_filtro", "Fossa + filtro anaeróbio + sumidouro", "un", 1, CALCULADA, "1 conjunto")
    elif esg == "ete":
        L.add(*et, "ete", "ETE compacta", "un", 1, CALCULADA, "1 unidade")
    elif esg == "rede":
        L.add(*et, "ligacao_esgoto", "Ligação à rede pública de esgoto", "un", 1, CALCULADA, "1 ligação")

    # 08 Revestimentos e acabamentos
    et = ("08", "Revestimentos e acabamentos")
    face_int = (2 * internas + perim) * pd - vaos * 1.5
    face_ext = perim * (pd + 0.3) - vaos / 2
    rev = e.get("revestimento_parede")
    if rev in ("chapisco_reboco", "chapisco_emboco_reboco", "gesso", "reboco_ext"):
        tem_int = rev != "reboco_ext"
        L.add(*et, "chapisco", "Chapisco", "m²", (face_int if tem_int else 0) + face_ext, CALCULADA,
              "faces internas + externas − vãos")
        if rev == "gesso":
            L.add(*et, "gesso_parede", "Revestimento de gesso liso (internas)", "m²",
                  face_int - _f(v, "area_molhada_parede"), CALCULADA, "faces internas − áreas cerâmicas")
            L.add(*et, "reboco", "Reboco / massa única (externas e áreas molhadas)", "m²",
                  face_ext + _f(v, "area_molhada_parede"), CALCULADA, "faces externas + áreas molhadas")
        else:
            if rev == "chapisco_emboco_reboco":
                L.add(*et, "emboco", "Emboço", "m²", (face_int if tem_int else 0) + face_ext, CALCULADA,
                      "faces internas + externas − vãos")
            L.add(*et, "reboco", "Reboco / massa única", "m²", (face_int if tem_int else 0) + face_ext, CALCULADA,
                  "faces internas + externas − vãos")
    L.add(*et, "ceramica_parede", "Revestimento cerâmico de parede", "m²", _f(v, "area_molhada_parede"), DIGITADA,
          "informado")
    L.add(*et, "contrapiso", "Contrapiso", "m²", area_util, CALCULADA, "área útil")
    nomes_piso = {"ceramico": "Piso cerâmico", "porcelanato": "Piso porcelanato", "vinilico": "Piso vinílico",
                  "cimentado": "Piso cimentado", "laminado": "Piso laminado"}
    if e.get("piso") in nomes_piso:
        L.add(*et, f"piso_{e['piso']}", nomes_piso[e["piso"]], "m²", area_util, CALCULADA, "área útil")
        if e["piso"] != "cimentado":
            L.add(*et, "rodape", "Rodapé", "m", 2 * internas + perim - _f(v, "portas_int") * 1.6
                  - _f(v, "portas_ext") * 0.9, CALCULADA, "perímetro dos ambientes − portas")
    nomes_forro = {"pvc": "Forro de PVC", "gesso": "Forro de gesso", "laje_pintada": "Reboco de teto (laje)",
                   "madeira": "Forro de madeira"}
    if e.get("forro") in nomes_forro:
        L.add(*et, f"forro_{e['forro']}", nomes_forro[e["forro"]], "m²", area_util, CALCULADA, "área útil")
    pint = e.get("pintura")
    if pint and pint != "sem_pintura":
        area_pint_int = max(face_int - _f(v, "area_molhada_parede"), 0)
        L.add(*et, "selador", "Fundo selador", "m²", area_pint_int + face_ext, CALCULADA, "faces pintadas")
        if pint == "massa_acrilica":
            L.add(*et, "massa_corrida", "Massa corrida (internas)", "m²", area_pint_int, CALCULADA, "faces internas")
        L.add(*et, "pintura_interna", "Pintura " + ("látex PVA" if pint == "latex_pva" else "acrílica") + " interna",
              "m²", area_pint_int, CALCULADA, "faces internas − cerâmica")
        if pint == "textura_ext":
            L.add(*et, "textura_externa", "Textura acrílica externa", "m²", face_ext, CALCULADA, "faces externas")
        else:
            L.add(*et, "pintura_externa", "Pintura acrílica externa", "m²", face_ext, CALCULADA, "faces externas")
        if e.get("forro") in ("laje_pintada", "gesso"):
            L.add(*et, "pintura_teto", "Pintura de teto", "m²", area_util, CALCULADA, "área útil")
    L.add(*et, "soleiras_peitoris", "Soleiras e peitoris", "m", _f(v, "portas_ext") * 0.9 + vaos_janelas / 1.2,
          PARAMETRICA, "largura das portas externas e janelas")

    # 09 Esquadrias
    et = ("09", "Esquadrias")
    port = e.get("portas")
    nomes_port = {"madeira_semi_oca": "madeira semioca", "madeira_macica": "madeira maciça", "aluminio": "alumínio",
                  "aco": "aço", "pvc": "PVC"}
    if port in nomes_port:
        L.add(*et, "porta_interna", f"Porta interna de {nomes_port[port]} 80×210 com batente e ferragens", "un",
              _f(v, "portas_int"), DIGITADA, "contagem")
        L.add(*et, "porta_externa", f"Porta externa de {nomes_port[port]} 90×210 com batente e ferragens", "un",
              _f(v, "portas_ext"), DIGITADA, "contagem")
    jan = e.get("janelas")
    nomes_jan = {"aluminio": "alumínio com vidro", "aco": "aço", "pvc": "PVC", "madeira": "madeira",
                 "vidro_temperado": "vidro temperado"}
    if jan in nomes_jan:
        L.add(*et, f"janela_{jan}", f"Janela de {nomes_jan[jan]}", "m²", vaos_janelas, DIGITADA, "área de janelas")

    # 10 Serviços complementares
    et = ("10", "Serviços complementares")
    ext = e.get("calcada") or []
    if "calcada_perimetro" in ext:
        L.add(*et, "calcada", "Calçada de proteção (largura 0,60 m)", "m²", (perim + 2.4) * 0.6, CALCULADA,
              "(perímetro + cantos) × 0,60 m")
    if "passeio_publico" in ext:
        L.add(*et, "passeio", "Passeio público (largura 1,50 m)", "m²", _f(v, "frente_terreno") * 1.5, CALCULADA,
              "testada × 1,50 m")
    if "ligacoes" in ext:
        L.add(*et, "ligacao_agua", "Ligação definitiva de água", "un", 1, CALCULADA, "1 ligação")
    if "limpeza_final" in ext:
        L.add(*et, "limpeza_final", "Limpeza final da obra", "m²", area, CALCULADA, "área construída")

    return L.itens
