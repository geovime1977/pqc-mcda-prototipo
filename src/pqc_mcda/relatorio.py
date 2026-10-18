"""Relatório enxuto (PDF e XLSX) de uma execução e conversor simples de Markdown para PDF."""
from __future__ import annotations

import io
import re
from pathlib import Path

import pandas as pd
from fpdf import FPDF

# Fonte Unicode do sistema (macOS ou Linux); sem ela, cai para Helvetica e troca símbolos.
FONTES = [("/System/Library/Fonts/Supplemental/Arial.ttf",
           "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
           "/System/Library/Fonts/Supplemental/Courier New.ttf"),
          ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")]
TROCAS = {"−": "-", "×": "x", "→": "->", "σ": "sigma", "λ": "lambda", "≥": ">=", "≤": "<=",
          "…": "...", "—": "-", "–": "-", "“": '"', "”": '"', "’": "'", "·": "-"}


class _PDF(FPDF):
    titulo = ""
    unicode = False

    def header(self):
        self.set_font("sans", "", 8)
        self.set_text_color(110)
        self.cell(0, 5, self.t(self.titulo), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0)
        self.ln(1)

    def footer(self):
        self.set_y(-12)
        self.set_font("sans", "", 8)
        self.cell(0, 5, str(self.page_no()), align="C")

    def t(self, s: str, negrito: bool = False) -> str:
        s = s.replace("`", "")
        s = re.sub(r"(?<!\*)\*(?!\*)([^*]+)(?<!\*)\*(?!\*)", r"\1", s)
        if not negrito:
            s = s.replace("**", "")
        if self.unicode:
            return s
        for k, v in TROCAS.items():
            s = s.replace(k, v)
        return s.encode("latin-1", "replace").decode("latin-1")


def _novo_pdf(titulo: str) -> _PDF:
    pdf = _PDF(format="A4")
    pdf.titulo = titulo
    for normal, negrito, mono in FONTES:
        if all(Path(f).exists() for f in (normal, negrito, mono)):
            pdf.add_font("sans", "", normal)
            pdf.add_font("sans", "B", negrito)
            pdf.add_font("mono", "", mono)
            pdf.unicode = True
            break
    if not pdf.unicode:
        _alias_core(pdf)
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_page()
    return pdf


def _alias_core(pdf: _PDF) -> None:
    orig = pdf.set_font

    def set_font(family="", style="", size=0):
        fam = {"sans": "helvetica", "mono": "courier"}.get(family, family)
        return orig(fam, style, size)

    pdf.set_font = set_font


def _tabela(pdf: _PDF, df: pd.DataFrame, larguras: list[float]) -> None:
    pdf.set_font("sans", "B", 8)
    for col, w in zip(df.columns, larguras):
        pdf.cell(w, 5, pdf.t(str(col)), border=1)
    pdf.ln()
    pdf.set_font("sans", "", 8)
    for _, linha in df.iterrows():
        for v, w in zip(linha, larguras):
            pdf.cell(w, 5, pdf.t(str(v))[:int(w / 1.6)], border=1)
        pdf.ln()
    pdf.ln(2)


def _secao(pdf: _PDF, texto: str) -> None:
    pdf.ln(2)
    pdf.set_font("sans", "B", 11)
    pdf.cell(0, 6, pdf.t(texto), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("sans", "", 9)


def _par(pdf: _PDF, texto: str) -> None:
    pdf.set_font("sans", "", 9)
    pdf.multi_cell(0, 4.6, pdf.t(texto), new_x="LMARGIN", new_y="NEXT")


def leitura(r: dict, cen: pd.DataFrame) -> list[str]:
    """Frases em linguagem simples sobre o resultado."""
    z = r["parametros"]["z_horizonte_anos"]
    rk = r["electre_com_veto"]["ranking"]
    topo = [x["alternativa"] for x in rk if x["posicao"] == 1]
    desc = cen.set_index("id")["descricao"].to_dict()
    expostos = [c["cenario"] for c in r["comparacao"] if c["margem_mosca"] > 0]
    top_soma = r["soma_ponderada"][0]["alternativa"]
    frases = [
        f"Com horizonte da ameaça de {z:g} anos, {len(expostos)} de {len(cen)} cenários já estão "
        f"expostos pela desigualdade de Mosca (x + y > z).",
        "Prioridade máxima (camada 1 do ELECTRE III com veto): "
        + "; ".join(f"{a} ({desc.get(a, '')})" for a in topo) + ".",
        f"A soma ponderada, com os mesmos pesos, põe {top_soma} em primeiro lugar.",
    ]
    inc = r["electre_com_veto"]["incomparabilidades"]
    if inc:
        frases.append(f"Há {len(inc)} pares incomparáveis: o método não força ordem entre eles, "
                      "e a decisão sobre esses pares cabe ao decisor.")
    pv = r["pares_alterados_pelo_veto"]
    frases.append(f"O veto da margem de Mosca alterou a relação de {len(pv)} "
                  f"{'par' if len(pv) == 1 else 'pares'} de cenários."
                  if pv else "O veto da margem de Mosca não alterou nenhuma relação com estes dados.")
    return frases


def relatorio_pdf(r: dict, cen: pd.DataFrame, sens: dict | None = None, max_linhas: int = 20) -> bytes:
    pdf = _novo_pdf("Relatório de priorização da migração pós-quântica · protótipo · dados sintéticos")
    pdf.set_font("sans", "B", 14)
    pdf.cell(0, 8, pdf.t("Priorização da migração para criptografia pós-quântica"),
             new_x="LMARGIN", new_y="NEXT")
    a = r["auditoria"]
    _par(pdf, f"Execução {a['quando']} · protótipo v{a['versao_prototipo']} · "
              f"SHA-256 da entrada {a['sha256_entrada'][:16]}…")

    _secao(pdf, "Leitura do resultado")
    for f in leitura(r, cen):
        _par(pdf, "• " + f)

    _secao(pdf, "Parâmetros e pesos")
    lim = r["parametros"]["limiares"]["margem_mosca"]
    _par(pdf, f"Horizonte z = {r['parametros']['z_horizonte_anos']:g} anos. Margem de Mosca: "
              f"q = {lim['q']:g}, p = {lim['p']:g}, veto v = {lim['v']:g} anos. "
              f"Pesos SAPEVO-M de {len(r['pesos_por_especialista'])} especialistas:")
    pesos = pd.DataFrame({"critério": list(r["pesos"]), "peso": [f"{v:.3f}" for v in r["pesos"].values()]})
    _tabela(pdf, pesos, [50, 25])

    _secao(pdf, f"Ordenações (primeiros {min(max_linhas, len(cen))} cenários)")
    comp = pd.DataFrame(r["comparacao"]).sort_values(["electre_com_veto", "soma_ponderada"])
    comp = comp.head(max_linhas)[["cenario", "margem_bruta", "margem_mosca", "soma_ponderada",
                                  "electre_sem_veto", "electre_com_veto"]]
    comp.columns = ["cenário", "x+y-z", "margem", "soma pond.", "ELECTRE s/ veto", "ELECTRE c/ veto"]
    _tabela(pdf, comp, [22, 20, 20, 25, 33, 33])
    _par(pdf, "Posição do ELECTRE = camada da pré-ordem final; cenários na mesma camada estão "
              "empatados ou são incomparáveis.")

    if sens:
        _secao(pdf, "Estabilidade quando z varia")
        _par(pdf, f"z de {min(sens['zs']):g} a {max(sens['zs']):g} anos. Estabilidade média "
                  f"(Spearman entre z consecutivos, 1 = ordem não muda): ELECTRE III com veto "
                  f"{sens['estabilidade_electre_com_veto']:.3f}; soma ponderada "
                  f"{sens['estabilidade_soma_ponderada']:.3f}.")
        freq = sens["frequencia_na_camada_1"]
        if freq:
            _par(pdf, "Frequência na camada 1: " +
                 ", ".join(f"{k} {v:.0%}" for k, v in list(freq.items())[:8]) + ".")

    _secao(pdf, "Limites")
    _par(pdf, "Dados sintéticos. Limiares ilustrativos. O resultado apoia a decisão, não a substitui; "
              "a aplicação com dados reais cabe aos órgãos competentes, em ambiente autorizado.")
    return bytes(pdf.output())


def relatorio_xlsx(r: dict, cen: pd.DataFrame, sens: dict | None = None) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        pd.DataFrame({"leitura": leitura(r, cen)}).to_excel(xw, sheet_name="Resumo", index=False)
        pd.DataFrame(r["comparacao"]).to_excel(xw, sheet_name="Comparação", index=False)
        pd.DataFrame(r["electre_com_veto"]["ranking"]).to_excel(xw, sheet_name="ELECTRE com veto", index=False)
        pd.DataFrame(r["soma_ponderada"]).to_excel(xw, sheet_name="Soma ponderada", index=False)
        pd.Series(r["pesos"], name="peso").to_frame().to_excel(xw, sheet_name="Pesos")
        pd.DataFrame(r["pares_alterados_pelo_veto"] or [{}]).to_excel(xw, sheet_name="Pares alterados", index=False)
        cen.to_excel(xw, sheet_name="Cenários", index=False)
        if sens:
            sens["posicoes_electre_com_veto"].to_excel(xw, sheet_name="Sensib. z (ELECTRE)")
            sens["posicoes_soma_ponderada"].to_excel(xw, sheet_name="Sensib. z (soma)")
        pd.Series(r["auditoria"]).to_frame("valor").to_excel(xw, sheet_name="Auditoria")
    return buf.getvalue()


def md_para_pdf(md: str, titulo: str) -> bytes:
    """Markdown simples (títulos, parágrafos, listas, tabelas e código) para PDF."""
    pdf = _novo_pdf(titulo)
    em_codigo = False
    tabela: list[list[str]] = []
    for bruta in md.splitlines() + [""]:
        linha = bruta.rstrip()
        if not em_codigo and linha.lstrip().startswith("|"):
            if not re.fullmatch(r"\s*\|[\s:|-]+\|\s*", linha):
                tabela.append([c.strip() for c in linha.strip().strip("|").split("|")])
            continue
        if tabela:
            pdf.set_font("sans", "", 8.5)
            with pdf.table(first_row_as_headings=True, line_height=4.6) as tb:
                for cols in tabela:
                    row = tb.row()
                    for c in cols:
                        row.cell(pdf.t(c))
            tabela = []
        if linha.startswith("```"):
            em_codigo = not em_codigo
            pdf.ln(1)
            continue
        if em_codigo:
            pdf.set_font("mono", "", 7.5)
            pdf.multi_cell(0, 3.8, pdf.t(linha) or " ", new_x="LMARGIN", new_y="NEXT")
            continue
        m = re.match(r"^(#{1,3})\s+(.*)", linha)
        if m:
            pdf.ln(2)
            pdf.set_font("sans", "B", {1: 15, 2: 12, 3: 10.5}[len(m.group(1))])
            pdf.multi_cell(0, 6.5, pdf.t(m.group(2)), new_x="LMARGIN", new_y="NEXT")
            continue
        if not linha.strip():
            pdf.ln(2)
            continue
        if linha.lstrip().startswith(("- ", "* ")):
            linha = "• " + linha.lstrip()[2:]
        pdf.set_font("sans", "", 9.5)
        pdf.multi_cell(0, 4.8, pdf.t(linha, negrito=True), new_x="LMARGIN", new_y="NEXT",
                       markdown=True)
    return bytes(pdf.output())
