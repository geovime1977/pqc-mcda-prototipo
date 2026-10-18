# Tutorial do protótipo de priorização da migração pós-quântica

Geovane Virmecati · Protótipo da proposta de estudo para o Mestrado em Sistemas e Computação (PGSC/IME), 2027.1 · Dados sintéticos

## 1. O que é

É um programa de apoio à decisão. Ele recebe uma lista de sistemas que usam criptografia e devolve a ordem em que esses sistemas deveriam migrar para a criptografia pós-quântica, com a justificativa de cada posição.

O programa não decide sozinho. Ele organiza a opinião de especialistas e os dados de cada sistema de forma que qualquer pessoa possa refazer a conta e entender por que um sistema ficou à frente de outro.

## 2. Para que serve

Para responder a uma pergunta prática: **se não dá para trocar toda a criptografia de uma vez, por onde começar?**

Uma organização grande tem centenas de sistemas que dependem de criptografia: enlaces de rede, rádios, certificados digitais, arquivos cifrados, assinaturas de software. Cada troca custa dinheiro, tempo e risco operacional. O protótipo ajuda a definir a ordem e a defender essa ordem diante de quem aprova o orçamento.

## 3. Por que é necessário

**A ameaça.** Um computador quântico de escala suficiente quebra a criptografia de chave pública usada hoje (RSA, Diffie-Hellman, curvas elípticas), pelo algoritmo de Shor (1994). Em 2024 o NIST publicou os substitutos: ML-KEM (FIPS 203), ML-DSA (FIPS 204) e SLH-DSA (FIPS 205).

**O risco que já existe.** Um adversário pode copiar hoje uma comunicação cifrada e guardá-la até conseguir decifrá-la. Esse modelo se chama "coletar agora, decifrar depois" (*Harvest Now, Decrypt Later*).

**A conta de Mosca (2018).** Sejam:

- x = por quantos anos o dado precisa continuar secreto;
- y = quantos anos leva a migração do sistema;
- z = quantos anos faltam para existir o computador quântico capaz de quebrar a criptografia.

Se x + y > z, o dado já está exposto, mesmo que a máquina ainda não exista. Exemplo: segredo de 25 anos, migração de 7 anos e ameaça em 15 anos. Como 25 + 7 = 32 é maior que 15, o sistema já está atrasado.

**O enquadramento.** O OWASP Quantum Top 10 (versão preliminar de 2026) organiza os riscos da migração em sete categorias (QS01 a QS07). O NCSC britânico fixou marcos para 2028, 2031 e 2035. Os prazos existem; falta um método para escolher a ordem.

## 4. Como funciona

O protótipo segue cinco passos.

**Passo 1. Pesos dos critérios (SAPEVO-M).** Cada especialista compara os critérios dois a dois em escala de −3 a +3 ("este critério é muito mais importante que aquele" = +3). O método SAPEVO-M (Gomes, Santos e Moreira, 2020) transforma essas comparações em pesos e junta a opinião do grupo.

**Passo 2. Margem de Mosca.** Para cada sistema, calcula max(0, x + y − z). Só conta quem já está exposto; uma folga grande não dá prioridade a quem ainda está seguro.

**Passo 3. Comparação dos sistemas (ELECTRE III).** O método ELECTRE III (Roy, 1978) compara os sistemas aos pares, critério a critério. Duas características importam aqui:

- **Veto.** Se um sistema tem margem de Mosca muito maior que outro, o segundo não pode passar à frente apenas por ser mais barato de migrar. Um ponto forte em custo não compensa uma exposição grave.
- **Incomparabilidade.** Quando um sistema é melhor em uns critérios e pior em outros, sem vantagem clara, o método declara os dois incomparáveis em vez de inventar uma ordem. Essa informação vai para o decisor.

**Passo 4. Linha de base (soma ponderada).** Os mesmos pesos e dados entram numa soma ponderada simples, em que um critério bom compensa um ruim. Como só muda a forma de agregar, a diferença entre as duas ordens mostra o efeito do veto.

**Passo 5. Estabilidade e registro.** O protótipo repete a análise para vários valores de z e mede o quanto a ordem muda. Cada execução fica registrada com uma impressão digital (SHA-256) dos dados de entrada, o que permite refazê-la depois.

## 5. Critérios usados no protótipo

| Critério | Sentido | Origem |
|---|---|---|
| Margem de Mosca | quanto maior, mais urgente | QS01, QS02; Mosca (2018) |
| Sensibilidade dos dados (1 a 5) | quanto maior, mais urgente | QS02 |
| Exposição do uso atual (1 a 5) | quanto maior, mais urgente | QS01, QS03 |
| Criticidade do sistema (1 a 5) | quanto maior, mais urgente | sistemas críticos |
| Complexidade da migração (1 a 5) | quanto maior, menos urgente | QS05, QS06 |
| Custo em bytes do novo algoritmo | quanto maior, menos urgente | FIPS 203, 204 e 205 |

## 6. Onde está e como instalar

- Código: github.com/geovime1977/pqc-mcda-prototipo
- Requisitos: Python 3.12 e o gerenciador uv.

```bash
git clone https://github.com/geovime1977/pqc-mcda-prototipo
cd pqc-mcda-prototipo
uv venv -p 3.12 .venv && uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m pytest -q
.venv/bin/streamlit run app.py --server.port 8517
```

O painel abre no navegador em http://localhost:8517.

## 7. Passo a passo no painel

1. **Dados de entrada** (barra lateral). Envie um CSV de cenários e, se quiser, um JSON de especialistas. Sem envio, o painel usa os 10 cenários de exemplo. Os arquivos de teste estão em `dados/exemplos/`.
2. **Parâmetros.** Ajuste z (horizonte da ameaça), v (veto da margem de Mosca) e a faixa de z para a sensibilidade.
3. **Executar.** Clique em **Executar análise**. Se mudar dados ou parâmetros depois, o painel avisa que é preciso executar de novo.
4. **Resultados**, em cinco abas:
   - *Resumo*: leitura em linguagem simples e os botões de relatório (PDF, planilha e JSON).
   - *Ordenações*: posição de cada sistema na soma ponderada, no ELECTRE III sem veto e com veto.
   - *Sensibilidade a z*: quanto a ordem muda quando o horizonte da ameaça varia.
   - *Dados e pesos*: pesos do grupo e de cada especialista.
   - *Auditoria*: impressão digital da entrada, versões e parâmetros.

## 8. Como ler o resultado

- **Posição (camada).** No ELECTRE III, a posição é uma camada. Sistemas na mesma camada estão empatados ou são incomparáveis. A camada 1 é a de migração mais urgente.
- **Incomparáveis.** São pares em que o método não força ordem. A escolha entre eles é do decisor, de preferência com mais informação.
- **Pares alterados pelo veto.** Mostram onde o veto mudou a relação entre dois sistemas. É o efeito que a pesquisa pretende medir.
- **Estabilidade.** Valor de 0 a 1 (correlação de Spearman entre z vizinhos). Perto de 1, a ordem pouco muda com a incerteza sobre z.

## 9. Formato dos arquivos

**Cenários (CSV)**, uma linha por sistema:

```
id,descricao,uso_criptografico,algoritmo_alvo,sigilo_anos,migracao_anos,sensibilidade,exposicao,criticidade,complexidade,custo_bytes
S01,VPN entre postos de comando,troca de chaves,ML-KEM-768,25,6,5,5,5,4,2272
```

**Especialistas (JSON)**, uma matriz 6 × 6 por especialista, na ordem dos critérios da seção 5. A matriz é antissimétrica: se a linha i, coluna j vale +2, a linha j, coluna i vale −2.

O painel recusa arquivos inválidos e lista os erros (id repetido, nota fora de 1 a 5, valor negativo, matriz fora do padrão).

## 10. Limitações

- Todos os dados são sintéticos. A aplicação com dados reais cabe aos órgãos competentes, em ambiente autorizado.
- Os limiares (q, p, v) são ilustrativos e serão calibrados na pesquisa.
- O custo em bytes usa os tamanhos nominais dos padrões; na dissertação será medido com a biblioteca liboqs.
- A matriz de credibilidade do ELECTRE III foi conferida contra o pyDecision 5.1.8 em 300 casos. A destilação e a agregação do SAPEVO-M ainda serão conferidas contra exemplos publicados.

## 11. Referências

GOMES, L. F. A. M.; SANTOS, M.; MOREIRA, M. A. L. SAPEVO-M: método de ordenação multicritério ordinal em grupo. *Pesquisa Operacional*, 2020.

MOSCA, M. Cybersecurity in an era with quantum computers: will we be ready? *IEEE Security & Privacy*, v. 16, n. 5, p. 38–41, 2018.

NCSC. *Timelines for migration to post-quantum cryptography*. London, 2025.

NIST. *FIPS 203, FIPS 204 e FIPS 205*. Gaithersburg, 2024.

OWASP. *Top 10 for Quantum Security Risks (2026)*: versão preliminar. OWASP Quantum Security Project, 2026.

ROY, B. ELECTRE III: un algorithme de classements fondé sur une représentation floue des préférences en présence de critères multiples. *Cahiers du CERO*, v. 20, n. 1, p. 3–24, 1978.

SHOR, P. W. Algorithms for quantum computation: discrete logarithms and factoring. In: *Proceedings of the 35th Annual Symposium on Foundations of Computer Science*. IEEE, 1994.
