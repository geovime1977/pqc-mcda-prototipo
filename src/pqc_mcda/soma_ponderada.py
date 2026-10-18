"""Linha de base compensatória: soma ponderada com normalização min-max por critério."""
from __future__ import annotations

import numpy as np

from .electre import orientar


def soma_ponderada(X: np.ndarray, nomes: list[str], sentidos: list[str],
                   pesos: np.ndarray) -> list[dict]:
    Y = orientar(X, sentidos)
    amp = Y.max(axis=0) - Y.min(axis=0)
    N = (Y - Y.min(axis=0)) / np.where(amp > 0, amp, 1.0)
    score = N @ pesos
    ordem = np.argsort(-score, kind="stable")
    return [{"posicao": k + 1, "alternativa": nomes[i], "score": round(float(score[i]), 6)}
            for k, i in enumerate(ordem)]
