"""Executa o protótipo pela linha de comando.

uso: .venv/bin/python run.py [--z 12] [--saida saida/resultado.json]
"""
import argparse
import json
from pathlib import Path

from pqc_mcda.pipeline import carregar, executar, registrar


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--z", type=float, default=12.0,
                    help="horizonte da ameaça quântica em anos (desigualdade de Mosca)")
    ap.add_argument("--saida", default=None)
    args = ap.parse_args()

    cen, esp = carregar()
    r = executar(cen, esp, args.z)
    registrar(r)

    print(f"z = {args.z} anos | pesos SAPEVO-M: {r['pesos']}")
    print(f"{'cenário':8} {'x+y-z':>6} {'margem':>7} {'soma':>5} {'sem veto':>9} {'com veto':>9}")
    for c in sorted(r["comparacao"], key=lambda c: (c["electre_com_veto"], c["soma_ponderada"])):
        print(f"{c['cenario']:8} {c['margem_bruta']:6.1f} {c['margem_mosca']:7.1f} "
              f"{c['soma_ponderada']:5d} {c['electre_sem_veto']:9d} {c['electre_com_veto']:9d}")
    if r["electre_com_veto"]["incomparabilidades"]:
        print("incomparáveis (com veto):", r["electre_com_veto"]["incomparabilidades"])
    pv = r["pares_alterados_pelo_veto"]
    print(f"pares cuja relação mudou pelo veto: {len(pv)}")
    for p in pv:
        print(f"  {p['a']} x {p['b']}: {p['sem_veto']} -> {p['com_veto']}")
    print(f"sha256 da entrada: {r['auditoria']['sha256_entrada'][:16]}…")
    if args.saida:
        Path(args.saida).parent.mkdir(parents=True, exist_ok=True)
        Path(args.saida).write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
