# Protocolo — modelos locais (Qwen3.8, Qwen3-Coder, Qwen3.8-Flash-Next) vs Claude, mesma harness

**Pré-registado em:** 2026-09-17
**Regra:** nada neste ficheiro muda depois da primeira run. Se mudares, a corrida
recomeça do zero. É isto que separa um benchmark de uma anedota.

**Nota de reinício (2026-09-17):** a Fase 0 (smoke test, `a1-bugfix`/`qwen`)
correu com `TIMEOUT_S=900s` e bateu no timeout — `agent_exit=124` — apesar de
a correção em `schedule.py` estar certa (ancorou `occurrences()` a
`rec.start` em vez de encadear a partir da última ocorrência, o fix de
duas camadas que a tarefa exige; 7/7 testes passaram). O processo só não
devolveu o resumo JSON a tempo. Isto confirma que os 900s pré-registados
eram curtos face à própria estimativa do README §4 (20–50 min/tarefa).
Essa é exatamente a condição da regra acima: `TIMEOUT_S` subiu para 3000s
(50 min, o limite superior já documentado, não um número novo), e
`runs/`, `logs/` e `results.csv` dessa corrida foram apagados antes de
qualquer Fase 1/2 a sério. Fica registado aqui em vez de reescrito em
silêncio.

---

## 1. Pergunta

Não é "o Qwen3.8-27B é tão bom como o Claude?". É:

> **Que fração de tarefas de engenharia reais consigo mover para hardware local,
> a que latência, a que custo energético, e onde é que isso parte?**

A primeira pergunta não é respondível com 4 tarefas. A segunda é, e é a que
interessa a quem está na sala.

## 2. Configuração fixa

| Parâmetro | Valor | Preencher |
|---|---|---|
| Máquina | ACEMAGIC M1A PRO+, Ryzen AI MAX+ 395, 128 GB UMA | confirmado: `lscpu` → "AMD RYZEN AI MAX+ 395 w/ Radeon 8060S"; `/proc/meminfo` → 128650716 kB (~123 GiB) |
| SO / kernel | Ubuntu 26.04, kernel ... | Ubuntu 26.04.1 LTS (resolute), kernel 7.0.0-31-generic |
| Claude Code version | `claude --version` | 2.1.274 (Claude Code) |
| Modelo Claude | `claude-opus-5` (fixa explicitamente) | decidido: `claude-opus-5` — é o exemplo já usado no README §Fase 1, e é o modelo de topo da Anthropic no momento do pré-registo, o que dá o enquadramento mais forte para "quanto é que o local aproxima do frontier". `CLAUDE_MODEL` não tem default em `bench.sh`; **exporta `CLAUDE_MODEL=claude-opus-5` antes de correr a Fase 1** — sem isso corre-se com o default do CLI, não com o valor fixado aqui. |
| Ollama version | `ollama --version` | 0.33.3 |
| Modelo local | `qwen3.8` | `qwen3.8:latest` (id `22130167c4c2`, 17 GB) — confirmado com `ollama list` |
| Quant | Q4_K_M (NÃO Q8 — ver §6) | Q4_K_M — confirmado com `ollama show qwen3.8` |
| Context | >= 32768 | 262144 nativo do modelo (`ollama show qwen3.8`). **Nota:** `bench.sh` não passa `num_ctx` explícito; corre com o default do Ollama, não com um valor fixado pelo harness. |
| `reasoning_effort` | `medium` (fixo, registado em todas as runs) | **não aplicado.** `bench.sh` não passa nenhuma flag de reasoning effort ao `claude` CLI — confirmar se existe uma flag para fixar isto antes de declarar "medium" em qualquer slide, ou remover a linha. |
| Temperatura (lado Qwen) | fixa | 1 (default do model file, `ollama show qwen3.8` → Parameters.temperature). Não é definida pelo `bench.sh`; é o que o Ollama aplica por omissão. |
| Temperatura / seed (lado Claude) | **não controlável via CLI** | n/a |
| k (runs por tarefa por lado) | 3 | confirmado: `K="${K:-3}"` em `bench.sh` |
| Timeout por run | 3000 s (50 min) | confirmado: `TIMEOUT_S="${TIMEOUT_S:-3000}"` em `bench.sh`. Subido de 900s após a Fase 0 — ver nota no topo do documento. |
| Permissões | idênticas nos dois lados | confirmado: `PERM_MODE="${PERM_MODE:-acceptEdits}"` aplicado igualmente a `side=claude` e a todos os `side` locais em `bench.sh` |

**Identidade exata do modelo local (nota de 2026-09-26).** As tags do Ollama
mudam de nome e de empacotamento; o que identifica os pesos testados é o
digest de cada camada do manifesto. O `qwen3.8:latest` usado em todas as
runs (id da tag local `22130167c4c2`,
`/usr/share/ollama/.ollama/models/manifests/registry.ollama.ai/library/qwen3.8/latest`):

| Camada | Digest (sha256) | Tamanho |
|---|---|---|
| model (GGUF, 27.3B, Q4_K_M) | `f5f1dd8920d417aac2718b0bda3403da274301efdd6760b4f0f4b864ff2ad57d` | 16 810 714 464 B |
| config | `492b2922d38e553cabc2d319345644ed482874fbf5e5c9e4495cbf8e17b0cf5f` | — |
| projector (visão) | `ac3714bfdddeca31351f2752bf1a63f266f4df87c0b68c895e44945ca704448e` | 931 146 016 B |
| params | `906ee87bde6cff7bf3c3b1550f55cbbec261e027187fbb9f511f908ffc418334` | 114 B |
| license | `4c6a8e842ef0d8504549facfb03f1273a8d0022991519bc1888522cc1a5517d1` | 11 345 B |

Verificado contra o registo a 2026-09-26: as tags `qwen3.8:27b` (hoje com
id `e118e4d12a70` na página do Ollama) e `qwen3.8:27b-mtp-q4_K_M` (id
`22130167c4c2`) têm **exatamente estas cinco camadas**. Os ids das tags
diferem só no empacotamento do manifesto; os pesos, os parâmetros e a
configuração são os mesmos. Para reproduzir, qualquer uma das duas tags
serve; confirma-se com o digest da camada `model`. As tags derivadas
(`qwen3.8-t02`, `qwen3.8-pp15`) usam a mesma camada `model` e só mudam os
parâmetros (`harness/ollama/*.Modelfile`).

### 2.1 Modelos locais adicionais

`bench.sh` mapeia cada `side` local a uma tag do Ollama (ver `invoke_agent`
em `bench.sh`); `qwen3.8` (side `qwen`) continua a ser o modelo local
principal — os dois abaixo são comparações adicionais, não substituições.
Especificações confirmadas com `ollama show <tag>`:

| `side` | Tag Ollama | Arquitetura | Parâmetros | Quant | Context | Nota |
|---|---|---|---|---|---|---|
| `qwen3-coder` | `qwen3-coder:30b` | qwen3moe | 30.5B | Q4_K_M | 262144 | Mesma política de quant que `qwen3.8`; especializado em código, relevante para 3 das 4 tarefas. |
| `qwen3.8-flash-next` | `qwen3.8-flash-next:latest` | qwen4exp | 176.9B | **IQ2_S** | 262144 | **Foge à política Q4_K_M do §6 de propósito** — ~94 GB em disco contra ~123 GiB de RAM utilizável (ver Máquina, §2). Corre-se à parte, `K` baixo primeiro (ver README §Fase 2). Resultado é evidência offline; não citar como comparável a par com `qwen3.8`/`qwen3-coder` sem dizer isto em voz alta. |

### 2.2 Amostragem do lado local (nota de 2026-09-22)

**Quem define a amostragem.** Nenhum harness envia `temperature`, `top_k`
ou `top_p` ao Ollama. Verificado a 2026-09-22 capturando os pedidos com um
servidor falso: o claude-code envia só `max_tokens: 32000` e
`thinking: {type: adaptive}`, e o pi só `reasoning_effort`. Por isso, em
qualquer `AGENT`, a amostragem é a do Modelfile da tag Ollama:

| Tag | temperature | top_k | top_p | outros |
|---|---|---|---|---|
| `qwen3.8:latest` | 1 | 20 | 0.95 | — |
| `qwen3-coder:30b` | 0.7 | 20 | 0.8 | repeat_penalty 1.05 |
| `qwen3.8-flash-next:latest` | **0.2** | 40 | 0.95 | — |

**Assimetria já presente nos dados.** O `qwen3.8-flash-next:latest` corre a
temperatura 0.2 desde antes das suas runs; o `qwen3.8` corre a 1. Isto não
estava registado. Todas as runs do flash-next até esta data (incluindo o
pass do `v3-viriato`) confundem "modelo maior" com "temperatura mais baixa".
Não se refazem — declaram-se (ver §7).

**Braços adicionais, não substituições.** A configuração fixa do §2
(`qwen3.8` com o Modelfile de origem) **não muda**, e nenhuma run anterior é
invalidada. Os ajustes de amostragem correm como tags derivadas, cada uma um
`side` próprio no `bench.sh`, com Modelfile versionado em `harness/ollama/`:

| `side` / tag | Base | Muda face à base | Hipótese |
|---|---|---|---|
| `qwen3.8-t02` | `qwen3.8:latest` | temperature 1 → 0.2 | Menos variância ajuda código. Risco: nos Qwen com raciocínio, temperatura baixa tende a produzir repetição e ciclos de pensamento sem fim — o modo de falha já observado. |
| `qwen3.8-pp15` | `qwen3.8:latest` | presence_penalty 0 → 1.5 | Cortar os ciclos de raciocínio sem mexer na temperatura. |
| `qwen3-coder-t02` | `qwen3-coder:30b` | temperature 0.7 → 0.2 | Modelo sem raciocínio: temperatura baixa sem o risco de ciclos. |

As tags derivadas partilham os pesos da base; só muda o Modelfile. O lado
Claude não é afetado por nada disto e não se refaz.

**Resultado destes braços (medido a 2026-09-23, K=3, `AGENT=pi`/`pi-sol`):** o
`qwen3.8-t02` passou o `v1-polygon` e o `v2-solar`, que o `qwen3.8` a
temperatura 1 nunca terminou dentro do tempo em nenhum dos três harnesses. O
`qwen3.8-pp15` passou o v1 mas fora de tempo. O `qwen3-coder-t02` falhou por
física errada, não por tempo. Números e ressalvas em `RESULTS.md` — este
ficheiro continua a ser o pré-registo e não se reescreve com resultados.

**Contexto da decisão.** No `v1-polygon` com `AGENT=pi` e `PI_THINKING=high`
(batch `pi-high-v1v2`), o `qwen3.8` passou mais de 30 min num único turno de
raciocínio (~78 mil caracteres) sem chamar nenhuma ferramenta. É consistente
com as pastas de run vazias do lado claude-code nos v1/v2: o modelo não chega
a escrever. `reasoning_effort` no Ollama 0.33.3 com o qwen3.8 é só
liga/desliga (medido: `none` desliga, os níveis dão o mesmo, sem parâmetro já
raciocina), por isso não é a alavanca para isto.

### 2.3 Memória: OOM de 2026-09-22 e descarga entre runs

O Ollama desta máquina corre com `OLLAMA_KEEP_ALIVE=24h`,
`OLLAMA_MAX_LOADED_MODELS=3` e `OLLAMA_NUM_PARALLEL=4` (unit systemd). Com o
contexto nativo de 262144 tokens e 4 slots paralelos, **cada tag local ocupa
~39 GiB residentes** (medido: `free` sobe de 4 para 43 GiB ao carregar o
`qwen3.8-t02`, que o `ollama ps` reporta como 18 GB) e não é descarregada
durante 24 h.

A 2026-09-22 17:50, ao carregar a 3.ª tag local do batch `sampling-v1`
(`qwen3-coder-t02`, com `qwen3.8-t02` e `qwen3.8-pp15` ainda residentes), a
RAM chegou a 110 GiB (`power-queue-20260922.csv`) e às 17:59:37 o kernel
disparou o OOM killer. O systemd derrubou `user@1000.service` inteiro: caiu
a sessão gráfica e as duas filas de runs. A run do `qwen3-coder-t02` no
`v1-polygon` morreu a meio e **não produziu linha no CSV** — não é um
timeout nem uma falha do modelo, é infraestrutura. Não se conta como falha.

Mitigação, sem alterar a unit do Ollama: o `bench.sh` faz `ollama stop` da
tag no fim de cada run local, por isso fica no máximo uma tag em memória.

**Correção (2026-09-25):** a explicação acima está incompleta. A 2026-09-23,
com a máquina acabada de reiniciar e nenhum outro modelo carregado, o
`qwen3-coder-t02` sozinho levou a RAM a 110.2 GiB durante o carregamento
(`power-queue3-20260923.csv`). O OOM de 2026-09-22 coincidiu com o
carregamento dessa tag. Ver `RESULTS.md`, secção de memória.
As runs anteriores a esta data correram sem essa descarga; nas que
partilharam memória com outra tag, a pressão de memória é uma variável não
controlada (relevante sobretudo para `qwen3.8-flash-next`, ~94 GB).

### 2.4 Braço opencode: temperatura enviada explicitamente (nota de 2026-09-26)

**Definição, não resultado.** Até esta data o ramo `AGENT=opencode` do
`bench.sh` nunca correu, e como estava não podia correr: não passava `-m` (o
opencode usaria o seu modelo por omissão), lia a config do utilizador (que
injeta as skills de `~/.claude` no prompt) e não produzia JSON.

Ao verificar o pedido com um servidor falso encontrou-se um problema que afeta
mais do que o opencode: **o `/v1/chat/completions` do Ollama 0.33.3 ignora a
temperatura do Modelfile quando o pedido não a traz** (prova em `RESULTS.md`
6.7). O pi, o pi-sol, o prime-agent e o opencode usam esse endpoint; o
claude-code usa o `/v1/messages`, que a respeita.

O braço opencode fica definido assim:

| | Valor |
|---|---|
| Config | gerada por run pelo `bench.sh`, nunca a do utilizador |
| Endpoint | `/v1/chat/completions`, `@ai-sdk/openai-compatible` |
| Amostragem | `temperature` e `top_p` lidos de `ollama show <tag> --parameters` e **enviados no pedido** |
| Ferramentas | `bash`, `edit`, `glob`, `grep`, `read`, `write` (`skill`, `webfetch`, `task`, `todowrite` desligadas) |
| Isolamento | `--pure`, `OPENCODE_DISABLE_CLAUDE_CODE=1`, `OPENCODE_DISABLE_EXTERNAL_SKILLS=1`, `OPENCODE_DISABLE_PROJECT_CONFIG=1` |
| Permissões | `--auto` (aprova tudo, como o pi). **Assimetria** face ao `acceptEdits` do claude-code, declarada. |
| `top_k` | não enviado; o `/v1` não o expõe. Não verificado se o do Modelfile se mantém. Igual nos dois braços. |

Braços: `qwen` (`temperature 1`) contra `qwen3.8-t02` (`temperature 0.2`),
ambos `top_p 0.95`, v1-polygon e v2-solar, K=3, batch `oc-temp-k3`. Os
harnesses pi/pi-sol/prime-agent **não** são alterados: as runs já feitas
ficam como estão e são reinterpretadas em `RESULTS.md` 6.7.

## 3. Tarefas

Cada tarefa tem: `PROMPT.md` (enviado verbatim aos dois lados), `fixture/`
(estado inicial limpo) e `fixture/tests/` (critério objetivo, escrito ANTES).

| ID | Tipo | Critério | Porquê está aqui |
|---|---|---|---|
| `v1-polygon` | física própria, colisão com paredes móveis | contenção, não-sobreposição, período de rotação | Parâmetros alterados face ao prompt viral (nonágono/13 bolas/7 s) para quebrar memorização. |
| `v2-solar` | correção física por baixo do visual | Kepler + janelas de lançamento e regresso | Separa "bonito" de "correto". É o slide central. |
| `v3-viriato` | seguir um SRS com constraints duras | checker em 4 seeds | Não contaminado. Verificável por código, não por gosto. |
| `a1-bugfix` | debugging agêntico | 7 testes pytest | Curta — é esta que corre ao vivo. Bug de duas camadas: clamp + drift. |

**Removidos do plano original:** `c1-flatten-json` (tarefa canónica, quase de
certeza no training data dos dois lados), o hexágono/1 bola no prompt original
(viral desde início de 2025, memorizado), e uma tarefa `site` narrativa
(build livre para o voto cego de estética, sem checker) que nunca chegou a
ser escrita — a camada de "Artefacto" descrita numa versão anterior deste
documento não existe nesta corrida. O V1 mantém a física e muda os
parâmetros.

**Não usar o pelicano SVG.** O autor do teste diz que a correlação com
qualidade real do modelo está praticamente quebrada, e está saturado. Serve
como abertura de 30 segundos, não como medição.

## 4. Métricas registadas

Por run, automático:

- `pass` — exit code dos testes (binário; **não há rubrica 1–5**)
- `num_turns`, `duration_ms`, `total_cost_usd` — do `--output-format json`
- tok/s, TTFT — `llama-bench` no lado local
- W, RAM, temperatura — `monitor.py` a correr em paralelo

Agregação: **pass@1 sobre k=3**, não "passou/não passou" de uma run.

## 5. Camadas da apresentação

1. **Evidência** (§3–4) — corre dias antes, off-stage. É o que sustenta as
   afirmações.
2. **Palco** — só `a1-bugfix`, ao vivo, tmux com dois panes. Vídeo de
   backup gravado.

Uma terceira camada, "Artefacto" (voto cego de estética sobre uma tarefa
`site` narrativa e não pontuada), estava numa versão anterior deste
documento mas essa tarefa nunca foi escrita — ver §3. Não existe nesta
corrida; se quiseres reintroduzi-la, é preciso escrever `tasks/site/` (sem
`score.sh`, o próprio ponto é não ser verificada por código) antes de
voltar a citá-la aqui.

## 6. Decisões contra-intuitivas (justificadas)

- **Q4_K_M e não Q8_0.** O Strix Halo é bandwidth-bound. Q8 corta o throughput
  quase a metade sobre um baseline já modesto, e este modelo é muito verboso.
  Numa demo ao vivo isso é a diferença entre 8 e 20 minutos de espera.
- **Exceção deliberada: `qwen3.8-flash-next` corre a IQ2_S, não Q4_K_M.** É a
  única run fora da política acima — 176.9B parâmetros só cabem
  confortavelmente na RAM disponível a essa quant. Por isso corre-se e
  reporta-se à parte (ver §2.1 e §7), nunca como comparação direta ao mesmo
  nível de `qwen3.8`/`qwen3-coder`.
- **`reasoning_effort: medium` fixo.** Consequência: **não podes citar os
  números de índice públicos**, que são medidos em `xhigh`. Escolheste
  velocidade; assume-o no slide.
- **Sem rubrica subjetiva.** Qualquer pontuação 1–5 dada por ti depois de veres
  o output é post-hoc e indefensável em Q&A.

## 7. Assimetrias a declarar em slide

- A harness do Claude Code está afinada para modelos Claude (system prompt,
  tool schemas). Correr o Qwen pelo endpoint Anthropic-compatible é a
  comparação mais justa disponível — não é neutra, e favorece o lado Claude.
- Sem controlo de seed/temperatura do lado Claude. k=3 é a única defesa.
- HTML/CSS é o domínio mais saturado de training data que existe. Um modelo
  pequeno parece desproporcionalmente bom a fazer sites — vale a pena dizer
  isto em voz alta quando `v1-polygon`/`v2-solar` correrem bem, já que ambas
  entregam um `index.html` autónomo.
- Quota de subscrição: o lado Claude corre dias antes. Bater no limite na
  manhã da talk acaba com a talk.
- Amostragem diferente entre os locais: `qwen3.8` a temperatura 1,
  `qwen3-coder` a 0.7, `qwen3.8-flash-next` a 0.2 (ver §2.2). Qualquer
  diferença entre o flash-next e o `qwen3.8` mistura tamanho, quant e
  temperatura — não se atribui só ao tamanho.
- `qwen3.8-flash-next` não é comparável a par com os outros dois locais: quant
  muito mais agressiva (IQ2_S vs Q4_K_M), perto do limite de RAM da máquina, e
  tempo por run desconhecido até correr. Trata os números dele como uma nota
  à parte ("o que acontece se fores maior mas mais comprimido"), não como
  mais um ponto na mesma reta que `qwen3.8`/`qwen3-coder`.

## 8. Publicação

Repo público com este protocolo, prompts verbatim, logs JSON crus e CSV. Sem
isto, ninguém tem como te contestar — e um benchmark que ninguém pode contestar
não é um benchmark.
