# Protocolo — Qwen3.8-27B local vs Claude, mesma harness

**Pré-registado em:** _(preenche a data ANTES da primeira run)_
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
| Máquina | ACEMAGIC M1A PRO+, Ryzen AI MAX+ 395, 128 GB UMA | |
| SO / kernel | Ubuntu 26.04, kernel ... | |
| Claude Code version | `claude --version` | |
| Modelo Claude | `--model ...` (fixa explicitamente) | |
| Ollama version | `ollama --version` | |
| Modelo local | `qwen3.8` | |
| Quant | Q4_K_M (NÃO Q8 — ver §6) | |
| Context | >= 32768 | |
| `reasoning_effort` | `medium` (fixo, registado em todas as runs) | |
| Temperatura (lado Qwen) | fixa | |
| Temperatura / seed (lado Claude) | **não controlável via CLI** | n/a |
| k (runs por tarefa por lado) | 3 | |
| Timeout por run | 900 s | |
| Permissões | idênticas nos dois lados | |

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
certeza no training data dos dois lados) e o hexágono/1 bola no prompt original
(viral desde início de 2025, memorizado). O V1 mantém a física e muda os
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
2. **Artefacto** (`site`) — os dois builds projetados lado a lado, sem
   identificação, audiência vota. **O voto mede preferência, não capacidade.**
   Diz isto em voz alta antes de votarem.
3. **Palco** — só `a1-task-manager`, ao vivo, tmux com dois panes. Vídeo de
   backup gravado.

## 6. Decisões contra-intuitivas (justificadas)

- **Q4_K_M e não Q8_0.** O Strix Halo é bandwidth-bound. Q8 corta o throughput
  quase a metade sobre um baseline já modesto, e este modelo é muito verboso.
  Numa demo ao vivo isso é a diferença entre 8 e 20 minutos de espera.
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
  pequeno parece desproporcionalmente bom a fazer sites. A tarefa `site` é
  narrativa, e por isso não entra no número final.
- Quota de subscrição: o lado Claude corre dias antes. Bater no limite na
  manhã da talk acaba com a talk.

## 8. Publicação

Repo público com este protocolo, prompts verbatim, logs JSON crus e CSV. Sem
isto, ninguém tem como te contestar — e um benchmark que ninguém pode contestar
não é um benchmark.
