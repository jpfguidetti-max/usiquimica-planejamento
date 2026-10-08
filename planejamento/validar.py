"""Valida todos os CSVs de uma pasta de dados contra os esquemas.

Uso: python -m planejamento.validar <pasta_de_dados>
Cada arquivo deve se chamar <esquema>.csv (ex.: produto.csv, bom.csv).
Sai com código 1 se houver erro, para o GitHub Actions bloquear a carga.
"""

from __future__ import annotations

import sys
from pathlib import Path

from planejamento.cadastros.schemas import TODOS
from planejamento.io.csv_loader import carregar_csv


def main(pasta: str) -> int:
    base = Path(pasta)
    arquivos = sorted(base.glob("*.csv"))
    if not arquivos:
        print(f"Nenhum CSV encontrado em {base}")
        return 1

    falhou = False
    for arq in arquivos:
        esquema = TODOS.get(arq.stem)
        if esquema is None:
            print(f"IGNORADO {arq.name}: nenhum esquema com esse nome ({', '.join(TODOS)})")
            continue
        _, rel = carregar_csv(arq, esquema)
        print(rel.resumo())
        for p in rel.erros[:50]:
            print(f"  linha {p.linha}, coluna {p.coluna}: {p.mensagem} (valor: {p.valor!r})")
        if len(rel.erros) > 50:
            print(f"  ... e mais {len(rel.erros) - 50} erro(s)")
        falhou = falhou or not rel.ok
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "dados"))
