"""Estabilidade das prioridades quando o horizonte da ameaça (z) varia."""
from __future__ import annotations

import pandas as pd

from .pipeline import executar


def varrer_z(cen: pd.DataFrame, esp: dict, zs: list[float],
             limiares: dict | None = None) -> dict:
    pos_veto, pos_soma = {}, {}
    for z in zs:
        r = executar(cen, esp, z, limiares)
        pos_veto[z] = {x["alternativa"]: x["posicao"] for x in r["electre_com_veto"]["ranking"]}
        pos_soma[z] = {x["alternativa"]: x["posicao"] for x in r["soma_ponderada"]}
    veto = pd.DataFrame(pos_veto)
    soma = pd.DataFrame(pos_soma)

    def estabilidade(df: pd.DataFrame) -> float:
        """Média da correlação de Spearman entre ordens de z consecutivos (1 = não muda)."""
        cols = list(df.columns)
        cor = [df[a].corr(df[b], method="spearman") for a, b in zip(cols, cols[1:])]
        return round(float(pd.Series(cor).fillna(1.0).mean()), 4) if cor else 1.0

    topo = (veto == 1).mean(axis=1).sort_values(ascending=False)
    return {
        "zs": zs,
        "posicoes_electre_com_veto": veto,
        "posicoes_soma_ponderada": soma,
        "estabilidade_electre_com_veto": estabilidade(veto),
        "estabilidade_soma_ponderada": estabilidade(soma),
        "frequencia_na_camada_1": topo[topo > 0].round(3).to_dict(),
    }
