"""Montagem do orçamento: preços pelos vínculos, BDI, totais e curva ABC."""
from __future__ import annotations

import io

import pandas as pd

from . import db
from .quantitativos import Item


def montar(itens: list[Item], bdi_pct: float) -> pd.DataFrame:
    vinc = db.vinculos()
    linhas = []
    for it in itens:
        d = it.dict()
        d["fonte"], d["codigo"], d["preco_unit"], d["data_base"] = "", "", None, ""
        if it.servico in vinc:
            fonte, codigo = vinc[it.servico]
            achado = db.preco_vigente(fonte, codigo)
            if achado:
                d.update(fonte=fonte, codigo=codigo, preco_unit=round(achado[0], 2), data_base=achado[2])
        linhas.append(d)
    df = pd.DataFrame(linhas)
    if df.empty:
        return df
    df["preco_unit"] = pd.to_numeric(df["preco_unit"], errors="coerce")
    df["total"] = (df["quantidade"] * df["preco_unit"].fillna(0)).round(2)
    df["preco_unit_bdi"] = (df["preco_unit"] * (1 + bdi_pct / 100)).round(2)
    df["total_bdi"] = (df["quantidade"] * df["preco_unit_bdi"].fillna(0)).round(2)
    return df


def resumo_etapas(df: pd.DataFrame) -> pd.DataFrame:
    r = df.groupby(["etapa"], sort=False).agg(itens=("servico", "count"), custo_direto=("total", "sum"),
                                              total_bdi=("total_bdi", "sum")).reset_index()
    tot = r["total_bdi"].sum()
    r["pct"] = (r["total_bdi"] / tot * 100).round(2) if tot else 0
    return r


def curva_abc(df: pd.DataFrame, lim_a: float = 50, lim_b: float = 80) -> pd.DataFrame:
    c = df[df["total_bdi"] > 0][["eap", "descricao", "unidade", "quantidade", "preco_unit_bdi", "total_bdi"]]
    c = c.sort_values("total_bdi", ascending=False).reset_index(drop=True)
    if c.empty:
        return c
    tot = c["total_bdi"].sum()
    c["pct"] = (c["total_bdi"] / tot * 100).round(2)
    c["pct_acumulado"] = c["pct"].cumsum().round(2)
    anterior = c["pct_acumulado"].shift(fill_value=0)
    c["classe"] = ["A" if a < lim_a else "B" if a < lim_b else "C" for a in anterior]
    return c


def excel(df: pd.DataFrame, etapas: pd.DataFrame, abc: pd.DataFrame, cabecalho: dict, premissas: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        pd.DataFrame(list(cabecalho.items()), columns=["Campo", "Valor"]).to_excel(xw, sheet_name="Capa", index=False)
        etapas.to_excel(xw, sheet_name="Resumo por etapa", index=False)
        df.to_excel(xw, sheet_name="Orçamento analítico", index=False)
        abc.to_excel(xw, sheet_name="Curva ABC", index=False)
        premissas.to_excel(xw, sheet_name="Premissas", index=False)
        for ws in xw.book.worksheets:
            for col in ws.columns:
                largura = max(len(str(c.value or "")) for c in col[:200])
                ws.column_dimensions[col[0].column_letter].width = min(max(10, largura + 2), 70)
    return buf.getvalue()
