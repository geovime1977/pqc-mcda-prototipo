# Diretiva de Contexto Global

Sempre consulte as configurações, comandos e subagentes definidos em `~/.claude/` antes de executar tarefas complexas.

---

# CLAUDE.md — pqc-mcda-prototipo

## Sobre este projeto

- **O que faz:** protótipo do framework do mestrado PGSC/IME — SAPEVO-M → ELECTRE III (veto de Mosca) × soma ponderada para priorizar migração PQC; dados sintéticos
- **Stack:** Python 3.12, numpy, pandas, Streamlit (porta 8517), pytest
- **Como rodar:** `.venv/bin/python run.py --z 12` ou `.venv/bin/streamlit run app.py --server.port 8517`
- **Status:** em-desenvolvimento

## Localização

- **Local:** `~/projetos/pqc-mcda-prototipo/`
- **Backup:** `onedrive-eixoestrategico10:repos/pqc-mcda-prototipo`
- **Nota no vault:** `01 - Profissional/Projetos/Mestrados RJ 2027/IME-PGSC-2027/`

## Comandos principais

```bash
# Instalar
uv venv -p 3.12 .venv && uv pip install --python .venv/bin/python -e ".[dev]"

# Rodar
.venv/bin/python -m pytest -q && .venv/bin/python run.py --z 12

# Backup
rclone copy . onedrive-eixoestrategico10:repos/pqc-mcda-prototipo --exclude '.venv/**'
```

## Governança e riscos

Regras globais: `~/.claude/rules/seguranca.md`. Checklist: `Checklist de Segurança e Governança de Projeto` no vault.

- **Dono do projeto:** Geovane Virmecati
- **Dados sensíveis que entram:** nenhum — só cenários e especialistas sintéticos; proibido inserir inventário real ou dado classificado
- **Segredos:** só em `.env` (no `.gitignore`); conferir com `git ls-files | grep -iE '\.env|secret|\.key|\.pem'`
- **Dependências:** rodar `pip-audit` ou `npm audit` antes de entregar
- **Saída com consequência legal ou financeira:** checagem humana em 100%
- **Última verificação:** 2026-10-18

## Contexto relevante

- Proposta: vault `IME-PGSC-2027/06-Proposta-de-Estudo-A4-MCDA-PQC.md`
- `src/pqc_mcda/electre.py` deriva de `~/.claude/skills/po-sobreclassificacao/scripts/electre.py` (corrigido em 2026-10-18 para destilação de Roy + interseção); manter os dois em sincronia
- Pendências de validação: destilação contra exemplo publicado; agregação SAPEVO-M contra Gomes et al. (2020)

<!-- Links para notas do vault relacionadas -->
<!-- Variáveis de ambiente necessárias -->
<!-- Dependências externas -->
