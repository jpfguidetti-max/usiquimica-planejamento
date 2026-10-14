# Usiquímica — App de Planejamento Integrado

Ciclo completo de planejamento em uma só base: previsão de demanda, consenso S&OP,
MPS, MRP e acompanhamento da produção nos industrializadores E8 e IQT.
Referências funcionais: Plannera (demanda e consenso) e Pyplan (MPS, MRP e execução).

## Status: Fase 1 — Planejamento de demanda

A entrega segue o fluxo do planejamento: demanda → MPS → RCCP → MRP (decidido em 14/10/2026).

| Fase | Conteúdo | Portão para avançar | Status |
| --- | --- | --- | --- |
| 0 | Cargas CSV com validação, testes e CI | Vendas, produtos e clientes carregados sem erro | Concluída |
| 1 | Planejamento de demanda estatístico e painel de acurácia | Backtest de 12 meses com erro menor que o método de referência | **Próxima** |
| 2 | MPS, RCCP e MRP (migra as regras da ferramenta atual) | Plano igual ao da planilha por 4 ciclos semanais | A fazer |
| 3 | Execução (S&OE): apontamentos e aderência | Apontamento diário dos dois industrializadores | A fazer |
| 4 | Consenso S&OP, Supabase Pro e integração com o ERP | — | A fazer |

## Arquitetura (decidida em 08/10/2026)

- **Este repositório (privado):** código, testes e o app publicado no GitHub Pages.
- **Dados:** nunca neste repositório. Até a Fase 3, em um repositório privado separado;
  na Fase 4, no Supabase Pro. No GitHub Pro o site do Pages é público, por isso o
  `.gitignore` bloqueia a pasta `dados/` e planilhas.

## Estrutura

```
config/parametros.yaml        Regras de negócio (bulk 23.700 L, cores, congelamento etc.)
modelos_cadastro/*.csv        Cabeçalhos dos 10 arquivos de carga (separador ;)
planejamento/cadastros/       Esquemas e regras de validação de cada cadastro
planejamento/io/csv_loader.py Carga de CSV com correção automática de decimal (ponto/vírgula)
planejamento/validar.py       Valida uma pasta inteira de CSVs
tests/                        Testes automáticos (rodam no GitHub Actions a cada push)
```

## Como validar uma carga de dados

1. Copie os modelos de `modelos_cadastro/` e preencha (Excel → salvar como CSV).
2. Coloque os arquivos em uma pasta, com os mesmos nomes (`produto.csv`, `bom.csv`...).
3. Rode:

```
pip install -e ".[dev]"
python -m planejamento.validar caminho/da/pasta
```

O relatório mostra, por arquivo, linhas lidas, números corrigidos e cada erro com
linha, coluna e motivo. A saída é 1 quando há erro.

## Regra de decimal

Decidida por coluna: se algum valor usa vírgula decimal (`1.234,56`), o ponto vira
separador de milhar na coluna toda. Atenção: um valor isolado como `1.234`, numa
coluna sem nenhuma vírgula, é lido como 1,234 (padrão americano).
