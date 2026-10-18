"""Pesos dos critérios pelo SAPEVO-M (Gomes, Santos e Moreira, 2020), versão em grupo.

Cada especialista preenche uma matriz ordinal antissimétrica em {-3..+3}. Para cada um,
o peso de um critério é a soma da sua linha, normalizada por min-max em [0,01; 1]. Os vetores
dos especialistas são somados e renormalizados para somar 1.
"""
from __future__ import annotations

import numpy as np

ESCALA_MIN, ESCALA_MAX = -3, 3


def validar_matriz(mat: np.ndarray, nome: str) -> None:
    if mat.shape[0] != mat.shape[1]:
        raise ValueError(f"{nome}: matriz não é quadrada {mat.shape}")
    if mat.min() < ESCALA_MIN or mat.max() > ESCALA_MAX:
        raise ValueError(f"{nome}: valores fora de [{ESCALA_MIN}, {ESCALA_MAX}]")
    if not np.array_equal(mat, -mat.T):
        raise ValueError(f"{nome}: matriz não é antissimétrica")


def pesos_especialista(mat: np.ndarray) -> np.ndarray:
    somas = mat.sum(axis=1).astype(float)
    lo, hi = somas.min(), somas.max()
    if hi == lo:
        return np.full(len(somas), 1.0 / len(somas))
    v = 0.01 + (somas - lo) / (hi - lo) * 0.99
    return v / v.sum()


def pesos_grupo(matrizes: dict[str, list[list[int]]]) -> tuple[np.ndarray, dict]:
    individuais = {}
    for nome, m in matrizes.items():
        mat = np.array(m, dtype=int)
        validar_matriz(mat, nome)
        individuais[nome] = pesos_especialista(mat)
    soma = np.sum(list(individuais.values()), axis=0)
    return soma / soma.sum(), {k: v.tolist() for k, v in individuais.items()}
