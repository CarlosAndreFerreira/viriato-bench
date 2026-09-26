# Resultados

Estado a **2026-09-26**. Números gerados por `python3 score.py` a partir do
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

> **Correção de 2026-09-26 (§6.7):** nos harnesses desta secção (pi, pi-sol) a
> temperatura 0.2 **nunca chegou ao modelo**. O `/v1/chat/completions` do
> Ollama ignora a temperatura do Modelfile, e os dois braços correram com a
> mesma amostragem. Os números abaixo estão certos; a atribuição à temperatura
> não está.

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
  local continua sensível ao `TIMEOUT_S` (§6.6).

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

> **Correção de 2026-09-26 (§6.7):** o claude-code é o único harness onde o
> `qwen3.8-t02` correu de facto a 0.2. No pi correu ao default do `/v1`, por
> isso a comparação abaixo não é "à mesma temperatura".

Batch `cc-t02-k3`, 2026-09-24/25: o harness do PROTOCOL com `qwen3.8-t02`, a
mesma tag que passou nos harnesses leves.

| Tarefa | Run 1 | Run 2 | Run 3 | Limpos |
|---|---|---|---|---|
| v1-polygon | timeout, pasta vazia | timeout, pasta vazia | timeout, pasta vazia | **0/3** |
| v2-solar | pass fora de tempo (ficheiro aos 2641 s) | erro do harness, exit=1 | timeout, pasta vazia | **0/3** |

**0/6 limpos no claude-code contra 9/12 em pi + pi-sol, com o mesmo modelo, a
mesma temperatura e as mesmas tarefas: Fisher p = 0.0045.** O harness conta.
A conclusão do §2 vale para os harnesses leves, não para o claude-code.

O que os logs do Ollama mostram (`journalctl -u ollama`, run 2 do v1):

- **O Ollama correu com um único slot.** As 7167 linhas de slot entre
  2026-09-24 23:00 e 2026-09-25 15:15 são todas do slot 0: os pedidos ficam
  em fila, não correm em paralelo.
- **Um pedido secundário do Claude Code ocupou o slot durante 29 minutos.**
  O primeiro pedido tinha 1420 tokens e nenhuma ferramenta — não é o agente,
  é o pedido que gera o resumo/título da sessão (capturado com um servidor
  falso: `max_tokens` 3072, sem ferramentas, *"A user kicked off a Claude Code
  agent to do a coding task…"*). O modelo gerou ~31 mil tokens para ele, das
  11:10 às 11:39.
- **O pedido do agente ficou na fila atrás dele e foi cortado de 6 em 6
  minutos.** O Ollama registou *"aborting completion request due to client
  closing the connection"* às 11:16, 11:22, 11:28, 11:34 e 11:40: o Claude
  Code desiste de um pedido sem primeiro byte ao fim de ~6 min e volta a
  tentar. O pedido do agente (22 494 tokens) só começou a ser processado às
  11:39 — **29 dos 50 minutos da run foram gastos no título da sessão.**
- **O pi não faz pedidos secundários**: 65 pedidos em 6 runs, 0 cortes.
- **A run 2 do v2 morreu por erro do harness**, não do modelo: dois pedidos de
  ~52 mil tokens cancelados pelo cliente aos ~3 min 15 s, e o Claude Code
  terminou com *"API Error: The response stopped arriving"*.

Uma versão anterior desta secção dizia que os pedidos secundários
"disputam a GPU em paralelo". Estava errado: com um único slot, bloqueiam.

**Teste da hipótese: sem pedidos secundários** (batch `cc-t02-noness-k3`,
2026-09-25, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`, v1, K=3). Capturado
com um servidor falso antes de correr: a variável reduz os pedidos de 3 para
1, **mas também reduz as ferramentas nativas do pedido principal de 33 para
23** — os dois efeitos não se separam.

| Run | Resultado | Pedidos ao Ollama (duração) |
|---|---|---|
| 1 | pass fora de tempo (`index.html` aos 2158 s) | 30 min 47 s · 5 min · 5 min · 9 min |
| 2 | timeout, pasta vazia | **32 min** · 18 min |
| 3 | timeout, pasta vazia | **33 min** · 17 min |

- **0/3 limpos.** A variável eliminou os pedidos secundários e os cortes (0
  nas três runs), e deu o primeiro `index.html` válido do claude-code com um
  modelo local no v1 — mas fora de tempo.
- **O primeiro turno gigante é do próprio pedido do agente**: 31–33 minutos
  nas três runs, sem nenhum pedido secundário à frente. Na run 1, esse turno
  gerou ~32 mil tokens (17 835 → 49 834 tokens no slot), praticamente o
  `max_tokens: 32000` que o Claude Code envia — pista, não conclusão, de que
  só parou por bater no limite.
- **Conclusão:** o pedido do título agravava a falha (na run 2 do batch
  anterior roubou 29 minutos), mas não era a causa. A causa está no pedido
  principal do claude-code. Contra pi+pi-sol no v1 (5/6): **Fisher p = 0.048**.

**O que difere entre os pedidos** (capturados a 2026-09-25 com um servidor
falso, nas condições do bench: mesmas flags do `bench.sh`, cópia da pasta do
v1, dentro de uma unidade do systemd; nenhum modelo carregado):

| | claude-code: título da sessão | claude-code: agente | pi: agente |
|---|---|---|---|
| Corpo do pedido | 6.5 KB | **89 KB** | 10.6 KB |
| Ferramentas | 0 | 26 | 7 |
| Limite de saída | `max_tokens` 32 000 | `max_tokens` 32 000 | `max_completion_tokens` 32 768 |
| Raciocínio | `output_config.effort: high` | `thinking: adaptive` + **`effort: high`** | `reasoning_effort: medium` |

- **O pedido do título pede esforço `high` e até 32 000 tokens** para gerar
  uma frase — o que explica os 29 minutos que ocupou o slot.
- **O agente do claude-code pede esforço `high`; o do pi, `medium`.**
- O Ollama 0.33.3 reconhece o `output_config` da API da Anthropic (a
  estrutura `anthropic.OutputConfig` está no binário), mas não foi possível
  confirmar como traduz o esforço ou o `thinking: adaptive` para o modelo.

Controlos do Claude Code, confirmados na captura:

| Configuração | `thinking` | `effort` |
|---|---|---|
| Por omissão | `adaptive` | `high` |
| `--effort medium` | `adaptive` | `medium` |
| `MAX_THINKING_TOKENS=4000` | `adaptive` | `high` — **não muda o pedido** |
| `CLAUDE_CODE_DISABLE_THINKING=1` | (retirado) | `high` |

**Teste do esforço** (batch `cc-t02-noness-effmed-k3`, 2026-09-25/26,
`CC_EFFORT=medium` + `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`, v1, K=3).
Igual ao `cc-t02-noness-k3` em tudo menos no esforço do agente (`high` →
`medium`). Com `--effort medium` o pedido do título continua em `high`
(capturado), por isso os pedidos secundários ficaram desligados nos dois. A
run 3 original perdeu-se quando o PC foi desligado e foi repetida a 2026-09-26
com a mesma configuração (`K_START=3`).

| claude-code + `qwen3.8-t02`, v1 | Run 1 | Run 2 | Run 3 | Limpos | Ficheiro válido |
|---|---|---|---|---|---|
| com pedidos secundários, `high` (`cc-t02-k3`) | falha | falha | falha | 0/3 | 0/3 |
| sem pedidos secundários, `high` (`cc-t02-noness-k3`) | fora de tempo (2158 s) | falha | falha | 0/3 | 1/3 |
| sem pedidos secundários, **`medium`** | **limpo (1846 s)** | fora de tempo (2162 s) | fora de tempo (2761 s) | **1/3** | **3/3** |

Primeiro turno do agente (duração da primeira resposta no Ollama):

| Esforço | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `high` | 30 min 47 s | 32 min | 33 min |
| `medium` | **20 min 39 s** | **11 min 52 s** | 33 min 7 s |

- **O único pass limpo do claude-code com um modelo local numa tarefa visual**
  saiu desta configuração (run 1, 2330 s).
- **As três runs a `medium` produziram um `index.html` válido**, contra 1 de 3
  a `high` e 0 de 3 com pedidos secundários. A direção é consistente em cada
  passo (tirar o título, baixar o esforço), mas **com K=3 nenhuma diferença é
  significativa**: 1/3 contra 0/3 limpos, p = 0.5; 3/3 contra 1/3 com
  ficheiro válido, p = 0.2.
- O esforço `medium` encurtou o primeiro turno em duas runs e não na terceira
  (33 min, igual ao `high`). **O Ollama traduz o `effort`** — senão as três
  seriam iguais às do `high` —, mas o turno longo continua a aparecer.
- Mesmo na melhor configuração, o claude-code fica atrás do pi com o mesmo
  modelo (pi 2/3 e pi-sol 3/3 limpos no v1, com primeiros turnos muito mais
  curtos). A diferença que sobra está no pedido em si: 89 KB e 26 ferramentas
  contra 10.6 KB e 7.

**Teste do tamanho do pedido: claude-code "magro"** (batch `cc-lean-t02-k3`,
2026-09-26). Igual ao anterior (`qwen3.8-t02`, `--effort medium`, sem pedidos
secundários), mas com `--tools Read,Write,Edit,Bash,Glob,Grep` e
`--system-prompt` com o prompt de sistema do pi, capturado
(`harness/claude-code-pi-system-prompt.txt`, sem a linha da pasta de
trabalho). O pedido baixou de 89 KB para **17.6 KB** (o do pi tem 10.6 KB);
o primeiro prompt que chegou ao Ollama tinha **4428 tokens**, contra 17 835.

| Run | Resultado | Primeiro turno |
|---|---|---|
| 1 | **limpo, 1757 s** | 13 min 42 s |
| 2 | **limpo, 691 s** | 8 min 58 s |
| 3 | **limpo, 741 s** | 9 min 38 s |

- **3/3 limpos** — o mesmo nível do pi (2/3) e do pi-sol (3/3) com o mesmo
  modelo. Contra as outras 9 runs do claude-code + `qwen3.8-t02` no v1 (1/9
  limpos): **Fisher p = 0.018**. Contra a melhor configuração anterior
  (1/3): p = 0.2.
- **O ciclo do agente do Claude Code não era o problema; o pedido era.** Com
  as mesmas instruções e ferramentas equivalentes às do pi, o claude-code
  resolve o v1 com o modelo local. O que o prejudicava era o pedido de origem:
  prompt de sistema longo e 26 ferramentas.
- O que este teste não separa: o efeito do prompt de sistema e o das
  ferramentas (mudaram os dois juntos). O prompt usado diz "operating inside
  pi" — é o texto do pi, sem adaptação.

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

### 6.5 O esforço fixado no PROTOCOL nunca foi aplicado — e as runs correram a `high`

O `PROTOCOL.md` §2 fixa `reasoning_effort: medium` e deixa a nota "não
aplicado — confirmar se existe uma flag". **A flag existe (`claude
--effort`), e o `bench.sh` nunca a passou.** Capturado a 2026-09-25: sem ela,
o Claude Code envia `output_config.effort: "high"`. Portanto **todas as runs
com `AGENT=claude-code` correram a esforço `high`**, contra o `medium`
pré-registado — **incluindo as do Claude**. No lado Claude isto significa mais
raciocínio (e mais custo) do que o protocolo previa; no lado local, o efeito
depende da forma como o Ollama traduz o campo, que não foi confirmada.

**Grelha do Claude repetida com o esforço pré-registado** (batch
`claude-effmed-k3`, 2026-09-26, `--effort medium`, `claude-opus-5`):

| Tarefa | `high` (grelha original) | `medium` (pré-registado) |
|---|---|---|
| a1-bugfix | 3/3, 138 s, 4.12 $ | 3/3, 136 s, 3.02 $ |
| v1-polygon | 3/3, 429 s, 6.15 $ | 3/3, 348 s, 5.72 $ |
| v2-solar | 3/3, 458 s, 6.89 $ | 3/3, 435 s, 5.44 $ |
| v3-viriato | 3/3, 486 s, 7.90 $ | **2/3**, 309 s, 4.56 $ |
| **Total** | **12/12, 25.06 $** | **11/12, 18.72 $** |

A falha a `medium` (v3, run 3) foi um erro de código, não de tempo: o
`maze.py` usa uma constante que nunca define (`NameError: MAX_CORRIDOR`) nas 4
seeds, e não expõe `render()`. A `medium` o Claude ficou 25% mais barato e
ligeiramente mais rápido, com uma falha em 12. 11/12 contra 12/12 não é uma
diferença significativa (p = 0.5), mas o "12/12" do slide foi medido a `high`
e deve ser apresentado como tal.

### 6.6 Os resultados locais dependem do timeout escolhido

Momento em que o ficheiro final foi escrito, nos passes limpos:

- **Claude:** 263–491 s. Nenhum perto do limite.
- **Local, `qwen3.8-t02`:** 517 · 554 · 683 · 1188 · 1627 · 1654 · 1970 · 2054
  · 2465 · 2646 s. **2 dos 10 acima dos 2400 s**, a menos de 10 minutos do
  corte.

Com `TIMEOUT_S=2400` o local perderia pelo menos 2 passes; com um timeout
maior, alguns dos 4 passes fora de tempo passariam a limpos. O pass@1 local é,
em parte, uma medida do timeout.

### 6.7 O `/v1/chat/completions` do Ollama ignora a temperatura do Modelfile

**Medido a 2026-09-26, Ollama 0.33.3.** Quando o pedido não traz
`temperature`, o endpoint compatível com OpenAI **não usa a do Modelfile**. O
endpoint nativo (`/api/chat`) e o compatível com Anthropic (`/v1/messages`)
usam-na. Prova (`verify/ollama_v1_temperature_probe.py`, o mesmo pedido curto
repetido, raciocínio desligado):

| Tag (temperatura do Modelfile) | Endpoint | Respostas distintas |
|---|---|---|
| `minicpm5:2b` derivada, **temperature 0**, sem seed | `/api/chat` | **1/8** |
| idem | `/v1/chat/completions`, sem `temperature` | **8/8** |
| idem | `/v1/chat/completions`, `top_p: 1` (o que o opencode envia) | 8/8 |
| idem | `/v1/messages` (o que o claude-code envia) | **1/6** |
| `qwen3.8-t02` (**0.2**) | `/api/chat` | 6/8, todas *"I call it the Velvet…"* |
| idem | `/v1/chat/completions`, sem `temperature` | **8/8, nenhuma igual às do `/api/chat`** |
| idem | `/v1/chat/completions`, `temperature: 0.2` | 4/8, **3 iguais palavra a palavra** às do `/api/chat` |

A temperatura 0 é o caso limpo: determinística pelo Modelfile, aleatória pelo
`/v1`. No `qwen3.8-t02`, enviar `temperature: 0.2` explicitamente reproduz as
frases do endpoint nativo; omiti-la não reproduz nenhuma.

**Quem usa o quê:**

| Harness | Endpoint | Envia `temperature`? | Temperatura efetiva do `qwen3.8-t02` |
|---|---|---|---|
| claude-code | `/v1/messages` | não | **0.2** (Modelfile) |
| pi, pi-sol, prime-agent | `/v1/chat/completions` (`harness/*/models.json`) | não (captura do PROTOCOL 2.2) | **não é 0.2**: é o default do `/v1`, igual ao do `qwen3.8` |
| opencode (de origem) | `/v1/chat/completions` | não, mas envia `top_p: 1` | idem |

Recapturado a 2026-09-26 com `verify/fake_openai_server.py`, com a config de
`harness/<agente>` e as flags do `bench.sh`, pedindo explicitamente
`--model qwen3.8-t02:latest`: o pi, o pi-sol e o prime-agent enviam só
`model`, `messages`, `tools`, `max_completion_tokens`, `reasoning_effort`,
`store` e `stream`/`stream_options`. **Nenhum envia `temperature`, `top_p` ou
`top_k`**, e nenhum `models.json` define amostragem por modelo. Nas datas das
runs o Ollama já era o 0.33.3 (binário de 2026-09-03; o journal de 21 a 26 de
setembro só regista essa versão) e o pi e o prime-agent já estavam instalados
na versão atual (2026-08-16 e 2026-08-12).

**O que isto invalida:**

1. **O §2 não mede a temperatura.** No pi, pi-sol e prime-agent, `qwen3.8` e
   `qwen3.8-t02` correram com a mesma amostragem. A diferença 0/5 contra 9/12
   (p = 0.009) existe entre esses batches, mas **não pode ser atribuída à
   temperatura**. O que ainda difere entre os braços: `PI_THINKING` (`high`/`off`
   contra `medium`), as datas (22–23 contra 23–25 de setembro) e o nome da tag.
   A causa fica em aberto.
2. **O §3.3 compara temperaturas diferentes, não iguais.** O claude-code correu
   o `qwen3.8-t02` a 0.2; o pi correu-o ao default do `/v1`. O pi ganhou
   (9/12 contra 0/6) **sem** a temperatura baixa. Isto reforça que o harness
   conta, mas a frase "mesma temperatura" estava errada.
3. **A única comparação de temperatura válida do bench é no claude-code**: v1 e
   v2, `qwen3.8` 0/6 limpos contra `qwen3.8-t02` 0/6 limpos. Nenhum efeito
   detetado, e com esse K nenhum efeito pequeno seria detetável.

A correção para o opencode está no `bench.sh` (2026-09-26): o harness lê a
temperatura e o `top_p` do Modelfile da tag e envia-os explicitamente
(capturado com `verify/fake_openai_server.py`: `qwen` → `temperature: 1`,
`qwen3.8-t02` → `temperature: 0.2`, ambos `top_p: 0.95`, mesmas 6
ferramentas). O pi, o pi-sol e o prime-agent não foram corrigidos: mudá-los
agora cortava a comparabilidade com as runs já feitas.

## 7. O que estes números NÃO suportam

- **Ordenar harnesses por taxa de acerto.** Nenhuma comparação entre harnesses
  é significativa (pi-sol contra pi p = 0.50; prime-agent contra pi+pi-sol
  p = 0.23).
- **"O local iguala o frontier."** O Claude fez 12/12 limpos em 124–515 s. O
  local, no melhor caso, 9/12 nas tarefas visuais, 2 a 6 vezes mais lento.
- **"A 0.2 o local resolve".** Nos harnesses leves a 0.2 nunca chegou ao
  modelo (§6.7); no claude-code, onde chegou, deu 0/6 limpos (§3.3).
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
