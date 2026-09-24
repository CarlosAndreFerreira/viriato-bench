# Resultados

Estado a **2026-09-24**. Números gerados por `python3 score.py` a partir do
`results.csv`; os logs crus estão em `logs/`. O `PROTOCOL.md` é o pré-registo
e não muda com o que está aqui. Cada afirmação abaixo indica a prova.

**Lê a coluna limpa.** Um run cortado pelo `TIMEOUT_S` ainda é pontuado: se os
ficheiros estavam certos no instante em que o processo foi morto, o verificador
dá PASS com o agente ainda a iterar. `score.py` separa `pass_at_1_limpo`
(passes com `timeout_hit=0`, **o que se cita**) de `pass_at_1` (largo).

Intervalos de confiança: Wilson a 95%. Testes: Fisher exato unilateral.

---

## 1. A grelha nuclear do PROTOCOL

claude-code, `claude-opus-5` contra `qwen3.8` (temperatura 1, a de origem), K=3.

| Tarefa | claude-opus-5 | Mediana | Custo | qwen3.8 | Mediana |
|---|---|---|---|---|---|
| v1-polygon | **3/3** | 429 s | 6.15 $ | 0/1 | 3000 s (timeout) |
| v2-solar | **3/3** | 458 s | 6.89 $ | 0/1 | 3000 s (timeout) |
| v3-viriato | **3/3** | 486 s | 7.90 $ | 0/1 | 3001 s (timeout) |
| a1-bugfix | **3/3** | 138 s | 4.12 $ | 1/1 | 571 s |

O lado Claude está completo: 12 runs, 12 passes limpos, 25.06 $ de custo
equivalente em API. Cada célula 3/3 tem IC95% de [44%, 100%]. **O lado
`qwen3.8` continua a K=1** (ver §8).

## 2. Resultado principal: a temperatura desbloqueou o local

A tag derivada `qwen3.8-t02` só muda a temperatura de 1 para 0.2
(`harness/ollama/qwen3.8-t02.Modelfile`).

| Comparação emparelhada: pi + pi-sol, v1 + v2 | Passes limpos | IC95% |
|---|---|---|
| `qwen3.8`, temperatura 1 | **0/5** | [0%, 43%] |
| `qwen3.8-t02`, temperatura 0.2 | **9/12** | [47%, 91%] |

**Fisher exato unilateral: p = 0.009.** É a única diferença deste bench que é
estatisticamente significativa com o K que existe. Contando todas as runs
visuais a temperatura 1, em qualquer harness, são **0/10 limpos**.

**O modo de falha a temperatura 1 é raciocínio sem fim, sem ação.** Prova que
sobreviveu em disco (ver §6.2 sobre a que não sobreviveu):

| Run (temperatura 1) | Turnos | Chamadas a ferramentas | Raciocínio | Ficheiros |
|---|---|---|---|---|
| `pi-qwen-v2-solar-1` | 0 | 0 | 113 162 car. | nenhum |
| `pi-sol-qwen-v2-solar-1` | 0 | 0 | 122 194 car. | nenhum |
| claude-code, v1/v2/v3 (5 runs) | — | — | — | nenhum (`index.html`/`maze.py nao existe`) |

A 0.2, os 9 passes limpos escreveram o ficheiro final entre os 517 s e os
2646 s, com 3 a 39 turnos.

**Ressalva:** as runs a temperatura 1 do pi usaram `PI_THINKING=high`; as a
0.2 usaram o default `medium`. No Ollama 0.33.3 com o qwen3.8 os níveis dão o
mesmo raciocínio (medido a 2026-09-21), por isso não deve pesar — mas é uma
diferença de configuração e fica declarada.

## 3. Harness

### 3.1 O scaffold muda quanto o modelo raciocina

Mesmo modelo (`qwen3.8-t02`), mesma tarefa (`v1-polygon`), K=3 por harness:

| Harness | Ferramentas | Passes limpos | Maior turno de raciocínio, por run |
|---|---|---|---|
| pi | read/write/edit/bash | 2/3 | 10 289 · 15 019 · 13 913 |
| pi-sol | idem + 3 do SoL-Pi | 3/3 | 9 236 · 22 479 · 22 362 |
| prime-agent | só `ipython` | **1/3** | **54 461 · 93 409 · 69 254** |

O menor "maior turno" do prime-agent (54 mil) é mais do dobro do maior de todos
os outros (22 mil): **separação completa, p exato = 0.012** (Mann-Whitney, 3
contra 6). O prime-agent traz de volta os turnos gigantes que a temperatura 0.2
tinha eliminado no pi.

Nos passes limpos a diferença **não** é significativa: prime-agent 1/3 contra
pi+pi-sol 5/6, p = 0.23. O efeito provado é no comportamento, não ainda no
resultado.

### 3.2 O SoL-Pi nunca atuou

Em **9 runs** do pi-sol houve **44 chamadas a `edit`/`write` e nenhuma usou o
`then_run`**; `obs_recall` e `update_plan` foram chamados **0 vezes**; e **não
existe nenhum ficheiro** em `sol-pi/<sessão>/` em nenhuma das 9 sessões, que é
onde o SoL-Pi grava sempre que o ObservationPack ou o redutor atuam.

A extensão estava carregada (confirmado a 2026-09-22: regista `obs_recall` e
`update_plan` e acrescenta `then_run` ao `edit`/`write`), mas **nenhum dos
quatro mecanismos disparou**. Na prática o pi-sol foi o pi com três ferramentas
a mais no prompt. A diferença pi-sol contra pi (5/6 contra 4/6, p = 0.50) é
ruído, e não pode ser atribuída ao SoL-Pi.

### 3.3 No a1-bugfix

| Harness (`qwen3.8`) | Tempo | Turnos | K |
|---|---|---|---|
| claude-code | 451 · 828 · 571 s | 11 · 11 · 12 | 3 batches de 1 |
| pi | 166 s | 8 | 1 |
| prime-agent | 166 s | 6 | 1 |
| pi-sol | 144 s | 5 | 1 |

Os harnesses leves foram 3 a 5 vezes mais rápidos, mas **cada um tem K=1**.
É uma observação, não uma conclusão.

## 4. O modelo especializado em código entregou lixo depressa

`qwen3-coder-t02`, `v1-polygon`: `index.html` escrito aos **87 s**, 2 turnos, 0
caracteres de raciocínio (modelo sem modo de raciocínio). Verificador: *13
amostras com bola fora do polígono, a pior a 4607.7 px*.

## 5. Os verificadores são válidos nos dois sentidos

- **Aceitam o correto:** `make check-reference` a 2026-09-24 — PASS nos três
  (v1, v2, v3).
- **Rejeitam o errado com razões físicas concretas**, em runs reais:
  - `qwen3-coder-t02`, v1: bola a 4607.7 px fora do polígono;
  - `prime-agent`/t02, v1, run 2: 203 amostras fora do polígono (pior 11 px);
  - `pi-sol`/t02, v2, run 1: *"no dia 972 (regresso à Terra) a nave está a
    1.75 UA da posição real esperada, tolerância 0.35 UA"* — com a animação a
    funcionar. É o slide "bonito ≠ correto".
- **Testes do a1:** o `score.sh` repõe `tests/` e `conftest.py` antes do pytest
  e regista qualquer alteração. Nenhuma run foi assinalada; o controlo só
  existe desde 2026-09-21, por isso as runs de a1 anteriores não foram
  vigiadas.

## 6. Problemas de medição encontrados (e o que invalidam)

### 6.1 `PI_THINKING=off` nunca desligou o raciocínio

Capturado com um servidor falso a 2026-09-24: com `--thinking off` o pi **não
envia parâmetro nenhum**; com `--thinking medium` envia
`reasoning_effort: "medium"`. Sem parâmetro, o Ollama deixa o raciocínio
ligado. O batch `pi-off-v1` teve 57 885 caracteres de raciocínio. **Esse batch
não testou "sem raciocínio"** — correu com o raciocínio ligado como qualquer
outro, e não suporta nenhuma conclusão sobre desligá-lo.

### 6.2 Evidência sobrescrita entre batches

O `bench.sh` nomeia pastas e logs por `agent-side-task-k`, sem o `batch_id`.
Quando a mesma célula corre noutro batch, a evidência do primeiro é apagada.
**Seis células foram afetadas**, por exemplo:

| Pasta | CSV (batch mais antigo) | O que está hoje em disco |
|---|---|---|
| `pi-qwen-v1-polygon-1` | `pi-high-v1v2`: 0 turnos | 29 turnos (é do `pi-off-v1`) |
| `pi-qwen3.8-t02-v1-polygon-1` | `sampling-v1`: 19 turnos | 18 turnos (é do `t02-k3-pi`) |
| `claude-code-qwen3.8-flash-next-a1-bugfix-1` | pass=0 | `.score` com 7 passed (do batch seguinte) |

As linhas do `results.csv` estão corretas; o que se perdeu foram os logs e as
pastas por trás delas. As afirmações acima só citam evidência que sobreviveu.

### 6.3 Energia nunca foi medida

As **26 673 linhas** de todos os `power*.csv` têm a coluna `watts` vazia. O
RAPL existe, mas `/sys/class/powercap/intel-rapl:0/energy_uj` só é legível como
root (`Permission denied`). A coluna `cpu_temp_c` também está vazia em todas as
linhas, apesar de o `k10temp` ser legível sem root.

Há uma fonte que funciona sem root: `/sys/class/hwmon/hwmon6/power1_average`
(sensor `amdgpu`), que marcava 120 W durante uma run do prime-agent. **A parte
"a que custo energético" da pergunta do PROTOCOL §1 continua sem resposta.**

### 6.4 Deriva de ambiente durante as corridas

| | PROTOCOL §2 | Agora |
|---|---|---|
| Kernel | 7.0.0-31 | **7.0.0-34** (reboot de 2026-09-23 13:45) |
| Claude Code | 2.1.274 | **2.1.276** (atualização automática) |
| Ollama | 0.33.3 | 0.33.3 |
| pi | 0.84.2 | 0.84.2 |

Correram com 2.1.276 as runs do Claude no a1 e as runs 2–3 do v3; o v1 e o v2
correram com 2.1.274.

### 6.5 Os resultados locais dependem do timeout escolhido

Momento em que o ficheiro final foi escrito, nos passes limpos:

- **Claude:** 263–491 s. Nenhum perto do limite.
- **Local, `qwen3.8-t02`:** 517 · 554 · 683 · 1188 · 1627 · 1654 · 1970 · 2054
  · 2465 · 2646 s. **2 dos 10 acima dos 2400 s**, a menos de 10 minutos do
  corte.

Com `TIMEOUT_S=2400` o local perderia pelo menos 2 passes; com um timeout
maior, alguns dos 4 passes fora de tempo passariam a limpos. O pass@1 local é,
em parte, uma medida do timeout.

## 7. O que estes números NÃO suportam

- **Ordenar harnesses por taxa de acerto.** Nenhuma comparação entre harnesses
  é significativa (pi-sol contra pi p = 0.50; prime-agent contra pi+pi-sol
  p = 0.23).
- **"O local iguala o frontier."** O Claude fez 12/12 limpos em 124–515 s. O
  local, no melhor caso, 9/12 nas tarefas visuais, 2 a 6 vezes mais lento.
- **"A 0.2 o local resolve"**, em geral. Só foi medido no pi, pi-sol e
  prime-agent. O claude-code a 0.2 nunca correu.
- **Nada sobre o v3-viriato local a 0.2** — nunca correu. O único pass local no
  v3 (`qwen3.8-flash-next`) foi fora de tempo.
- **Nada sobre energia** (§6.3), nem sobre "sem raciocínio" (§6.1).

## 8. O que falta

| # | O que falta | Porquê |
|---|---|---|
| 1 | `qwen3.8` (temperatura 1) em claude-code até K=3, nas 4 tarefas | A grelha nuclear do PROTOCOL exige K=3; hoje está a K=1. |
| 2 | Corrigir o `monitor.py` para ler `amdgpu/power1_average` e `k10temp` | Sem isto, a pergunta do PROTOCOL §1 sobre energia não tem resposta. |
| 3 | Incluir o `batch_id` nos nomes de pasta e log do `bench.sh` | Para não voltar a perder evidência (§6.2). |
| 4 | claude-code + `qwen3.8-t02`, v1 e v2, K=3 | Separa o efeito da temperatura do efeito do harness. |
| 5 | v3 e a1 com `qwen3.8-t02` | O resultado principal só está medido em 2 das 4 tarefas. |
| 6 | Um teste real de "sem raciocínio" | O `pi-off-v1` não o testou (§6.1). Precisa de `reasoning_effort: none` enviado ao Ollama. |

Infraestrutura: pico de 50 GiB de RAM nas corridas com um modelo de cada vez,
contra os 110 GiB do OOM de 2026-09-22 (`PROTOCOL.md` §2.3).
