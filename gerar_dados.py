"""Gera conjuntos sintéticos para testar o protótipo.

uso: .venv/bin/python gerar_dados.py [--n 30] [--seed 1] [--pasta dados/exemplos]

Saídas: cenarios_<n>.csv, cenarios_invalido.csv, especialistas_divergentes.json
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

# tipo de uso -> (algoritmo, bytes adicionais por operação, faixas típicas)
# bytes: ML-KEM-768 1184+1088; ML-DSA-65 1952+3309; SLH-DSA-SHA2-128s 32+7856 (FIPS 203/204/205)
TIPOS = {
    "enlace VPN/IPsec": ("ML-KEM-768", 2272, dict(sig=(10, 30), mig=(3, 8), sens=(4, 5), exp=(4, 5), crit=(4, 5), comp=(3, 5))),
    "rádio/cifrador embarcado": ("ML-KEM-768", 2272, dict(sig=(15, 30), mig=(7, 12), sens=(4, 5), exp=(3, 5), crit=(4, 5), comp=(4, 5))),
    "sessão TLS de aplicação": ("ML-KEM-768", 2272, dict(sig=(1, 10), mig=(1, 4), sens=(1, 4), exp=(4, 5), crit=(1, 4), comp=(1, 3))),
    "assinatura de firmware": ("SLH-DSA-SHA2-128s", 7888, dict(sig=(1, 5), mig=(5, 10), sens=(2, 4), exp=(2, 4), crit=(4, 5), comp=(3, 5))),
    "certificação digital (PKI)": ("ML-DSA-65", 5261, dict(sig=(5, 20), mig=(4, 8), sens=(3, 5), exp=(3, 4), crit=(4, 5), comp=(4, 5))),
    "armazenamento cifrado": ("ML-KEM-768", 1088, dict(sig=(20, 50), mig=(2, 5), sens=(3, 5), exp=(1, 3), crit=(2, 4), comp=(1, 3))),
    "mensageria assinada": ("ML-KEM-768 + ML-DSA-65", 4397, dict(sig=(5, 15), mig=(2, 5), sens=(2, 4), exp=(3, 5), crit=(2, 4), comp=(2, 4))),
    "telemetria/IoT": ("ML-KEM-768", 2272, dict(sig=(0, 3), mig=(3, 8), sens=(1, 2), exp=(3, 5), crit=(1, 3), comp=(2, 4))),
}


def cenarios(n: int, rng: np.random.Generator) -> pd.DataFrame:
    linhas = []
    nomes = list(TIPOS)
    for i in range(n):
        tipo = nomes[rng.integers(len(nomes))]
        alg, b, f = TIPOS[tipo]
        r = lambda k: int(rng.integers(f[k][0], f[k][1] + 1))
        linhas.append({"id": f"S{i + 1:03d}", "descricao": f"{tipo} #{i + 1}",
                       "uso_criptografico": tipo, "algoritmo_alvo": alg,
                       "sigilo_anos": r("sig"), "migracao_anos": r("mig"),
                       "sensibilidade": r("sens"), "exposicao": r("exp"),
                       "criticidade": r("crit"), "complexidade": r("comp"),
                       "custo_bytes": b})
    return pd.DataFrame(linhas)


def especialistas_divergentes() -> dict:
    crits = ["margem_mosca", "sensibilidade", "exposicao", "criticidade", "complexidade", "custo_bytes"]
    # importância latente (0-3); o E3 privilegia viabilidade, o que força divergência no painel
    lat = {"E1_criptografia": [3.0, 2.0, 2.5, 1.5, 0.5, 1.0],
           "E2_operacoes": [1.5, 1.5, 1.0, 3.0, 2.0, 0.5],
           "E3_gestao_orcamento": [1.0, 1.0, 0.5, 2.0, 3.0, 2.5]}
    mats = {k: [[int(np.clip(round(v[i] - v[j]), -3, 3)) for j in range(6)] for i in range(6)]
            for k, v in lat.items()}
    return {"descricao": "Três especialistas SINTÉTICOS com opiniões divergentes.",
            "criterios": crits, "matrizes": mats}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--pasta", default="dados/exemplos")
    a = ap.parse_args()
    pasta = Path(a.pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(a.seed)

    df = cenarios(a.n, rng)
    df.to_csv(pasta / f"cenarios_{a.n}.csv", index=False)

    ruim = cenarios(5, rng)
    ruim.loc[1, "sensibilidade"] = 7
    ruim.loc[2, "id"] = ruim.loc[0, "id"]
    ruim.loc[3, "migracao_anos"] = -2
    ruim.to_csv(pasta / "cenarios_invalido.csv", index=False)

    (pasta / "especialistas_divergentes.json").write_text(
        json.dumps(especialistas_divergentes(), ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"gerados em {pasta}/: cenarios_{a.n}.csv, cenarios_invalido.csv, especialistas_divergentes.json")


if __name__ == "__main__":
    main()
