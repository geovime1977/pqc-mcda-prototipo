"""ELECTRE III (Roy, 1978) com pseudo-critérios, veto, destilação e pré-ordem por interseção.

Derivado de po-sobreclassificacao/scripts/electre.py (mesmo autor), revisão de 2026-10-18.
A matriz de credibilidade foi conferida contra o pyDecision 5.1.8 em 300 instâncias aleatórias.
"""
from __future__ import annotations

import numpy as np


def orientar(X: np.ndarray, sentidos: list[str]) -> np.ndarray:
    Y = X.astype(float).copy()
    for j, s in enumerate(sentidos):
        if s == "min":
            Y[:, j] = -Y[:, j]
    return Y


def credibilidade(X: np.ndarray, sentidos: list[str], pesos: np.ndarray,
                  limiares: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    """limiares[j] = {"q": ..., "p": ..., "v": ... ou None} na escala original do critério."""
    Y = orientar(X, sentidos)
    m, n = Y.shape
    c_par = np.zeros((n, m, m))
    d_par = np.zeros((n, m, m))
    for j in range(n):
        q, p, v = limiares[j]["q"], max(limiares[j]["p"], limiares[j]["q"]), limiares[j].get("v")
        for a in range(m):
            for b in range(m):
                if a == b:
                    continue
                d = Y[b, j] - Y[a, j]
                if d <= q:
                    c_par[j, a, b] = 1.0
                elif d < p:
                    c_par[j, a, b] = (p - d) / (p - q)
                if v is not None and d > p:
                    d_par[j, a, b] = 1.0 if d >= v else (d - p) / (v - p)
    C = np.tensordot(pesos, c_par, axes=(0, 0))
    sigma = C.copy()
    for a in range(m):
        for b in range(m):
            if a == b:
                sigma[a, b] = 1.0
                continue
            fator = 1.0
            for j in range(n):
                if d_par[j, a, b] > C[a, b]:
                    fator *= (1.0 - d_par[j, a, b]) / (1.0 - C[a, b])
            sigma[a, b] = C[a, b] * fator
    return sigma, C


def destilacao(sigma: np.ndarray, nomes: list[str], descendente: bool,
               alpha: float = 0.3, beta: float = -0.15) -> list[list[str]]:
    """λ_{k+1} = maior σ abaixo de λ_k − s(λ_k); a T b se σ(a,b) > λ_{k+1} e
    σ(a,b) − σ(b,a) > s(σ(a,b)); qualificação = força − fraqueza; empates são
    destilados de novo com o λ seguinte até sobrar um ou λ = 0."""
    def s(lam):
        return alpha + beta * lam

    restantes = list(range(len(nomes)))
    niveis = []
    while restantes:
        D = restantes
        if len(D) > 1:
            fora = ~np.eye(len(D), dtype=bool)
            lam_k = float(sigma[np.ix_(D, D)][fora].max())
            while len(D) > 1:
                sub = sigma[np.ix_(D, D)]
                fora = ~np.eye(len(D), dtype=bool)
                abaixo = sub[fora][sub[fora] < lam_k - s(lam_k)]
                lam_prox = float(abaixo.max()) if abaixo.size else 0.0
                T = (sub > lam_prox) & (sub - sub.T > s(sub)) & fora
                qual = T.sum(axis=1) - T.sum(axis=0)
                alvo = qual.max() if descendente else qual.min()
                D = [D[i] for i in range(len(D)) if qual[i] == alvo]
                if lam_prox == 0.0:
                    break
                lam_k = lam_prox
        niveis.append([nomes[i] for i in D])
        restantes = [i for i in restantes if i not in D]
    return niveis if descendente else list(reversed(niveis))


def intersecao(desc: list[list[str]], asc: list[list[str]], nomes: list[str]) -> dict:
    """a P b: não fica atrás em nenhuma destilação e fica à frente em pelo menos uma.
    a I b: empate nas duas. a R b: cada uma à frente em uma (incomparáveis)."""
    pd_ = {a: i + 1 for i, nv in enumerate(desc) for a in nv}
    pa = {a: i + 1 for i, nv in enumerate(asc) for a in nv}
    m = len(nomes)
    P = np.zeros((m, m), dtype=bool)
    relacoes, incomparaveis = [], []
    for i in range(m):
        for j in range(i + 1, m):
            a, b = nomes[i], nomes[j]
            dd, da = pd_[a] - pd_[b], pa[a] - pa[b]
            if dd == 0 and da == 0:
                rel = "I"
            elif dd <= 0 and da <= 0:
                rel, P[i, j] = "P", True
            elif dd >= 0 and da >= 0:
                rel, P[j, i] = "P-", True
            else:
                rel = "R"
                incomparaveis.append([a, b])
            relacoes.append({"a": a, "b": b, "relacao": rel})
    camada, restantes, nivel = {}, set(range(m)), 0
    while restantes:
        nivel += 1
        topo = [i for i in restantes if not any(P[k, i] for k in restantes)]
        for i in topo:
            camada[i] = nivel
        restantes -= set(topo)
    ordem = sorted(range(m), key=lambda i: (camada[i], pd_[nomes[i]] + pa[nomes[i]]))
    ranking = [{"posicao": camada[i], "alternativa": nomes[i],
                "pos_descendente": pd_[nomes[i]], "pos_ascendente": pa[nomes[i]],
                "incomparavel_com": [b if a == nomes[i] else a
                                     for a, b in incomparaveis if nomes[i] in (a, b)]}
               for i in ordem]
    return {"ranking": ranking, "relacoes": relacoes, "incomparabilidades": incomparaveis}


def electre_iii(X: np.ndarray, nomes: list[str], sentidos: list[str], pesos: np.ndarray,
                limiares: list[dict]) -> dict:
    sigma, C = credibilidade(X, sentidos, pesos, limiares)
    desc = destilacao(sigma, nomes, True)
    asc = destilacao(sigma, nomes, False)
    final = intersecao(desc, asc, nomes)
    return {"matriz_credibilidade": sigma.round(6).tolist(),
            "destilacao_descendente": desc, "destilacao_ascendente": asc, **final}
