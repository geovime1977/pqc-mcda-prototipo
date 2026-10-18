# pqc-mcda-prototipo

Protótipo do framework proposto para o Mestrado em Sistemas e Computação (PGSC/IME, 2027.1):
priorizar a migração para criptografia pós-quântica como problema de decisão multicritério.

**Dados 100% sintéticos.** Nenhum inventário real, documento classificado ou sistema em operação.

## O que faz

1. **Pesos (SAPEVO-M):** três especialistas sintéticos comparam os critérios em escala ordinal
   de −3 a +3. Os pesos individuais são somados e normalizados.
2. **Margem de Mosca:** para cada cenário, `max(0, x + y − z)`, com x = anos de sigilo,
   y = anos de migração, z = horizonte da ameaça quântica (parâmetro).
3. **ELECTRE III** com pseudo-critérios, veto na margem de Mosca, destilação de Roy e pré-ordem
   final por interseção (mantém incomparabilidades).
4. **Linha de base:** soma ponderada com os mesmos pesos e dados.
5. **Comparação:** ordem por soma ponderada × ELECTRE sem veto × ELECTRE com veto, e os pares
   cuja relação o veto altera.
6. **Auditoria:** cada execução registra SHA-256 da entrada, parâmetros e versões em
   `auditoria/execucoes.jsonl`.

## Critérios (protótipo)

| Critério | Sentido | Origem |
|---|---|---|
| margem_mosca | max | QS01, QS02; Mosca (2018) |
| sensibilidade (1–5) | max | QS02 |
| exposicao (1–5) | max | QS01, QS03 |
| criticidade (1–5) | max | sistemas críticos |
| complexidade (1–5) | min | QS05, QS06 |
| custo_bytes | min | tamanhos nominais FIPS 203/204/205 |

`custo_bytes` usa os tamanhos nominais dos padrões (ML-KEM-768: 1184 + 1088 B;
ML-DSA-65: 1952 + 3309 B; SLH-DSA-SHA2-128s: 32 + 7856 B). Na dissertação serão
substituídos por medições com a liboqs.

## Como rodar

```bash
uv venv -p 3.12 .venv && uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m pytest -q
.venv/bin/python run.py --z 12
.venv/bin/streamlit run app.py --server.port 8517
```

## Dados de entrada

O painel aceita upload na barra lateral (e oferece modelos para baixar):

- **Cenários — CSV**, uma linha por cenário: `id, descricao, uso_criptografico, algoritmo_alvo,
  sigilo_anos, migracao_anos, sensibilidade, exposicao, criticidade, complexidade, custo_bytes`.
  Notas de 1 a 5; anos e bytes não negativos; `id` único.
- **Especialistas — JSON**: `{"criterios": [...6 critérios na ordem acima...], "matrizes":
  {"E1": [[0, 2, ...], ...], ...}}`, uma matriz 6×6 antissimétrica em −3..+3 por especialista.

Entrada inválida é recusada com a lista de erros. Sem upload, usa `dados/cenarios.csv` e
`dados/especialistas.json`.

### Conjuntos de teste

```bash
.venv/bin/python gerar_dados.py --n 30 --seed 1    # dados/exemplos/cenarios_30.csv
.venv/bin/python gerar_dados.py --n 100 --seed 2   # dados/exemplos/cenarios_100.csv
```

`dados/exemplos/` também traz `cenarios_invalido.csv` (id repetido, nota 7, ano negativo) e
`especialistas_divergentes.json` (painel que privilegia viabilidade em vez de exposição).

## Limitações conhecidas

- A destilação do ELECTRE III segue Roy (1978) e Figueira, Mousseau e Roy (2005), e a matriz de
  credibilidade coincide com o pyDecision 5.1.8 em 300 instâncias. A destilação ainda precisa
  ser conferida contra um exemplo numérico publicado.
- A agregação de grupo do SAPEVO-M precisa ser conferida contra as fórmulas de Gomes, Santos e
  Moreira (2020).
- Limiares (q, p, v) são ilustrativos; na dissertação serão calibrados e submetidos a análise
  de sensibilidade.
- Ainda sem: medição liboqs, relatórios PDF/XLSX. O gerador de cenários é simples (faixas uniformes por tipo de uso).
