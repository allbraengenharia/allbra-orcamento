"""Banco de dados local (SQLite): empresa, tabelas de preço, vínculos e orçamentos salvos."""
from __future__ import annotations

import json
import unicodedata
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

CAMINHO = Path(__file__).resolve().parent.parent / "dados" / "allbra.db"

EMPRESA_PADRAO = {
    "nome_fantasia": "Allbra Engenharia",
    "razao_social": "Allbra Construtora e Incorporadora Ltda",
    "cnpj": "28.481.350/0001-36",
    "cidade": "Aparecida de Goiânia",
    "uf": "GO",
    "responsavel_tecnico": "Octtávio de Morais Lopes",
    "regime_tributario": "Simples Nacional",
    "regime_encargos": "INSS padrão (SINAPI-GO não desonerado)",
    "encargos_horista_pct": 0.0,
    "bdi_pct": 25.0,
    "distancia_obra_fora_km": 80.0,
}


def conectar() -> sqlite3.Connection:
    CAMINHO.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(CAMINHO)
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS config (chave TEXT PRIMARY KEY, valor TEXT);
        CREATE TABLE IF NOT EXISTS precos (
            fonte TEXT, uf TEXT, data_base TEXT, regime TEXT, codigo TEXT,
            descricao TEXT, unidade TEXT, preco REAL, tipo TEXT,
            PRIMARY KEY (fonte, uf, data_base, regime, codigo)
        );
        CREATE TABLE IF NOT EXISTS vinculos (servico TEXT PRIMARY KEY, fonte TEXT, codigo TEXT);
        CREATE TABLE IF NOT EXISTS orcamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, criado TEXT, dados TEXT
        );
        """
    )
    return con


def empresa() -> dict:
    with conectar() as con:
        row = con.execute("SELECT valor FROM config WHERE chave = 'empresa'").fetchone()
    dados = dict(EMPRESA_PADRAO)
    if row:
        dados.update(json.loads(row[0]))
    return dados


def salvar_empresa(dados: dict):
    with conectar() as con:
        con.execute("INSERT OR REPLACE INTO config VALUES ('empresa', ?)", (json.dumps(dados, ensure_ascii=False),))


def importar_precos(df: pd.DataFrame, fonte: str, uf: str, data_base: str, regime: str, tipo: str) -> int:
    """df com colunas codigo, descricao, unidade, preco."""
    df = df.dropna(subset=["codigo", "preco"]).copy()
    df["codigo"] = df["codigo"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    df = df[df["codigo"] != ""]
    linhas = [
        (fonte, uf, data_base, regime, r.codigo, str(r.descricao), str(r.unidade), float(r.preco), tipo)
        for r in df.itertuples()
    ]
    with conectar() as con:
        con.executemany("INSERT OR REPLACE INTO precos VALUES (?,?,?,?,?,?,?,?,?)", linhas)
    return len(linhas)


def resumo_bases() -> pd.DataFrame:
    with conectar() as con:
        return pd.read_sql(
            "SELECT fonte, uf, data_base, regime, tipo, COUNT(*) AS itens FROM precos "
            "GROUP BY fonte, uf, data_base, regime, tipo ORDER BY fonte, data_base DESC", con)


PALAVRAS_VAZIAS = {"DE", "DA", "DO", "DAS", "DOS", "E", "COM", "EM", "A", "O", "PARA", "POR"}


def _sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode().upper()


def buscar_precos(texto: str, fonte: str | None = None, limite: int = 50) -> pd.DataFrame:
    """Busca sem diferenciar acentos e maiúsculas; todas as palavras precisam aparecer (ou o código exato)."""
    sql = "SELECT fonte, uf, data_base, regime, codigo, descricao, unidade, preco FROM precos"
    args: list = []
    if fonte:
        sql += " WHERE fonte = ?"
        args.append(fonte)
    with conectar() as con:
        df = pd.read_sql(sql + " ORDER BY data_base DESC", con, params=args)
    palavras = [w for w in _sem_acento(texto).split() if w not in PALAVRAS_VAZIAS]
    if not palavras or df.empty:
        return df.head(0)
    desc = df["descricao"].map(_sem_acento)
    filtro = pd.Series(True, index=df.index)
    for w in palavras:
        filtro &= desc.str.contains(w, regex=False) | (df["codigo"] == w)
    return df[filtro].head(limite)


def vinculos() -> dict[str, tuple[str, str]]:
    with conectar() as con:
        return {s: (f, c) for s, f, c in con.execute("SELECT servico, fonte, codigo FROM vinculos")}


def salvar_vinculo(servico: str, fonte: str, codigo: str):
    with conectar() as con:
        con.execute("INSERT OR REPLACE INTO vinculos VALUES (?,?,?)", (servico, fonte, codigo))


def remover_vinculo(servico: str):
    with conectar() as con:
        con.execute("DELETE FROM vinculos WHERE servico = ?", (servico,))


def preco_vigente(fonte: str, codigo: str, regime: str | None = None) -> tuple[float, str, str] | None:
    """Preço mais recente de um código: (preço, descrição, data-base)."""
    sql = "SELECT preco, descricao, data_base FROM precos WHERE fonte = ? AND codigo = ?"
    args = [fonte, codigo]
    if regime:
        sql += " AND regime = ?"
        args.append(regime)
    sql += " ORDER BY data_base DESC LIMIT 1"
    with conectar() as con:
        row = con.execute(sql, args).fetchone()
    if not row and regime:
        return preco_vigente(fonte, codigo)
    return row


def salvar_orcamento(nome: str, dados: dict, id_: int | None = None) -> int:
    texto = json.dumps(dados, ensure_ascii=False)
    with conectar() as con:
        if id_:
            con.execute("UPDATE orcamentos SET nome = ?, dados = ? WHERE id = ?", (nome, texto, id_))
            return id_
        cur = con.execute("INSERT INTO orcamentos (nome, criado, dados) VALUES (?,?,?)",
                          (nome, datetime.now().isoformat(timespec="minutes"), texto))
        return cur.lastrowid


def listar_orcamentos() -> pd.DataFrame:
    with conectar() as con:
        return pd.read_sql("SELECT id, nome, criado FROM orcamentos ORDER BY id DESC", con)


def carregar_orcamento(id_: int) -> dict | None:
    with conectar() as con:
        row = con.execute("SELECT dados FROM orcamentos WHERE id = ?", (id_,)).fetchone()
    return json.loads(row[0]) if row else None
