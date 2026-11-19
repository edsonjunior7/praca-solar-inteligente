"""Cálculos da Praça Solar Inteligente (GS 2026.2, SERS).

Lê dados/parametros.json, calcula as alternativas A, B e C, o dimensionamento
solar e os indicadores do dashboard, e grava dados/indicadores.json.
Uso: python3 src/calculos.py
"""
import json
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def carregar_parametros(caminho=None):
    caminho = Path(caminho) if caminho else RAIZ / "dados" / "parametros.json"
    with open(caminho, encoding="utf-8") as f:
        bruto = json.load(f)
    return {k: v["valor"] for k, v in bruto.items() if isinstance(v, dict)}


def cenarios(p, tarifa=None, reducao=None, solar=None):
    """Retorna A, B e C para a mesma necessidade (iluminar a praça) em um mês."""
    tarifa = p["tarifa_rs_kwh"] if tarifa is None else tarifa
    reducao = p["reducao_modo_economico"] if reducao is None else reducao
    solar = p["participacao_solar_meta"] if solar is None else solar
    n, h, d = p["luminarias"], p["horas_por_noite"], p["dias_mes"]
    fe = p["fator_emissao_kg_kwh"]

    a = p["potencia_convencional_w"] * h * n / 1000 * d          # E = P x t x n / 1000
    b = p["potencia_led_w"] * h * n / 1000 * d * (1 - reducao)
    c_solar = b * solar
    c_rede = b - c_solar

    def alt(consumo, rede, sol):
        return {
            "consumo_kwh_mes": consumo,
            "rede_kwh_mes": rede,
            "solar_kwh_mes": sol,
            "custo_rede_rs_mes": rede * tarifa,
            "economia_energetica_pct": (1 - consumo / a) * 100,
            "participacao_renovavel_pct": sol / consumo * 100,
            "emissoes_evitadas_kg_mes": (a - rede) * fe,
        }

    r = {"A": alt(a, a, 0.0), "B": alt(b, b, 0.0), "C": alt(b, c_rede, c_solar)}
    r["extra_C_sobre_B_rs_mes"] = r["B"]["custo_rede_rs_mes"] - r["C"]["custo_rede_rs_mes"]
    r["extra_C_sobre_B_rs_ano"] = r["extra_C_sobre_B_rs_mes"] * 12
    r["limite_investimento_extra_rs"] = {
        f"{anos}_anos": r["extra_C_sobre_B_rs_ano"] * anos for anos in (5, 10, 25)
    }
    return r


def dimensionar_solar(p, carga_kwh_mes=None):
    """P = E / (HSP x dias x PR); bateria para N noites com profundidade de descarga."""
    c = cenarios(p)
    carga = c["B"]["consumo_kwh_mes"] if carga_kwh_mes is None else carga_kwh_mes
    energia_solar = carga * p["participacao_solar_meta"]
    fator = p["irradiacao_kwh_m2_dia"] * p["dias_mes"] * p["desempenho_fv_pr"]
    kwp = energia_solar / fator
    modulos = math.ceil(kwp * 1000 / p["modulo_fv_wp"])
    kwp_instalado = modulos * p["modulo_fv_wp"] / 1000
    geracao = kwp_instalado * fator
    noite = carga / p["dias_mes"]
    bateria = noite * p["autonomia_noites"] / p["profundidade_descarga"]
    return {
        "energia_solar_desejada_kwh_mes": energia_solar,
        "potencia_necessaria_kwp": kwp,
        "modulos": modulos,
        "potencia_instalada_kwp": kwp_instalado,
        "geracao_estimada_kwh_mes": geracao,
        "margem_sobre_meta_pct": (geracao / energia_solar - 1) * 100,
        "carga_kwh_noite": noite,
        "bateria_kwh": bateria,
    }


def matriz_decisao():
    pesos = [0.25, 0.25, 0.15, 0.15, 0.10, 0.10]
    notas = {"A": [1, 1, 5, 5, 2, 1], "B": [4, 1, 4, 4, 4, 4], "C": [4, 5, 2, 3, 5, 5]}
    return {k: round(sum(w * x for w, x in zip(pesos, v)), 2) for k, v in notas.items()}


def sensibilidade(p):
    return {
        "Conservador": cenarios(p, 0.70, 0.15, 0.60),
        "Base": cenarios(p),
        "Favorável": cenarios(p, 1.00, 0.45, 0.95),
    }


def main():
    p = carregar_parametros()
    saida = {
        "cenarios": cenarios(p),
        "dimensionamento": dimensionar_solar(p),
        "matriz_decisao": matriz_decisao(),
        "sensibilidade": {k: {"economia_C_sobre_A_rs_mes": v["A"]["custo_rede_rs_mes"] - v["C"]["custo_rede_rs_mes"],
                              "extra_C_sobre_B_rs_ano": v["extra_C_sobre_B_rs_ano"]}
                          for k, v in sensibilidade(p).items()},
        "aviso": "Projeções condicionadas às premissas de dados/parametros.json; não são resultados garantidos.",
    }
    destino = RAIZ / "dados" / "indicadores.json"
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    c = saida["cenarios"]
    print("Alternativa  Consumo(kWh/mês)  Rede(kWh/mês)  Custo rede(R$/mês)  Renovável(%)  CO2 evitado(kg/mês)")
    for k in "ABC":
        x = c[k]
        print(f"{k:^11}  {x['consumo_kwh_mes']:>16.1f}  {x['rede_kwh_mes']:>13.2f}  {x['custo_rede_rs_mes']:>18.2f}  "
              f"{x['participacao_renovavel_pct']:>12.0f}  {x['emissoes_evitadas_kg_mes']:>19.1f}")
    print(f"Economia adicional de C sobre B: R$ {c['extra_C_sobre_B_rs_mes']:.2f}/mês = R$ {c['extra_C_sobre_B_rs_ano']:.2f}/ano")
    dim = saida["dimensionamento"]
    print(f"Solar: {dim['potencia_necessaria_kwp']:.2f} kWp necessários, {dim['modulos']} módulos, "
          f"{dim['geracao_estimada_kwh_mes']:.2f} kWh/mês, bateria {dim['bateria_kwh']:.1f} kWh")
    print("Matriz de decisão:", saida["matriz_decisao"])
    print("Gravado em", destino.relative_to(RAIZ))


if __name__ == "__main__":
    main()
