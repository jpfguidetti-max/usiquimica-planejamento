"""Carga de CSV com validação e correção automática do separador decimal.

Problema conhecido: arquivos chegam com números em formatos misturados
("1.234,56", "1234.56", "1234,56"). A correção é decidida por coluna:
se algum valor da coluna usa vírgula decimal, o ponto é tratado como
separador de milhar em toda a coluna; caso contrário, o ponto é decimal.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from planejamento.cadastros.schemas import Esquema

_VIRGULA_DECIMAL = re.compile(r"^-?[\d.]*,\d+$")
_PONTO_MILHAR_BR = re.compile(r"^-?\d{1,3}(\.\d{3})+$")


@dataclass
class Problema:
    linha: int  # linha no arquivo (1 = cabeçalho)
    coluna: str
    valor: str
    mensagem: str


@dataclass
class Relatorio:
    arquivo: str
    esquema: str
    linhas_lidas: int = 0
    correcoes_decimais: int = 0
    erros: list[Problema] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.erros

    def resumo(self) -> str:
        status = "OK" if self.ok else f"{len(self.erros)} erro(s)"
        return (
            f"{self.arquivo} [{self.esquema}]: {self.linhas_lidas} linhas, "
            f"{self.correcoes_decimais} número(s) corrigido(s), {status}"
        )


def _detectar_separador(texto: str) -> str:
    amostra = texto[:5000]
    try:
        return csv.Sniffer().sniff(amostra, delimiters=";,\t").delimiter
    except csv.Error:
        return ";" if amostra.count(";") >= amostra.count(",") else ","


def _coluna_usa_virgula_decimal(valores: list[str]) -> bool:
    return any(_VIRGULA_DECIMAL.match(v) for v in valores if v)


def converter_numero(valor: str, virgula_decimal: bool) -> float:
    """Converte texto em número segundo a convenção decidida para a coluna."""
    v = valor.strip().replace(" ", "").replace("R$", "")
    if virgula_decimal:
        v = v.replace(".", "").replace(",", ".")
    elif "," in v and "." in v:
        # padrão americano 1,234.56
        v = v.replace(",", "")
    elif _PONTO_MILHAR_BR.match(v) and v.count(".") > 1:
        # 1.234.567 sem decimais
        v = v.replace(".", "")
    return float(v)


def converter_data(valor: str) -> date:
    v = valor.strip()
    for formato in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(v, formato).date()
        except ValueError:
            continue
    raise ValueError(f"data em formato não reconhecido: {valor!r}")


def carregar_csv(caminho: str | Path, esquema: Esquema) -> tuple[pd.DataFrame, Relatorio]:
    caminho = Path(caminho)
    bruto = caminho.read_bytes()
    try:
        texto = bruto.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = bruto.decode("latin-1")

    sep = _detectar_separador(texto)
    df = pd.read_csv(io.StringIO(texto), sep=sep, dtype=str, keep_default_na=False)
    df.columns = [c.strip().lower() for c in df.columns]

    rel = Relatorio(arquivo=caminho.name, esquema=esquema.nome, linhas_lidas=len(df))

    faltando = [c.nome for c in esquema.colunas if c.obrigatoria and c.nome not in df.columns]
    for nome in faltando:
        rel.erros.append(Problema(1, nome, "", "coluna obrigatória ausente"))
    if faltando:
        return df, rel

    for c in esquema.colunas:
        if c.nome not in df.columns:
            df[c.nome] = ""
    df = df[esquema.nomes].copy()

    for col in esquema.colunas:
        serie = df[col.nome].astype(str).str.strip()
        convertidos: list[object] = []
        virgula = col.tipo in ("numero", "inteiro") and _coluna_usa_virgula_decimal(serie.tolist())

        for i, valor in enumerate(serie.tolist()):
            linha = i + 2
            if valor == "":
                if col.obrigatoria:
                    rel.erros.append(Problema(linha, col.nome, valor, "valor obrigatório vazio"))
                convertidos.append(None)
                continue
            try:
                if col.tipo in ("numero", "inteiro"):
                    try:
                        numero = converter_numero(valor, virgula)
                    except ValueError:
                        raise ValueError("não é um número válido") from None
                    if numero != _numero_ingenuo(valor):
                        rel.correcoes_decimais += 1
                    if col.tipo == "inteiro":
                        if numero != int(numero):
                            raise ValueError("esperado número inteiro")
                        numero = int(numero)
                    if col.minimo is not None and numero < col.minimo:
                        raise ValueError(f"menor que o mínimo {col.minimo}")
                    convertidos.append(numero)
                elif col.tipo == "data":
                    convertidos.append(converter_data(valor))
                else:
                    if col.valores_permitidos and valor not in col.valores_permitidos:
                        raise ValueError(f"valor fora da lista {list(col.valores_permitidos)}")
                    convertidos.append(valor)
            except ValueError as exc:
                rel.erros.append(Problema(linha, col.nome, valor, str(exc)))
                convertidos.append(None)
        df[col.nome] = convertidos

    duplicadas = df.duplicated(subset=list(esquema.chave), keep="first")
    for i in df.index[duplicadas]:
        chave = ", ".join(str(df.at[i, k]) for k in esquema.chave)
        rel.erros.append(Problema(int(i) + 2, "/".join(esquema.chave), chave, "chave duplicada"))

    return df, rel


def _numero_ingenuo(valor: str) -> float | None:
    """Leitura 'ingênua' (padrão Python) só para contar correções aplicadas."""
    try:
        return float(valor.strip())
    except ValueError:
        return None
