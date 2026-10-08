from pathlib import Path

import pytest
import yaml

from planejamento.cadastros.schemas import BOM, PRODUTO, VENDAS
from planejamento.io.csv_loader import carregar_csv, converter_numero


@pytest.mark.parametrize(
    "texto, virgula, esperado",
    [
        ("1.234,56", True, 1234.56),
        ("1234,56", True, 1234.56),
        ("23.700", True, 23700.0),
        ("1234.56", False, 1234.56),
        ("1,234.56", False, 1234.56),
        ("1.234.567", False, 1234567.0),
        ("R$ 10,50", True, 10.5),
    ],
)
def test_converter_numero(texto, virgula, esperado):
    assert converter_numero(texto, virgula) == pytest.approx(esperado)


def _csv(tmp_path: Path, nome: str, conteudo: str) -> Path:
    p = tmp_path / nome
    p.write_text(conteudo, encoding="utf-8")
    return p


def test_coluna_mista_e_corrigida(tmp_path):
    # Bug conhecido: a mesma coluna chega com vírgula e com ponto
    arq = _csv(
        tmp_path,
        "bom.csv",
        "sku_pai;componente;quantidade_por_unidade;unidade\n"
        "PA1;INT1;1,05;L\n"
        "PA2;INT1;1.250,5;L\n"
        "PA3;INT2;2;L\n",
    )
    df, rel = carregar_csv(arq, BOM)
    assert rel.ok, rel.erros
    assert df["quantidade_por_unidade"].tolist() == pytest.approx([1.05, 1250.5, 2.0])
    assert rel.correcoes_decimais == 2


def test_separador_virgula_e_ponto_decimal(tmp_path):
    arq = _csv(
        tmp_path,
        "vendas.csv",
        "data,documento,sku,cliente,quantidade_l,valor_brl\n"
        "2026-09-01,NF1,PA1,C1,200.5,1500.75\n",
    )
    df, rel = carregar_csv(arq, VENDAS)
    assert rel.ok, rel.erros
    assert df.loc[0, "quantidade_l"] == pytest.approx(200.5)


def test_erros_sao_reportados(tmp_path):
    arq = _csv(
        tmp_path,
        "produto.csv",
        "sku;descricao;marca;familia;tipo\n"
        "PA1;Óleo 15W40;YPF;motor;acabado\n"
        "PA1;Duplicado;Marca X;motor;acabado\n"
        ";Sem código;Valvoline;motor;xyz\n",
    )
    _, rel = carregar_csv(arq, PRODUTO)
    mensagens = {(p.linha, p.coluna, p.mensagem.split(" [")[0]) for p in rel.erros}
    assert (3, "marca", "valor fora da lista") in mensagens
    assert (4, "sku", "valor obrigatório vazio") in mensagens
    assert (4, "tipo", "valor fora da lista") in mensagens
    assert any(p.mensagem == "chave duplicada" for p in rel.erros)


def test_coluna_obrigatoria_ausente(tmp_path):
    arq = _csv(tmp_path, "bom.csv", "sku_pai;componente\nPA1;INT1\n")
    _, rel = carregar_csv(arq, BOM)
    assert not rel.ok
    assert {p.coluna for p in rel.erros} == {"quantidade_por_unidade", "unidade"}


def test_parametros_regras_usiquimica():
    cfg = yaml.safe_load(Path("config/parametros.yaml").read_text(encoding="utf-8"))
    assert cfg["mps"]["bulk"]["volume_litros"] == 23700
    assert cfg["mps"]["bulk"]["produzir_bulk_inteiro"] is True
    assert cfg["mps"]["semanas_congeladas"] == 2
    assert cfg["industrializadores"]["E8"]["sequencia_cores_obrigatoria"] == [["Amarelo dourado", "Vermelho"]]
