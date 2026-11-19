"""Gera dados/leituras_simuladas.csv: 30 noites x 20 luminárias (DADOS SIMULADOS, semente fixa).

Uma linha por luminária por noite. Eventos injetados de propósito para o dashboard
ter o que alertar: dias nublados, luminárias offline, falha de resposta à presença
e bateria baixa depois de dias nublados.
Uso: python3 src/gerar_leituras.py
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

from calculos import RAIZ, carregar_parametros

SEMENTE = 2026
INICIO = date(2026, 10, 1)


def gerar():
    p = carregar_parametros()
    rnd = random.Random(SEMENTE)
    n, dias = p["luminarias"], p["dias_mes"]
    carga_base = p["potencia_led_w"] * p["horas_por_noite"] / 1000 * (1 - p["reducao_modo_economico"])  # kWh/noite
    previsao = (p["modulo_fv_wp"] * 4 / 1000 * p["irradiacao_kwh_m2_dia"] * p["desempenho_fv_pr"]) / n  # kWh/noite por luminária
    nublados = {8: 0.55, 9: 0.50, 10: 0.60, 21: 0.62}
    linhas = []
    base_bat = {i: rnd.uniform(72, 88) for i in range(1, n + 1)}
    for d in range(1, dias + 1):
        fator_clima = nublados.get(d, rnd.uniform(0.88, 1.08))
        for i in range(1, n + 1):
            lid = f"L{i:02d}"
            status, modo = "ativo", "economico"
            carga = carga_base * rnd.uniform(0.92, 1.08)
            if i == 7 and d >= 28:
                status, carga = "offline", 0.0
            if i == 13 and d in (19, 20, 21):
                status, modo = "falha", "manutencao"      # presença detectada sem aumento de intensidade
            if i == 4 and d in (14, 15):
                carga *= 1.45                              # consumo acima do esperado
            geracao = previsao * fator_clima * rnd.uniform(0.97, 1.03) if status != "offline" else 0.0
            solar = min(geracao, carga * p["participacao_solar_meta"])
            rede = max(carga - solar, 0.0)
            # nível mínimo da bateria: cai depois de dias nublados e se recupera nos dias de sol
            queda = 18.0 if d in (9, 10, 11) else 0.0
            bat = base_bat[i] - queda + rnd.uniform(-4, 4)
            if i in (3, 16) and d in (10, 11):
                bat = 14.0 + (d - 10)                        # dois pontos chegam abaixo de 20%
            linhas.append({
                "data": (INICIO + timedelta(days=d - 1)).isoformat(),
                "luminaria_id": lid,
                "energia_total_kwh": round(carga, 4),
                "energia_solar_kwh": round(solar, 4),
                "energia_rede_kwh": round(rede, 4),
                "geracao_prevista_kwh": round(previsao, 4),
                "geracao_real_kwh": round(geracao, 4),
                "bateria_minima_pct": round(bat, 1),
                "modo_operacao": modo,
                "status": status,
            })
    destino = RAIZ / "dados" / "leituras_simuladas.csv"
    with open(destino, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)
    print(f"{len(linhas)} leituras simuladas gravadas em {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    gerar()
