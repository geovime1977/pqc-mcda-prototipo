"""Painel do protótipo. Rodar: .venv/bin/streamlit run app.py --server.port 8517"""
import json

import pandas as pd
import streamlit as st

from pqc_mcda.pipeline import CRITERIOS, LIMIARES_PADRAO, carregar, executar, registrar

st.set_page_config(page_title="Priorização PQC", layout="wide")
st.title("Priorização da migração para criptografia pós-quântica")
st.caption("Protótipo · SAPEVO-M → ELECTRE III com veto de Mosca × soma ponderada · dados sintéticos")

cen, esp = carregar()
with st.sidebar:
    st.header("Parâmetros")
    z = st.slider("Horizonte da ameaça z (anos)", 3, 30, 12)
    v = st.slider("Veto da margem de Mosca v (anos)", 4, 30,
                  int(LIMIARES_PADRAO["margem_mosca"]["v"]))
    arquivo = st.file_uploader("Trocar cenários (CSV)", type="csv")
    if arquivo:
        cen = pd.read_csv(arquivo)

try:
    lim = {"margem_mosca": {**LIMIARES_PADRAO["margem_mosca"], "v": float(v)}}
    r = executar(cen, esp, float(z), lim)
except ValueError as e:
    st.error(f"Entrada inválida: {e}")
    st.stop()

c1, c2 = st.columns([1, 2])
c1.subheader("Pesos (SAPEVO-M, 3 especialistas)")
c1.dataframe(pd.Series(r["pesos"], name="peso").to_frame(), width="stretch")
c2.subheader("Cenários")
c2.dataframe(cen, width="stretch", hide_index=True)

st.subheader("Comparação de ordenações")
comp = pd.DataFrame(r["comparacao"]).sort_values(["electre_com_veto", "soma_ponderada"])
st.dataframe(comp, width="stretch", hide_index=True)
st.caption("Posição do ELECTRE = camada da pré-ordem parcial; cenários na mesma camada "
           "estão empatados ou são incomparáveis.")

a, b = st.columns(2)
a.subheader("Incomparabilidades (com veto)")
a.write(r["electre_com_veto"]["incomparabilidades"] or "nenhuma")
b.subheader("Pares alterados pelo veto")
b.write(r["pares_alterados_pelo_veto"] or "nenhum")

if st.button("Registrar execução na auditoria"):
    registrar(r)
    st.success(f"Registrada · sha256 da entrada {r['auditoria']['sha256_entrada'][:16]}…")
st.download_button("Baixar resultado (JSON)", json.dumps(r, ensure_ascii=False, indent=2),
                   file_name=f"resultado_z{z}.json", mime="application/json")
