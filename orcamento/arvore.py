"""Árvore de perguntas do jogo de seleção, carregada de arquivos JSON em dados/."""
from __future__ import annotations

import json
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent / "dados"
OUTRO = "__outro__"


def carregar(nome: str = "arvore_residencial_terrea.json") -> dict:
    return json.loads((PASTA / nome).read_text(encoding="utf-8"))


def visivel(pergunta: dict, escolhas: dict) -> bool:
    cond = pergunta.get("mostrar_se")
    return not cond or escolhas.get(cond["pergunta"]) in cond["em"]


def campos_ativos(pergunta: dict, escolha) -> list[dict]:
    escolhidos = escolha if isinstance(escolha, list) else [escolha]
    return [c for c in pergunta.get("campos", []) if not c.get("quando") or set(c["quando"]) & set(escolhidos)]


def premissas(arvore: dict, escolhas: dict, valores: dict, outros: dict) -> list[dict]:
    """Lista legível de todas as respostas, para o memorial de premissas."""
    linhas = []
    for p in arvore["perguntas"]:
        if not visivel(p, escolhas):
            continue
        rotulos = {o["valor"]: o["rotulo"] for o in p["opcoes"]}
        esc = escolhas.get(p["id"])
        if p["opcoes"]:
            if esc == OUTRO:
                resp = f"Outro: {outros.get(p['id'], '')}"
            elif isinstance(esc, list):
                resp = ", ".join(rotulos.get(x, x) for x in esc) or "nenhum"
            else:
                resp = rotulos.get(esc, "—")
            linhas.append({"Etapa": p["etapa"], "Item": p["pergunta"], "Resposta": resp})
        for c in campos_ativos(p, esc):
            linhas.append({"Etapa": p["etapa"], "Item": c["rotulo"], "Resposta": f"{valores.get(c['id'], c['padrao'])}"})
    return linhas
