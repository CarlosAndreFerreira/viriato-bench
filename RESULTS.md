# Resultados

Estado a **2026-09-25**. Números gerados por `python3 score.py` a partir do
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
| v1-polygon | **3/3** | 429 s | 6.15 $ | **0/3** | 3000 s (timeout) |
| v2-solar | **3/3** | 458 s | 6.89 $ | **0/3** | 3000 s (timeout) |
| v3-viriato | **3/3** | 486 s | 7.90 $ | **0/3** | 3001 s (timeout) |
| a1-bugfix | **3/3** | 138 s | 4.12 $ | **3/3** | 571 s |

**A grelha está completa** (24 runs, K=3 nos dois lados, 2026-09-24).

- Claude: 12/12 limpos, 25.06 $ de custo equivalente em API.
- `qwen3.8` a temperatura 1: **3/3 no a1-bugfix** (489 · 571 · 813 s, cerca de
  4× o tempo do Claude) e **0/9 nas três tarefas visuais/SRS**. Nas 9 falhas a
  pasta da run ficou **vazia**: nenhum `index.html` nem `maze.py` em 50 min.
- Diferença nas tarefas v1+v2+v3: 9/9 contra 0/9, **Fisher p = 0.00002**.

As runs 2 e 3 do `qwen3.8` correram a 2026-09-24 com kernel 7.0.0-34 e Claude
Code 2.1.276; as runs 1, entre 17 e 20 de setembro, com 7.0.0-31 e 2.1.274
(ver §6.4). Como as 9 runs visuais falharam da mesma maneira nos dois
ambientes, a deriva não muda a leitura.

## 2. Resultado principal: a temperatura desbloqueou o local (nos harnesses leves)

A tag derivada `qwen3.8-t02` só muda a temperatura de 1 para 0.2
(`harness/ollama/qwen3.8-t02.Modelfile`).

| Comparação emparelhada: pi + pi-sol, v1 + v2 | Passes limpos | IC95% |
|---|---|---|
| `qwen3.8`, temperatura 1 | **0/5** | [0%, 43%] |
| `qwen3.8-t02`, temperatura 0.2 | **9/12** | [47%, 91%] |

**Fisher exato unilateral: p = 0.009.** É a única diferença deste bench que é
estatisticamente significativa com o K que existe, fora da comparação direta
Claude contra local. Contando todas as runs visuais a temperatura 1, em
qualquer harness, são **0/16 limpos**.

**O modo de falha a temperatura 1 é raciocínio sem fim, sem ação.** Prova que
sobreviveu em disco (ver §6.2 sobre a que não sobreviveu):

| Run (temperatura 1) | Turnos | Chamadas a ferramentas | Raciocínio | Ficheiros |
|---|---|---|---|---|
| `pi-qwen-v2-solar-1` | 0 | 0 | 113 162 car. | nenhum |
| `pi-sol-qwen-v2-solar-1` | 0 | 0 | 122 194 car. | nenhum |
| claude-code, v1/v2/v3 (5 runs) | — | — | — | nenhum (`index.html`/`maze.py nao existe`) |

A 0.2, os 9 passes limpos escreveram o ficheiro final entre os 517 s e os
2646 s, com 3 a 39 turnos.

**As quatro tarefas no pi** (`qwen3.8-t02`, K=3; a1 e v3 no batch
`pi-t02-v3a1-k3`, 2026-09-25):

| Tarefa | pi + `qwen3.8-t02` | Mediana | claude-code + `qwen3.8` (temp. 1) | claude-code + Claude |
|---|---|---|---|---|
| a1-bugfix | **3/3** | **121 s** | 3/3, 571 s | 3/3, 138 s |
| v1-polygon | **2/3** | 1280 s | 0/3 | 3/3, 429 s |
| v2-solar | **2/3** | 2087 s | 0/3 | 3/3, 458 s |
| v3-viriato | **2/3** | 2843 s | 0/3 | 3/3, 486 s |

- **O v3 tem o primeiro pass limpo local** do bench (1718 s e 2843 s). A
  terceira run deu timeout sem escrever o `maze.py`.
- Nas três tarefas visuais/SRS: 6/9 no pi a 0.2 contra 0/9 no claude-code a
  temperatura 1, **Fisher p = 0.0045**. Esta comparação mistura harness e
  temperatura; o §3.3 separa-os.
- No a1, o local no pi teve mediana de 121 s contra 138 s do Claude. Com K=3
  de cada lado é um empate, não uma vitória.
- Um dos passes no v3 acabou a 157 s do limite (2843 de 3000 s): o resultado
  local continua sensível ao `TIMEOUT_S` (§6.5).

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

### 3.3 No claude-code, a temperatura 0.2 não chega

Batch `cc-t02-k3`, 2026-09-24/25: o harness do PROTOCOL com `qwen3.8-t02`, a
mesma tag que passou nos harnesses leves.

| Tarefa | Run 1 | Run 2 | Run 3 | Limpos |
|---|---|---|---|---|
| v1-polygon | timeout, pasta vazia | timeout, pasta vazia | timeout, pasta vazia | **0/3** |
| v2-solar | pass fora de tempo (ficheiro aos 2641 s) | erro do harness, exit=1 | timeout, pasta vazia | **0/3** |

**0/6 limpos no claude-code contra 9/12 em pi + pi-sol, com o mesmo modelo, a
mesma temperatura e as mesmas tarefas: Fisher p = 0.0045.** O harness conta.
A conclusão do §2 vale para os harnesses leves, não para o claude-code.

O que os logs do Ollama mostram (`journalctl -u ollama`, runs 2–3 do v1):

- **Turnos únicos gigantes voltam.** O primeiro pedido da run 2 tinha 1420
  tokens de prompt (processados em 4.7 s) e demorou **29 minutos** a
  responder (11:10 → 11:39). Nas duas runs houve respostas de 16, 20, 29 e 34
  minutos. No pi, com o mesmo modelo, o maior turno nunca passou de ~15 mil
  caracteres de raciocínio.
- **Pedidos paralelos cortados.** Enquanto o pedido principal corria, o
  Ollama registou *"aborting completion request due to client closing the
  connection"* às 11:16, 11:22, 11:28 e 11:34 — pedidos secundários do Claude
  Code ao mesmo modelo (o stderr regista pelo menos um, `generate_session_title`),
  cortados de 6 em 6 minutos. Com `OLLAMA_NUM_PARALLEL=4` estes pedidos
  disputam a GPU com o principal. No pi: 65 pedidos, 0 cortes.
- **A run 2 do v2 morreu por erro do harness**, não do modelo: dois pedidos de
  ~52 mil tokens cancelados pelo cliente aos ~3 min 15 s, e o Claude Code
  terminou com *"API Error: The response stopped arriving"*.

Por confirmar: qual dos timeouts do Claude Code corta (existem
`CLAUDE_STREAM_FIRST_BYTE_TIMEOUT_MS`, `CLAUDE_STREAM_IDLE_TIMEOUT_MS`,
`CLAUDE_BYTE_STREAM_IDLE_TIMEOUT_MS` e `API_TIMEOUT_MS`), e se desligar os
pedidos secundários mudaria o resultado.

### 3.4 No a1-bugfix

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

**Corrigido a 2026-09-24:** o `bench.sh` passou a usar `runs/<batch_id>/` e
`logs/<batch_id>/`. Testado com a mesma célula em três batches: as três pastas
e os três conjuntos de logs ficam intactos.

### 6.3 Energia nunca foi medida

As **26 673 linhas** de todos os `power*.csv` têm a coluna `watts` vazia. O
RAPL existe, mas `/sys/class/powercap/intel-rapl:0/energy_uj` só é legível como
root (`Permission denied`). A coluna `cpu_temp_c` também está vazia em todas as
linhas, apesar de o `k10temp` ser legível sem root.

Há uma fonte que funciona sem root: `/sys/class/hwmon/hwmon6/power1_average`
(sensor `amdgpu`, label `PPT`), que marcava 120 W durante uma run do
prime-agent. **A parte "a que custo energético" da pergunta do PROTOCOL §1
continua sem resposta para todas as runs até esta data.**

**Primeira medição real (2026-09-24, `power-qwen-k3-20260924.csv`, 9646
amostras, fonte `amdgpu_ppt`), `qwen3.8` em claude-code:**

| Run | Resultado | Duração | Potência média do SoC | Energia do SoC | Temp. máx. |
|---|---|---|---|---|---|
| a1-bugfix, 2 | pass | 489 s | 117.5 W | **16.0 Wh** | 91 °C |
| a1-bugfix, 3 | pass | 813 s | 118.4 W | **26.7 Wh** | 94 °C |
| v1/v2/v3, 6 runs | timeout | 3000 s | 119.2 W | **99.3–99.4 Wh cada** | 88–90 °C |

Um timeout custa ~99 Wh ao SoC sem produzir nada.

Com o `qwen3.8-t02` no pi (`power-pi-t02-v3a1-20260925.csv`): a1-bugfix com
**2.8–3.9 Wh** por pass (91–123 s a ~113 W), contra 16.0–26.7 Wh do `qwen3.8`
no claude-code para o mesmo pass — **5 a 7 vezes menos energia** pelo mesmo
resultado. v3-viriato: 56.7 e 93.8 Wh nos dois passes, 99.3 Wh no timeout. Isto é só o SoC: não inclui
RAM, SSD, ventoinhas nem perdas da fonte, por isso o consumo na tomada é maior.
O lado Claude não tem medida equivalente: corre na cloud.

**Corrigido a 2026-09-24:** o `monitor.py` usa o RAPL se for legível e, se não,
o `amdgpu` PPT, e regista a fonte numa coluna nova, `watts_source`. Mede a
**potência do SoC** (CPU + GPU), não a da tomada: fica de fora RAM, SSD,
ventoinhas e perdas da fonte. Em repouso marca ~15 W e 37 °C. Também corrigidos
dois bugs: a temperatura passou a vir do `k10temp` (a única `thermal_zone` desta
máquina marca 0), e o RAPL só soma os domínios de topo (o glob antigo apanhava
também o subdomínio `intel-rapl:0:0` e, como root, contaria o consumo duas
vezes).

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
- **"A 0.2 o local resolve"**, em geral. Resolve nos harnesses leves; no
  claude-code deu 0/6 limpos (§3.3).
- **Nada sobre o v3-viriato local a 0.2** — nunca correu. O único pass local no
  v3 (`qwen3.8-flash-next`) foi fora de tempo.
- **Nada sobre energia** (§6.3), nem sobre "sem raciocínio" (§6.1).

## 8. O que falta

| # | O que falta | Porquê |
|---|---|---|
| ~~1~~ | ~~`qwen3.8` em claude-code até K=3~~ | **Feito a 2026-09-24** (§1). |
| ~~2~~ | ~~Corrigir o `monitor.py`~~ | **Feito a 2026-09-24** (§6.3). A energia passa a ser medida nas próximas runs; as anteriores continuam sem ela. |
| ~~3~~ | ~~Incluir o `batch_id` nas pastas e logs~~ | **Feito a 2026-09-24** (§6.2). |
| ~~4~~ | ~~claude-code + `qwen3.8-t02`~~ | **Feito a 2026-09-25** (§3.3): 0/6, o harness conta. |
| ~~5~~ | ~~v3 e a1 com `qwen3.8-t02`~~ | **Feito a 2026-09-25 no pi** (§2): a1 3/3, v3 2/3. |
| 6 | Um teste real de "sem raciocínio" | O `pi-off-v1` não o testou (§6.1). Precisa de `reasoning_effort: none` enviado ao Ollama. |

### Memória: correção à explicação do OOM

O `PROTOCOL.md` §2.3 atribui o OOM de 2026-09-22 a três tags carregadas ao
mesmo tempo. Os dados do dia seguinte mostram que isso não chega: a
2026-09-23 às 13:53, **com a máquina acabada de reiniciar e nenhum outro
modelo em memória**, carregar o `qwen3-coder-t02` levou a RAM a **110.2 GiB**
durante 16 s (`power-queue3-20260923.csv`). O OOM de 2026-09-22 aconteceu
exatamente ao carregar esse modelo. Picos das outras filas, um modelo de
cada vez: 45.8–52.8 GiB. **O `qwen3-coder`, sozinho, com contexto de 262144 e
4 slots paralelos, chega perto do limite da máquina.** Não voltar a corrê-lo
sem baixar `num_ctx` ou `OLLAMA_NUM_PARALLEL`.

Infraestrutura: pico de 50 GiB de RAM nas corridas com um modelo de cada vez,
contra os 110 GiB do OOM de 2026-09-22 (`PROTOCOL.md` §2.3).
