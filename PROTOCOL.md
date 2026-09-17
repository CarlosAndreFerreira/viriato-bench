# Protocolo — modelos locais (Qwen3.8, Qwen3-Coder, Qwen3.8-Flash-Next) vs Claude, mesma harness

**Pré-registado em:** 2026-09-17
**Regra:** nada neste ficheiro muda depois da primeira run. Se mudares, a corrida
recomeça do zero. É isto que separa um benchmark de uma anedota.

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
| Timeout por run | 900 s | confirmado: `TIMEOUT_S="${TIMEOUT_S:-900}"` em `bench.sh` |
| Permissões | idênticas nos dois lados | confirmado: `PERM_MODE="${PERM_MODE:-acceptEdits}"` aplicado igualmente a `side=claude` e a todos os `side` locais em `bench.sh` |

### 2.1 Modelos locais adicionais

`bench.sh` mapeia cada `side` local a uma tag do Ollama (ver `invoke_agent`
em `bench.sh`); `qwen3.8` (side `qwen`) continua a ser o modelo local
principal — os dois abaixo são comparações adicionais, não substituições.
Especificações confirmadas com `ollama show <tag>`:

| `side` | Tag Ollama | Arquitetura | Parâmetros | Quant | Context | Nota |
|---|---|---|---|---|---|---|
| `qwen3-coder` | `qwen3-coder:30b` | qwen3moe | 30.5B | Q4_K_M | 262144 | Mesma política de quant que `qwen3.8`; especializado em código, relevante para 3 das 4 tarefas. |
| `qwen3.8-flash-next` | `qwen3.8-flash-next:latest` | qwen4exp | 176.9B | **IQ2_S** | 262144 | **Foge à política Q4_K_M do §6 de propósito** — ~94 GB em disco contra ~123 GiB de RAM utilizável (ver Máquina, §2). Corre-se à parte, `K` baixo primeiro (ver README §Fase 2). Resultado é evidência offline; não citar como comparável a par com `qwen3.8`/`qwen3-coder` sem dizer isto em voz alta. |

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
- `qwen3.8-flash-next` não é comparável a par com os outros dois locais: quant
  muito mais agressiva (IQ2_S vs Q4_K_M), perto do limite de RAM da máquina, e
  tempo por run desconhecido até correr. Trata os números dele como uma nota
  à parte ("o que acontece se fores maior mas mais comprimido"), não como
  mais um ponto na mesma reta que `qwen3.8`/`qwen3-coder`.

## 8. Publicação

Repo público com este protocolo, prompts verbatim, logs JSON crus e CSV. Sem
isto, ninguém tem como te contestar — e um benchmark que ninguém pode contestar
não é um benchmark.
