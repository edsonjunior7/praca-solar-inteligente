"""Aplica as regras de alerta do relatório às leituras simuladas e resume o último dia.

As leituras são diárias (uma por luminária por noite), então "sem leitura" vira
"status offline". Em produção, a regra é "sem leitura por 15 minutos".
Uso: python3 src/alertas.py   (grava dados/alertas.json)
"""
import csv
import json
from collections import defaultdict

from calculos import RAIZ

REGRAS = {
    "bateria_baixa": ("Bateria baixa", "Alta", "Verificar geração e autonomia"),
    "offline": ("Luminária offline", "Alta", "Abrir chamado de manutenção"),
    "sem_resposta": ("Presença sem resposta", "Alta", "Verificar luminária e controlador"),
    "consumo_alto": ("Consumo acima do esperado", "Média", "Investigar sensor ou carga"),
    "geracao_baixa": ("Baixa geração solar", "Média", "Verificar sujeira, sombra ou falha"),
}


def ler():
    with open(RAIZ / "dados" / "leituras_simuladas.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def aplicar_regras(linhas):
    ativas = [float(r["energia_total_kwh"]) for r in linhas if r["status"] == "ativo"]
    media = sum(ativas) / len(ativas)
    alertas = []
    for r in linhas:
        achados = []
        if float(r["bateria_minima_pct"]) < 20:
            achados.append("bateria_baixa")
        if r["status"] == "offline":
            achados.append("offline")
        if r["status"] == "falha":
            achados.append("sem_resposta")
        if r["status"] == "ativo" and float(r["energia_total_kwh"]) > 1.2 * media:
            achados.append("consumo_alto")
        if r["status"] != "offline" and float(r["geracao_real_kwh"]) < 0.7 * float(r["geracao_prevista_kwh"]):
            achados.append("geracao_baixa")
        for chave in achados:
            nome, gravidade, acao = REGRAS[chave]
            alertas.append({"data": r["data"], "luminaria": r["luminaria_id"], "regra": nome,
                            "gravidade": gravidade, "acao": acao})
    return alertas, media


def resumo(linhas):
    por_dia = defaultdict(list)
    for r in linhas:
        por_dia[r["data"]].append(r)
    ultimo = max(por_dia)
    total = sum(float(r["energia_total_kwh"]) for r in linhas)
    solar = sum(float(r["energia_solar_kwh"]) for r in linhas)
    ativos = sum(1 for r in linhas if r["status"] == "ativo")
    bat = [float(r["bateria_minima_pct"]) for r in por_dia[ultimo] if r["status"] != "offline"]
    return {
        "periodo": [min(por_dia), ultimo],
        "participacao_renovavel_medida_pct": solar / total * 100,
        "disponibilidade_pct": ativos / len(linhas) * 100,
        "bateria_media_ultimo_dia_pct": sum(bat) / len(bat),
        "ultimo_dia": [{"id": r["luminaria_id"], "status": r["status"], "modo": r["modo_operacao"],
                        "bateria": float(r["bateria_minima_pct"])} for r in por_dia[ultimo]],
    }


def main():
    linhas = ler()
    alertas, media = aplicar_regras(linhas)
    res = resumo(linhas)
    res["consumo_medio_luminaria_kwh_noite"] = media
    res["alertas_total"] = len(alertas)
    with open(RAIZ / "dados" / "alertas.json", "w", encoding="utf-8") as f:
        json.dump({"resumo": res, "alertas": alertas}, f, ensure_ascii=False, indent=2)
    print(f"{len(alertas)} alertas em {res['periodo'][0]} a {res['periodo'][1]}")
    por_regra = defaultdict(int)
    for a in alertas:
        por_regra[a["regra"]] += 1
    for k, v in sorted(por_regra.items()):
        print(f"  {k}: {v}")
    print(f"Participação renovável medida: {res['participacao_renovavel_medida_pct']:.1f}%  "
          f"Disponibilidade: {res['disponibilidade_pct']:.1f}%")


if __name__ == "__main__":
    main()
