"""Painel do protótipo. Rodar: .venv/bin/streamlit run app.py --server.port 8517"""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from pqc_mcda.pipeline import LIMIARES_PADRAO, carregar, executar, registrar
from pqc_mcda.relatorio import leitura, md_para_pdf, relatorio_pdf, relatorio_xlsx
from pqc_mcda.sensibilidade import varrer_z

TUTORIAL = Path(__file__).parent / "docs" / "TUTORIAL.md"

st.set_page_config(page_title="Priorização PQC", layout="wide")
st.title("Priorização da migração para criptografia pós-quântica")
st.caption("Protótipo · SAPEVO-M → ELECTRE III com veto de Mosca × soma ponderada · dados sintéticos")

cen, esp = carregar()
fonte_cen, fonte_esp = "dados/cenarios.csv (padrão)", "dados/especialistas.json (padrão)"

with st.sidebar:
    st.header("1. Dados de entrada")
    arquivo = st.file_uploader("Cenários (CSV)", type="csv")
    if arquivo:
        cen, fonte_cen = pd.read_csv(arquivo), arquivo.name
    arq_esp = st.file_uploader("Especialistas (JSON)", type="json")
    if arq_esp:
        try:
            esp, fonte_esp = json.load(arq_esp), arq_esp.name
        except json.JSONDecodeError as e:
            st.error(f"JSON inválido: {e}")
            st.stop()
    st.caption(f"Cenários: **{fonte_cen}** ({len(cen)})  \nEspecialistas: **{fonte_esp}** "
               f"({len(esp.get('matrizes', {}))})")

    st.header("2. Parâmetros")
    z = st.slider("Horizonte da ameaça z (anos)", 3, 30, 12,
                  help="Anos até existir um computador quântico capaz de quebrar a criptografia atual.")
    v = st.slider("Veto da margem de Mosca v (anos)", 4, 30,
                  int(LIMIARES_PADRAO["margem_mosca"]["v"]),
                  help="Diferença de margem a partir da qual um cenário não pode ser superado por outro.")
    faixa = st.slider("Faixa de z para a análise de sensibilidade", 3, 40, (5, 30))

    st.header("3. Executar")
    rodar = st.button("Executar análise", type="primary", width="stretch")

    with st.expander("Modelos de arquivo"):
        st.download_button("Modelo de cenários (CSV)", cen.head(3).to_csv(index=False),
                           file_name="modelo_cenarios.csv", mime="text/csv")
        st.download_button("Modelo de especialistas (JSON)",
                           json.dumps(esp, ensure_ascii=False, indent=1),
                           file_name="modelo_especialistas.json", mime="application/json")

assinatura = hashlib.sha256(
    (cen.to_csv(index=False) + json.dumps(esp, sort_keys=True) + f"{z}|{v}|{faixa}").encode()
).hexdigest()

if rodar:
    lim = {"margem_mosca": {**LIMIARES_PADRAO["margem_mosca"], "v": float(v)}}
    try:
        with st.spinner("Calculando pesos, ELECTRE III, soma ponderada e sensibilidade…"):
            r = executar(cen, esp, float(z), lim)
            zs = [float(x) for x in np.arange(faixa[0], faixa[1] + 1, 1)]
            sens = varrer_z(cen, esp, zs, lim)
        registrar(r)
        st.session_state.update(resultado=r, sens=sens, cen=cen, assinatura=assinatura)
    except ValueError as e:
        st.session_state.pop("resultado", None)
        st.error("Entrada inválida. Corrija e execute de novo:")
        for erro in str(e).split("; "):
            st.markdown(f"- {erro}")
        st.stop()

if "resultado" not in st.session_state:
    st.info("Escolha os arquivos (ou use os de exemplo) e os parâmetros na barra lateral e clique "
            "em **Executar análise**.")
    with st.expander("O que este protótipo faz"):
        st.markdown(TUTORIAL.read_text(encoding="utf-8") if TUTORIAL.exists() else "Ver README.md.")
    st.stop()

r, sens, cen_r = st.session_state.resultado, st.session_state.sens, st.session_state.cen
if st.session_state.assinatura != assinatura:
    st.warning("Os dados ou parâmetros mudaram depois da última execução. Clique em "
               "**Executar análise** para atualizar.")

aba = st.tabs(["Resumo", "Ordenações", "Sensibilidade a z", "Dados e pesos", "Auditoria"])

comp = pd.DataFrame(r["comparacao"]).sort_values(["electre_com_veto", "soma_ponderada"])
comp.insert(1, "descricao", comp["cenario"].map(cen_r.set_index("id")["descricao"]))

with aba[0]:
    st.subheader("Leitura do resultado")
    for f in leitura(r, cen_r):
        st.markdown(f"- {f}")
    c = st.columns(4)
    c[0].metric("Cenários", len(cen_r))
    c[1].metric("Já expostos (x+y>z)", sum(x["margem_mosca"] > 0 for x in r["comparacao"]))
    c[2].metric("Pares incomparáveis", len(r["electre_com_veto"]["incomparabilidades"]))
    c[3].metric("Pares alterados pelo veto", len(r["pares_alterados_pelo_veto"]))
    st.subheader("Relatório")
    d = st.columns(3)
    nome = f"priorizacao_pqc_z{r['parametros']['z_horizonte_anos']:g}"
    d[0].download_button("PDF (enxuto)", relatorio_pdf(r, cen_r, sens), f"{nome}.pdf",
                         "application/pdf", type="primary", width="stretch")
    d[1].download_button("Planilha (XLSX)", relatorio_xlsx(r, cen_r, sens), f"{nome}.xlsx",
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         width="stretch")
    d[2].download_button("Dados completos (JSON)", json.dumps(r, ensure_ascii=False, indent=2),
                         f"{nome}.json", "application/json", width="stretch")

with aba[1]:
    st.dataframe(comp, width="stretch", hide_index=True)
    st.caption("Posição do ELECTRE = camada da pré-ordem final; cenários na mesma camada estão "
               "empatados ou são incomparáveis. A soma ponderada sempre força uma ordem completa.")
    a, b = st.columns(2)
    a.markdown("**Incomparabilidades (com veto)**")
    a.dataframe(pd.DataFrame(r["electre_com_veto"]["incomparabilidades"], columns=["a", "b"]),
                hide_index=True, width="stretch")
    b.markdown("**Pares alterados pelo veto**")
    b.dataframe(pd.DataFrame(r["pares_alterados_pelo_veto"]), hide_index=True, width="stretch")

with aba[2]:
    s = st.columns(2)
    s[0].metric("Estabilidade ELECTRE III com veto", f"{sens['estabilidade_electre_com_veto']:.3f}")
    s[1].metric("Estabilidade soma ponderada", f"{sens['estabilidade_soma_ponderada']:.3f}")
    st.caption("Média da correlação de Spearman entre as ordens de z consecutivos (1 = não muda).")
    top = comp["cenario"].head(8).tolist()
    st.markdown("**Posição dos 8 primeiros cenários conforme z (ELECTRE III com veto; menor = mais urgente)**")
    st.line_chart(sens["posicoes_electre_com_veto"].loc[top].T)
    st.markdown("**Frequência de cada cenário na camada 1**")
    st.bar_chart(pd.Series(sens["frequencia_na_camada_1"], name="frequência"))

with aba[3]:
    st.markdown("**Pesos do grupo (SAPEVO-M)**")
    pesos = pd.DataFrame(r["pesos_por_especialista"], index=list(r["pesos"]))
    pesos.insert(0, "grupo", list(r["pesos"].values()))
    st.dataframe(pesos.round(3), width="stretch")
    st.caption("Colunas por especialista mostram onde o painel diverge.")
    st.markdown("**Cenários usados**")
    st.dataframe(cen_r, width="stretch", hide_index=True)

with aba[4]:
    st.json(r["auditoria"])
    st.json(r["parametros"])
    st.caption("Cada execução é gravada em auditoria/execucoes.jsonl. O mesmo SHA-256 de entrada "
               "com os mesmos parâmetros reproduz o mesmo resultado.")
    if TUTORIAL.exists():
        st.download_button("Tutorial (PDF)", md_para_pdf(TUTORIAL.read_text(encoding="utf-8"),
                                                         "Tutorial do protótipo"),
                           "tutorial_pqc_mcda.pdf", "application/pdf")
