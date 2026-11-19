# Praça Solar Inteligente — contribuição de SERS ao Neighborhood Action Dashboard

**GS 2026.2 · CitizenTech · Soluções em Energias Renováveis e Sustentáveis (SERS) · Ciência da Computação, turma 1CCPR · FIAP**

## Integrantes

| Nome | RM |
|---|---|
| Gustavo Freire | 561334 |
| João Miguel Barrionuevo Mantovani | 576397 |
| Edson Almeida | 575257 |

**Vídeo técnico (YouTube, não listado):** [COLE AQUI O LINK]

> Este repositório contém a contribuição de SERS. Se for compartilhado com outras disciplinas da GS, tudo o que é de SERS está nesta pasta e identificado por "energia".

## Problema

Uma praça comunitária de médio porte, em um bairro de São Paulo (cenário simulado), mantém 20 luminárias de 100 W acesas 12 h por noite, sem controle. Isso gera consumo e custo desnecessários, mais manutenção e emissões, e a administração não tem visão consolidada de consumo, falhas e economia para saber se uma troca por LED ou solar funcionou.

**Público:** moradores, crianças, idosos, praticantes de atividade física e trabalhadores que atravessam a praça à noite; indiretamente, a administração pública.

## Solução

Três alternativas para a mesma necessidade (iluminar a praça 12 h por noite, 30 noites):

| Alternativa | Descrição | Consumo | Energia da rede | Custo mensal da rede |
|---|---|---:|---:|---:|
| A — Convencional (referência) | 20 × 100 W, sem controle | 720,0 kWh | 720,0 kWh | R$ 612,00 |
| B — LED inteligente | 20 × 40 W com sensores; modo econômico reduz 30% | 201,6 kWh | 201,6 kWh | R$ 171,36 |
| C — Praça Solar Inteligente | B + 4 módulos de 450 Wp, controlador, baterias e monitoramento | 201,6 kWh | 40,32 kWh | R$ 34,27 |

Recomendação: implantar B nos 20 pontos e fazer um piloto solar em 4 luminárias, expandindo se as cotações ficarem dentro dos limites de investimento calculados (a camada solar acrescenta R$ 1.645,06/ano de economia sobre B). Detalhes, matriz de decisão, sensibilidade e plano de validação estão no relatório em `docs/`.

## Estrutura do repositório

```
dados/parametros.json          premissas, unidades, classe (dado público, premissa ou meta) e fonte
dados/leituras_simuladas.csv   600 leituras simuladas (30 noites x 20 luminárias)
dados/indicadores.json         saída dos cálculos (gerada)
dados/alertas.json             saída das regras de alerta (gerada)
src/calculos.py                consumo, custo, emissões, dimensionamento solar, matriz e sensibilidade
src/gerar_leituras.py          gera as leituras simuladas (semente fixa)
src/alertas.py                 aplica as regras de alerta e resume a operação
src/gerar_dashboard.py         monta o dashboard a partir dos dados
dashboard/index.html           dashboard de energia (abrir no navegador)
tests/test_calculos.py         testes automáticos
docs/                          relatório em PDF e figuras (inclui o diagrama de funcionamento)
```

## Como executar

Precisa apenas de Python 3 (sem bibliotecas extras). Na pasta do repositório:

```bash
python3 src/calculos.py                          # cálculos e indicadores (no Windows: python ou py)
python3 src/gerar_leituras.py                    # leituras simuladas
python3 src/alertas.py                           # alertas e resumo da operação
python3 src/gerar_dashboard.py                   # gera dashboard/index.html
python3 -m unittest discover -s tests -v         # testes
```

Depois abra `dashboard/index.html` no navegador. Os três controles no topo (tarifa, redução pelo modo econômico, participação solar) recalculam as alternativas, os gráficos e os indicadores na hora.

## Cálculos

- Energia: `E = P × t × n ÷ 1000` (kWh), com P em W, t em h e n em unidades.
- Dimensionamento solar: `P(kWp) = E ÷ (HSP × dias × PR)`, com E = 80% da carga de B → 1,59 kWp → 4 módulos de 450 Wp → 182,25 kWh/mês (13% acima da meta).
- Bateria: `C = energia por noite × noites de autonomia ÷ profundidade de descarga` = 6,72 × 1,5 ÷ 0,80 = 12,6 kWh (≈ 12,8 kWh nominais).
- Emissões evitadas: energia da rede evitada × 0,0385 kg CO₂/kWh.
- Limite de investimento extra de C sobre B: economia anual adicional (R$ 1.645,06) × horizonte = R$ 8.225 (5 anos), R$ 16.451 (10 anos), R$ 41.126 (25 anos).
- Matriz de decisão ponderada: A 2,30 · B 3,25 · C 4,00; com pesos alternativos B e C empatam em 3,70.

## Indicadores do dashboard

| Indicador | Unidade | Cálculo | Base (A / B / C) |
|---|---|---|---|
| Consumo mensal | kWh/mês | energia da rede + solar | 720 / 201,6 / 201,6 |
| Economia energética | % | 1 − consumo ÷ consumo de A | 0 / 72 / 72 |
| Custo da energia da rede | R$/mês | energia da rede × tarifa | 612,00 / 171,36 / 34,27 |
| Participação renovável | % | energia solar ÷ consumo total | 0 / 0 / 80 |
| Emissões evitadas | kg CO₂/mês | (consumo de A − energia da rede) × 0,0385 | 0 / 20,0 / 26,2 |
| Disponibilidade | % | tempo ativo ÷ tempo monitorado | medido nas leituras |
| Autonomia da bateria | horas | energia disponível ÷ carga média | estimada nas leituras |
| Alertas de manutenção | quantidade | contagem pelas regras abaixo | nas leituras |

Regras de alerta: bateria < 20% (alta); luminária offline (alta); presença sem resposta do LED (alta); consumo > 120% da média (média); geração solar < 70% da previsão (média).


## Dados e fontes

As premissas estão em `dados/parametros.json`, cada uma classificada:

- **Dado público:** fator de emissão do SIN em 2023, 38,5 kg CO₂/MWh (MCTI) [5].
- **Premissa:** número de luminárias, potências, horas de operação, redução de 30% pelo modo econômico, tarifa de R$ 0,85/kWh (conferir na tarifa homologada pela ANEEL [3]), irradiação de 4,5 kWh/m².dia (substituir pelo SunData para as coordenadas da praça [1]) e desempenho fotovoltaico de 0,75.
- **Dados simulados:** `dados/leituras_simuladas.csv` é gerado por `src/gerar_leituras.py` com semente fixa e eventos injetados de propósito (dias nublados, luminária offline, falha de resposta à presença, consumo alto e bateria baixa) para o dashboard ter o que alertar. Não são medições.

## Referências

1. CRESESB — Potencial Solar: SunData v3.0. cresesb.cepel.br/sundata
2. Ministério de Minas e Energia — Selo Procel chega às lâmpadas LED.
3. ANEEL — Tarifas e Informações Econômico-Financeiras.
4. ANEEL — Bandeiras Tarifárias.
5. MCTI — fator médio de emissão de CO₂ do SIN em 2023: 38,5 kg CO₂/MWh, segundo a reportagem da Eixos "Brasil tem menor taxa de emissão de carbono na geração elétrica em onze anos".

## Limitações

- Todos os números são projeções condicionadas às premissas, não resultados garantidos.
- Não há cotações reais; o repositório calcula quanto o conjunto solar pode custar a mais que B para se pagar, em vez de inventar preços.
- O dimensionamento não é projeto executivo: falta irradiância local, orientação, inclinação, sombreamento, tensão e corrente do conjunto, e normas aplicáveis.
- As leituras são diárias e simuladas; em produção, "offline" seria "sem leitura por 15 minutos".
- A geração varia com clima e estação; baterias têm vida útil limitada; o dashboard depende de conectividade.
- Como a matriz elétrica brasileira já é de baixa emissão, o benefício de CO₂ é pequeno perto do ganho de custo.

## Integração com o projeto da GS

Proposta: uma luminária em falha ou offline vira uma ocorrência de iluminação priorizada, e os cartões de energia entram ao lado dos indicadores de ocorrências do dashboard do bairro. Em dias de chuva forte, alertas de falha podem ser cruzados com as áreas de risco de alagamento. Nesta entrega, o dashboard de energia é independente (`dashboard/index.html`).

## Uso de IA

O Claude (Anthropic) foi usado como apoio para rascunhar o relatório, o código, os testes e este README. [CONFIRME: quem do grupo executou os scripts, conferiu os cálculos e leu o código.] As premissas, a escolha da praça e a recomendação são decisões do grupo.
