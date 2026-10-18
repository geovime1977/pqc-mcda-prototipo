"""Fluxo do protótipo: pesos SAPEVO-M -> margem de Mosca -> ELECTRE III (com e sem veto)
e soma ponderada com os mesmos pesos -> comparação -> registro de auditoria."""
from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import __version__
from .electre import electre_iii
from .sapevo import pesos_grupo
from .soma_ponderada import soma_ponderada

RAIZ = Path(__file__).resolve().parents[2]

# Critério -> (coluna na tabela, sentido). "max" = quanto maior, mais urgente migrar.
CRITERIOS = {
    "margem_mosca": "max",
    "sensibilidade": "max",
    "exposicao": "max",
    "criticidade": "max",
    "complexidade": "min",
    "custo_bytes": "min",
}

LIMIARES_PADRAO = {
    "margem_mosca": {"q": 1.0, "p": 3.0, "v": 8.0},
    "sensibilidade": {"q": 0.0, "p": 1.0, "v": None},
    "exposicao": {"q": 0.0, "p": 1.0, "v": None},
    "criticidade": {"q": 0.0, "p": 1.0, "v": None},
    "complexidade": {"q": 0.0, "p": 1.0, "v": None},
    "custo_bytes": {"q": 500.0, "p": 2000.0, "v": None},
}


def carregar(dir_dados: Path = RAIZ / "dados") -> tuple[pd.DataFrame, dict]:
    cen = pd.read_csv(dir_dados / "cenarios.csv")
    esp = json.loads((dir_dados / "especialistas.json").read_text(encoding="utf-8"))
    return cen, esp


def validar(cen: pd.DataFrame, esp: dict) -> list[str]:
    erros = []
    obrig = ["id", "descricao", "sigilo_anos", "migracao_anos", "sensibilidade",
             "exposicao", "criticidade", "complexidade", "custo_bytes"]
    faltam = [c for c in obrig if c not in cen.columns]
    if faltam:
        return [f"colunas ausentes: {faltam}"]
    if cen["id"].duplicated().any():
        erros.append("ids de cenário repetidos")
    if cen[obrig[2:]].isna().any().any():
        erros.append("há valores vazios nos critérios")
    for c in ["sensibilidade", "exposicao", "criticidade", "complexidade"]:
        fora = cen[(cen[c] < 1) | (cen[c] > 5)]
        if len(fora):
            erros.append(f"{c} fora da escala 1-5 em {fora['id'].tolist()}")
    if (cen[["sigilo_anos", "migracao_anos", "custo_bytes"]] < 0).any().any():
        erros.append("valores negativos em anos ou bytes")
    if not isinstance(esp.get("matrizes"), dict) or not esp["matrizes"]:
        erros.append("especialistas.json sem o bloco 'matrizes'")
    if esp.get("criterios") != list(CRITERIOS):
        erros.append(f"especialistas.json deve listar os critérios na ordem {list(CRITERIOS)}")
    return erros


def executar(cen: pd.DataFrame, esp: dict, z: float,
             limiares: dict | None = None) -> dict:
    erros = validar(cen, esp)
    if erros:
        raise ValueError("; ".join(erros))
    limiares = {**LIMIARES_PADRAO, **(limiares or {})}
    tab = cen.copy()
    # Só a parte positiva conta: folga de quem ainda não está exposto não dá prioridade.
    tab["margem_bruta"] = tab["sigilo_anos"] + tab["migracao_anos"] - z
    tab["margem_mosca"] = tab["margem_bruta"].clip(lower=0)
    nomes = tab["id"].tolist()
    crits = list(CRITERIOS)
    sentidos = [CRITERIOS[c] for c in crits]
    X = tab[crits].to_numpy(float)

    pesos, individuais = pesos_grupo(esp["matrizes"])
    lim = [limiares[c] for c in crits]
    lim_sem_veto = [{**d, "v": None} for d in lim]

    com_veto = electre_iii(X, nomes, sentidos, pesos, lim)
    sem_veto = electre_iii(X, nomes, sentidos, pesos, lim_sem_veto)
    base = soma_ponderada(X, nomes, sentidos, pesos)

    pos = lambda r: {x["alternativa"]: x["posicao"] for x in r}
    p_cv, p_sv, p_sp = pos(com_veto["ranking"]), pos(sem_veto["ranking"]), pos(base)
    linha = tab.set_index("id")
    comparacao = [{"cenario": n,
                   "margem_bruta": float(linha.loc[n, "margem_bruta"]),
                   "margem_mosca": float(linha.loc[n, "margem_mosca"]),
                   "soma_ponderada": p_sp[n], "electre_sem_veto": p_sv[n],
                   "electre_com_veto": p_cv[n]} for n in nomes]
    rel = lambda r: {(x["a"], x["b"]): x["relacao"] for x in r["relacoes"]}
    r_sv, r_cv = rel(sem_veto), rel(com_veto)
    pares_veto = [{"a": a, "b": b, "sem_veto": r_sv[(a, b)], "com_veto": r_cv[(a, b)]}
                  for (a, b) in r_sv if r_sv[(a, b)] != r_cv[(a, b)]]

    entrada = {"cenarios": cen.to_dict(orient="records"), "especialistas": esp,
               "z": z, "limiares": limiares}
    hash_entrada = hashlib.sha256(
        json.dumps(entrada, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {
        "auditoria": {"quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                      "versao_prototipo": __version__,
                      "python": platform.python_version(),
                      "numpy": np.__version__, "pandas": pd.__version__,
                      "sha256_entrada": hash_entrada},
        "parametros": {"z_horizonte_anos": z, "limiares": limiares},
        "pesos": {c: round(float(w), 6) for c, w in zip(crits, pesos)},
        "pesos_por_especialista": individuais,
        "soma_ponderada": base,
        "electre_sem_veto": sem_veto,
        "electre_com_veto": com_veto,
        "comparacao": comparacao,
        "pares_alterados_pelo_veto": pares_veto,
    }


def registrar(resultado: dict, arquivo: Path = RAIZ / "auditoria" / "execucoes.jsonl") -> None:
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    with arquivo.open("a", encoding="utf-8") as f:
        f.write(json.dumps(resultado, ensure_ascii=False) + "\n")
