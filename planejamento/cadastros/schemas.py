"""Esquemas dos cadastros mestres e das cargas transacionais.

Cada esquema define as colunas obrigatórias, o tipo esperado e as regras
simples de validação. A especificação completa está em docs/ESPECIFICACAO.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Coluna:
    nome: str
    tipo: str  # "texto", "numero", "inteiro", "data"
    obrigatoria: bool = True
    minimo: float | None = None
    valores_permitidos: tuple[str, ...] | None = None


@dataclass(frozen=True)
class Esquema:
    nome: str
    descricao: str
    chave: tuple[str, ...]
    colunas: tuple[Coluna, ...] = field(default_factory=tuple)

    @property
    def nomes(self) -> list[str]:
        return [c.nome for c in self.colunas]


PRODUTO = Esquema(
    nome="produto",
    descricao="SKU acabado ou intermediário",
    chave=("sku",),
    colunas=(
        Coluna("sku", "texto"),
        Coluna("descricao", "texto"),
        Coluna("marca", "texto", valores_permitidos=("YPF", "Valvoline", "Outra")),
        Coluna("familia", "texto"),
        Coluna("tipo", "texto", valores_permitidos=("acabado", "intermediario", "materia_prima", "embalagem")),
        Coluna("volume_embalagem_l", "numero", obrigatoria=False, minimo=0),
        Coluna("cor", "texto", obrigatoria=False),
        Coluna("classe_abc", "texto", obrigatoria=False, valores_permitidos=("A", "B", "C")),
        Coluna("classe_xyz", "texto", obrigatoria=False, valores_permitidos=("X", "Y", "Z")),
    ),
)

CLIENTE = Esquema(
    nome="cliente",
    descricao="Cliente e canal; classe A é previsto em SKU x cliente, demais em SKU x canal",
    chave=("cliente",),
    colunas=(
        Coluna("cliente", "texto"),
        Coluna("nome", "texto"),
        Coluna("canal", "texto"),
        Coluna("regiao", "texto", obrigatoria=False),
        Coluna("kam", "texto", obrigatoria=False),
        Coluna("classe_abc", "texto", valores_permitidos=("A", "B", "C")),
    ),
)

BOM = Esquema(
    nome="bom",
    descricao="Lista de materiais: pai -> componente com quantidade por unidade do pai",
    chave=("sku_pai", "componente"),
    colunas=(
        Coluna("sku_pai", "texto"),
        Coluna("componente", "texto"),
        Coluna("quantidade_por_unidade", "numero", minimo=0),
        Coluna("unidade", "texto", valores_permitidos=("L", "kg", "un")),
    ),
)

FATOR_CONVERSAO = Esquema(
    nome="fator_conversao",
    descricao="Conversão PA -> intermediário (IQT); E8 usa 1:1",
    chave=("industrializador", "sku_acabado", "sku_intermediario"),
    colunas=(
        Coluna("industrializador", "texto", valores_permitidos=("E8", "IQT")),
        Coluna("sku_acabado", "texto"),
        Coluna("sku_intermediario", "texto"),
        Coluna("fator", "numero", minimo=0),
    ),
)

RECURSO = Esquema(
    nome="recurso",
    descricao="Linhas de envase e tanques por industrializador",
    chave=("industrializador", "recurso"),
    colunas=(
        Coluna("industrializador", "texto", valores_permitidos=("E8", "IQT")),
        Coluna("recurso", "texto"),
        Coluna("tipo", "texto", valores_permitidos=("linha", "tanque")),
        Coluna("capacidade", "numero", minimo=0),
        Coluna("unidade_capacidade", "texto", valores_permitidos=("L/dia", "L", "un/dia")),
    ),
)

SETUP_COR = Esquema(
    nome="setup_cor",
    descricao="Matriz de setup por troca de cor em cada linha (minutos)",
    chave=("recurso", "cor_de", "cor_para"),
    colunas=(
        Coluna("recurso", "texto"),
        Coluna("cor_de", "texto"),
        Coluna("cor_para", "texto"),
        Coluna("setup_min", "numero", minimo=0),
        Coluna("permitido", "texto", valores_permitidos=("sim", "nao")),
    ),
)

MATERIAL_COMPRADO = Esquema(
    nome="material_comprado",
    descricao="Parâmetros de compra por material e fornecedor",
    chave=("material", "fornecedor"),
    colunas=(
        Coluna("material", "texto"),
        Coluna("fornecedor", "texto"),
        Coluna("lead_time_dias", "inteiro", minimo=0),
        Coluna("lote_minimo", "numero", minimo=0),
        Coluna("multiplo", "numero", minimo=0),
        Coluna("moeda", "texto", valores_permitidos=("BRL", "USD")),
        Coluna("preferencial", "texto", valores_permitidos=("sim", "nao")),
    ),
)

VENDAS = Esquema(
    nome="vendas",
    descricao="Vendas faturadas (histórico da previsão)",
    chave=("data", "sku", "cliente", "documento"),
    colunas=(
        Coluna("data", "data"),
        Coluna("documento", "texto"),
        Coluna("sku", "texto"),
        Coluna("cliente", "texto"),
        Coluna("quantidade_l", "numero"),
        Coluna("valor_brl", "numero", obrigatoria=False),
    ),
)

ESTOQUE = Esquema(
    nome="estoque",
    descricao="Posição de estoque por SKU, local e lote",
    chave=("data", "sku", "local", "lote"),
    colunas=(
        Coluna("data", "data"),
        Coluna("sku", "texto"),
        Coluna("local", "texto"),
        Coluna("lote", "texto", obrigatoria=False),
        Coluna("quantidade", "numero", minimo=0),
    ),
)

APONTAMENTO = Esquema(
    nome="apontamento",
    descricao="Apontamento diário de produção enviado pelos industrializadores",
    chave=("industrializador", "ordem", "data", "lote"),
    colunas=(
        Coluna("industrializador", "texto", valores_permitidos=("E8", "IQT")),
        Coluna("data", "data"),
        Coluna("ordem", "texto"),
        Coluna("sku", "texto"),
        Coluna("linha", "texto"),
        Coluna("lote", "texto"),
        Coluna("quantidade_produzida", "numero", minimo=0),
        Coluna("refugo", "numero", obrigatoria=False, minimo=0),
        Coluna("motivo_parada", "texto", obrigatoria=False),
    ),
)

TODOS: dict[str, Esquema] = {
    e.nome: e
    for e in (
        PRODUTO, CLIENTE, BOM, FATOR_CONVERSAO, RECURSO, SETUP_COR,
        MATERIAL_COMPRADO, VENDAS, ESTOQUE, APONTAMENTO,
    )
}
