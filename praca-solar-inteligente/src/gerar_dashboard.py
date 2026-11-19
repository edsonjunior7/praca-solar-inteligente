"""Gera dashboard/index.html a partir de dados/*.json (página única, sem dependências).
Uso: python3 src/gerar_dashboard.py   (rode antes calculos.py, gerar_leituras.py e alertas.py)
"""
import json
from collections import defaultdict

from calculos import RAIZ, carregar_parametros, cenarios, dimensionar_solar

TEMPLATE = (RAIZ / "src" / "dashboard_template.html").read_text(encoding="utf-8")


def agrupar(alertas):
    grupos = defaultdict(list)
    for a in alertas:
        grupos[(a["regra"], a["gravidade"], a["acao"])].append(a)
    saida = []
    for (regra, grav, acao), itens in grupos.items():
        datas = sorted({i["data"] for i in itens})
        lums = sorted({i["luminaria"] for i in itens})
        saida.append({"regra": regra, "gravidade": grav, "acao": acao, "ocorrencias": len(itens),
                      "datas": datas, "luminarias": lums})
    saida.sort(key=lambda g: (g["gravidade"] != "Alta", -g["ocorrencias"]))
    return saida


def main():
    p = carregar_parametros()
    dados = json.loads((RAIZ / "dados" / "alertas.json").read_text(encoding="utf-8"))
    carga = {
        "params": p,
        "base": cenarios(p),
        "dim": dimensionar_solar(p),
        "resumo": dados["resumo"],
        "alertas": agrupar(dados["alertas"]),
    }
    html = TEMPLATE.replace("__DADOS__", json.dumps(carga, ensure_ascii=False))
    destino = RAIZ / "dashboard" / "index.html"
    destino.write_text(html, encoding="utf-8")
    print("Dashboard gerado em", destino.relative_to(RAIZ))


if __name__ == "__main__":
    main()
