"""Leitura de planilhas de preço (SINAPI, GOINFRA, tabela própria) com detecção automática do cabeçalho.

Os layouts das planilhas oficiais mudam com o tempo, então o importador procura a linha de cabeçalho
e sugere as colunas; o operador confirma ou corrige na tela antes de gravar.
"""
from __future__ import annotations

import re
import unicodedata

import pandas as pd


def _norm(texto) -> str:
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", texto).strip().upper()


def abas(arquivo) -> list[str]:
    if getattr(arquivo, "name", "").lower().endswith(".csv"):
        return ["(CSV)"]
    return pd.ExcelFile(arquivo).sheet_names


def ler(arquivo, aba: str) -> pd.DataFrame:
    """Lê a aba e usa como cabeçalho a primeira linha que tenha 'CODIGO' e 'DESCRI'."""
    if aba == "(CSV)":
        bruto = pd.read_csv(arquivo, header=None, sep=None, engine="python", dtype=str, encoding_errors="replace")
    else:
        bruto = pd.read_excel(arquivo, sheet_name=aba, header=None, dtype=str)
    linha_cab = 0
    for i in range(min(len(bruto), 40)):
        valores = " | ".join(_norm(x) for x in bruto.iloc[i].tolist() if pd.notna(x))
        if "CODIGO" in valores and "DESCRI" in valores:
            linha_cab = i
            break
    cab = []
    for j, x in enumerate(bruto.iloc[linha_cab].tolist()):
        nome = str(x).strip() if pd.notna(x) else f"coluna_{j + 1}"
        while nome in cab:
            nome += "_"
        cab.append(nome)
    df = bruto.iloc[linha_cab + 1:].copy()
    df.columns = cab
    return df.dropna(how="all").reset_index(drop=True)


def sugerir_colunas(colunas: list[str], uf: str = "GO") -> dict[str, str | None]:
    n = {c: _norm(c) for c in colunas}

    def primeira(*testes):
        for c, t in n.items():
            if any(teste(t) for teste in testes):
                return c
        return None

    return {
        "codigo": primeira(lambda t: t.startswith("CODIGO") and "AGRUP" not in t and "CLASS" not in t,
                           lambda t: "CODIGO" in t),
        "descricao": primeira(lambda t: t.startswith("DESCRI")),
        "unidade": primeira(lambda t: t.startswith("UNID"), lambda t: t in ("UN", "UND")),
        "preco": primeira(lambda t: t == uf.upper(), lambda t: "CUSTO TOTAL" in t,
                          lambda t: "PRECO" in t or "CUSTO" in t, lambda t: "VALOR" in t),
    }


def converter_numero(serie: pd.Series) -> pd.Series:
    def conv(x):
        if pd.isna(x):
            return None
        s = str(x).strip().replace("R$", "").replace(" ", "")
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None
    return serie.map(conv)


def preparar(df: pd.DataFrame, mapa: dict[str, str]) -> pd.DataFrame:
    saida = pd.DataFrame({
        "codigo": df[mapa["codigo"]],
        "descricao": df[mapa["descricao"]],
        "unidade": df[mapa["unidade"]] if mapa.get("unidade") else "",
        "preco": converter_numero(df[mapa["preco"]]),
    })
    return saida.dropna(subset=["codigo", "preco"])
