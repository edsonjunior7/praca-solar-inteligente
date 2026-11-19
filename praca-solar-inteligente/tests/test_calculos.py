"""Testes dos cálculos. Uso: python3 -m unittest discover -s tests -v  (na raiz do repositório)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import calculos  # noqa: E402
import alertas   # noqa: E402


class TestCalculos(unittest.TestCase):
    def setUp(self):
        self.p = calculos.carregar_parametros()
        self.c = calculos.cenarios(self.p)

    def test_consumo_das_alternativas(self):
        self.assertAlmostEqual(self.c["A"]["consumo_kwh_mes"], 720.0)
        self.assertAlmostEqual(self.c["B"]["consumo_kwh_mes"], 201.6)
        self.assertAlmostEqual(self.c["C"]["rede_kwh_mes"], 40.32)

    def test_custos(self):
        self.assertAlmostEqual(self.c["A"]["custo_rede_rs_mes"], 612.00)
        self.assertAlmostEqual(self.c["B"]["custo_rede_rs_mes"], 171.36)
        self.assertAlmostEqual(self.c["C"]["custo_rede_rs_mes"], 34.272, places=3)
        self.assertAlmostEqual(self.c["extra_C_sobre_B_rs_mes"], 137.088, places=3)

    def test_economia_e_renovavel(self):
        self.assertAlmostEqual(self.c["B"]["economia_energetica_pct"], 72.0)
        self.assertAlmostEqual(self.c["C"]["participacao_renovavel_pct"], 80.0)
        self.assertAlmostEqual(self.c["A"]["participacao_renovavel_pct"], 0.0)

    def test_emissoes(self):
        self.assertAlmostEqual(self.c["B"]["emissoes_evitadas_kg_mes"], 518.4 * 0.0385, places=3)
        self.assertAlmostEqual(self.c["C"]["emissoes_evitadas_kg_mes"], 679.68 * 0.0385, places=3)

    def test_dimensionamento(self):
        d = calculos.dimensionar_solar(self.p)
        self.assertAlmostEqual(d["potencia_necessaria_kwp"], 1.5929, places=3)
        self.assertEqual(d["modulos"], 4)
        self.assertAlmostEqual(d["geracao_estimada_kwh_mes"], 182.25, places=2)
        self.assertAlmostEqual(d["bateria_kwh"], 12.6, places=2)

    def test_matriz_de_decisao(self):
        self.assertEqual(calculos.matriz_decisao(), {"A": 2.3, "B": 3.25, "C": 4.0})

    def test_sensibilidade_extremos(self):
        s = calculos.sensibilidade(self.p)
        self.assertAlmostEqual(s["Conservador"]["B"]["consumo_kwh_mes"], 244.8)
        self.assertAlmostEqual(s["Favorável"]["B"]["consumo_kwh_mes"], 158.4)

    def test_alertas_detectam_eventos_injetados(self):
        regras = {a["regra"] for a in alertas.aplicar_regras(alertas.ler())[0]}
        self.assertEqual(regras, {"Bateria baixa", "Luminária offline", "Presença sem resposta",
                                  "Consumo acima do esperado", "Baixa geração solar"})


if __name__ == "__main__":
    unittest.main()
