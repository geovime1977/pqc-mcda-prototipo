import json

import numpy as np
import pytest

from pqc_mcda.electre import credibilidade, electre_iii, intersecao
from pqc_mcda.pipeline import carregar, executar
from pqc_mcda.sapevo import pesos_grupo, validar_matriz
from pqc_mcda.soma_ponderada import soma_ponderada


def test_sapevo_rejeita_matriz_nao_antissimetrica():
    with pytest.raises(ValueError):
        validar_matriz(np.array([[0, 1], [1, 0]]), "x")


def test_sapevo_pesos_somam_um_e_seguem_a_ordem():
    w, _ = pesos_grupo({"e": [[0, 2, 3], [-2, 0, 1], [-3, -1, 0]]})
    assert abs(w.sum() - 1) < 1e-12
    assert w[0] > w[1] > w[2]


def test_credibilidade_nao_excede_concordancia():
    rng = np.random.default_rng(1)
    X = rng.uniform(0, 10, (6, 4))
    lim = [{"q": 0.5, "p": 1.5, "v": 4.0}] * 4
    sigma, C = credibilidade(X, ["max"] * 4, np.full(4, 0.25), lim)
    fora = ~np.eye(6, dtype=bool)
    assert (sigma[fora] <= C[fora] + 1e-12).all() and sigma.min() >= 0


def test_veto_impede_que_custo_baixo_supere_exposicao_grave():
    # A: barato, margem baixa. B: caro, margem muito alta.
    X = np.array([[0.0, 1.0], [12.0, 5.0]])
    lim = [{"q": 1.0, "p": 3.0, "v": 8.0}, {"q": 0.0, "p": 1.0, "v": None}]
    w = np.array([0.3, 0.7])
    sigma, _ = credibilidade(X, ["max", "min"], w, lim)
    assert sigma[0, 1] == 0.0
    sem, _ = credibilidade(X, ["max", "min"], w, [{**lim[0], "v": None}, lim[1]])
    assert sem[0, 1] > 0.0


def test_intersecao_marca_incomparabilidade():
    r = intersecao([["A"], ["B"], ["C"]], [["B"], ["A"], ["C"]], ["A", "B", "C"])
    assert r["incomparabilidades"] == [["A", "B"]]
    assert {x["alternativa"]: x["posicao"] for x in r["ranking"]} == {"A": 1, "B": 1, "C": 2}


def test_dominante_fica_sozinha_no_topo():
    X = np.array([[10.0, 10.0], [5.0, 6.0], [1.0, 1.0]])
    lim = [{"q": 0.5, "p": 2.0, "v": None}] * 2
    r = electre_iii(X, ["Ot", "Md", "Ru"], ["max", "max"], np.array([0.5, 0.5]), lim)
    pos = {x["alternativa"]: x["posicao"] for x in r["ranking"]}
    assert pos == {"Ot": 1, "Md": 2, "Ru": 3}


def test_soma_ponderada_respeita_sentido():
    r = soma_ponderada(np.array([[1.0], [5.0]]), ["a", "b"], ["min"], np.array([1.0]))
    assert r[0]["alternativa"] == "a"


def test_pipeline_reprodutivel_e_completo():
    cen, esp = carregar()
    r1, r2 = executar(cen, esp, 12.0), executar(cen, esp, 12.0)
    assert r1["auditoria"]["sha256_entrada"] == r2["auditoria"]["sha256_entrada"]
    assert r1["comparacao"] == r2["comparacao"]
    assert len(r1["comparacao"]) == len(cen)
    json.dumps(r1, ensure_ascii=False)


def test_pipeline_rejeita_escala_invalida():
    cen, esp = carregar()
    cen.loc[0, "sensibilidade"] = 9
    with pytest.raises(ValueError, match="sensibilidade"):
        executar(cen, esp, 12.0)
