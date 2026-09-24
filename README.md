# Lusitano Bench

Comparação de modelos locais (Strix Halo) contra Claude, **na mesma harness**,
com correção verificada por código e estética votada em separado. Modelo
local principal: Qwen3.8-27B. Adicionalmente testados: `qwen3-coder:30b`
(especializado em código) e `qwen3.8-flash-next` (176.9B, quant IQ2_S — ver
aviso em §4 e §6/§7 do `PROTOCOL.md`, não é comparável a par com os outros
por correr fora da política de quant Q4_K_M).

A tese não é "o 27B é tão bom como o Claude". É: **que fração do trabalho
migra para local, a que latência, a que custo, e onde é que parte.**

Resultados medidos até agora, com as ressalvas do que não suportam:
**[`RESULTS.md`](RESULTS.md)**.

---

## 0. Pré-requisitos

```bash
sudo apt install -y jq coreutils
python3 -m pip install --break-system-packages pytest
ollama pull qwen3.8                    # confirma o nome exato com: ollama list
ollama pull qwen3-coder:30b            # opcional, so se fores testar SIDES=qwen3-coder
ollama pull qwen3.8-flash-next:latest  # opcional, 94GB — ver aviso em §4
claude --version                       # Claude Code, autenticado com a subscrição
```

**Playwright** (só para V1 e V2):

```bash
python3 -m pip install --break-system-packages playwright
python3 -m playwright install chromium
```

Aviso honesto: o Python de sistema do mini-PC é o 3.14 e pode não haver wheels
do Playwright para essa versão. Se a instalação falhar, não percas a tarde:

```bash
uv venv --python 3.12 .venv && source .venv/bin/activate
pip install playwright pytest && playwright install chromium
```

Sem Playwright, V1 e V2 devolvem **SKIP** (exit 2). Um skip nunca conta como
pass — fica registado como skip no CSV e o dashboard mostra-o. V3 e A1 não
precisam de browser e correm sempre.

---

## 1. Estrutura

```
lusitano-bench/
├── PROTOCOL.md          # pré-registo. Preenche ANTES da primeira run.
├── RESULTS.md           # o que já foi medido, e o que os números nao suportam
├── bench.sh             # runner: fixture limpo, timeout, JSON, scoring
├── score.py             # results.csv -> pass@1
├── monitor.py           # watts / RAM / temperatura durante as runs
├── dashboard/index.html # lê o CSV no browser, sem chaves de API
├── slides/OUTLINE.md    # estrutura da apresentação
├── verify/
│   ├── browser.py           # harness Playwright partilhado
│   ├── reference_v1.html    # }  implementações de referência: provam que
│   ├── reference_v2.html    # }  os checkers são passáveis. NÃO copiar
│   └── reference_maze.py    # }  para dentro de tasks/*/fixture/.
└── tasks/
    ├── v1-polygon/   nonágono em rotação, 13 bolas   (browser)
    ├── v2-solar/     sistema solar + missão a Marte  (browser)
    ├── v3-viriato/   gerador de labirinto do SRS     (stdlib)
    └── a1-bugfix/    bug plantado, corre ao vivo     (pytest)
```

Cada tarefa tem `PROMPT.md` (enviado verbatim aos dois lados), `fixture/`
(estado inicial, copiado limpo por run) e `score.sh` (binário: pass/fail).

---

## 2. As quatro tarefas

| ID | O que mede | Como é verificado |
|---|---|---|
| **v1-polygon** | física própria, colisão com paredes em movimento | bolas sempre dentro do nonágono, sem sobreposição, período de rotação ±10% |
| **v2-solar** | correção física por baixo de um visual bonito | raios e períodos ±5%, 3.ª lei de Kepler, janela de partida 44°±6°, ida 259 d, espera 455 d, total 970 d |
| **v3-viriato** | seguir um SRS com constraints duras | 36×28, simetria horizontal, zero dead ends, componente conexo único, castrum 6×4, 1 túnel, densidade 35–60%, determinismo — em 4 seeds |
| **a1-bugfix** | debugging agêntico | 7 testes pytest têm de passar |

O **v2** é o melhor slide que tens: as duas versões podem ser lindas e só uma
tem a janela de regresso certa. É a demonstração de que julgar modelos a olho
não funciona.

O **a1** tem um bug de duas camadas de propósito: corrigir só o *clamp* de fim
de mês ainda deixa um teste a falhar por *drift*. Corrigir a sério exige ancorar
as ocorrências à data de início. Uma correção superficial não passa.

---

## 3. Plano de execução

### Fase 0 — smoke test

```bash
chmod +x bench.sh tasks/*/score.sh
K=1 TASKS=a1-bugfix SIDES=qwen ./bench.sh
python3 score.py
```

Pode demorar bem mais que 15 minutos num modelo verboso — conta com o
`TIMEOUT_S` inteiro (3000 s por omissão, §2) como pior caso. Confirma:
- o `runs/claude-code-qwen-a1-bugfix-1/` foi criado e tem `schedule.py`;
- o `logs/*.score` mostra o pytest (isto é o que importa; um `TIMEOUT`
  ainda pode ter deixado o ficheiro corrigido no disco antes de o processo
  ser morto — vê o `.score`, não só o exit code, antes de assumir que falhou);
- o `logs/*.json` tem JSON válido **só quando o processo termina dentro do
  timeout**. Um `!! TIMEOUT` no terminal produz um `.json` vazio de propósito
  — não é bug, é o processo a ser morto a meio antes de escrever o resumo.

### Fase 1 — lado Claude, **dias antes** (não na manhã da talk)

```bash
CLAUDE_MODEL=claude-opus-5 SIDES=claude K=3 ./bench.sh
```

A subscrição tem limites de utilização. 4 tarefas × 3 runs esgotam quota a
sério. Se bateres no limite na manhã da apresentação, ficas sem metade da talk.
Corre isto com antecedência e guarda os logs.

### Fase 2 — lado local, quantas vezes quiseres

```bash
python3 monitor.py --out power.csv &
SIDES="qwen qwen3-coder" K=3 ./bench.sh
kill %1
```

Custo marginal zero. Corre de noite. Se um modelo ficar preso a pensar, o
`TIMEOUT_S` (3000 s / 50 min por omissão, ver PROTOCOL.md §2) corta.

**`qwen3.8-flash-next` corre à parte, nunca junto dos outros:**

```bash
python3 monitor.py --out power.csv &
SIDES=qwen3.8-flash-next K=1 TIMEOUT_S=1800 ./bench.sh
kill %1
```

176.9B parâmetros a IQ2_S, ~94 GB em disco contra ~123 GiB de RAM utilizável
— perto do limite, e a quant foge de propósito à política Q4_K_M do §6 do
`PROTOCOL.md`. Começa com `K=1` e um `TIMEOUT_S` maior antes de confiar num
`K=3` de longa duração; se o sistema começar a fazer swap, mata a run — um
número obtido a fazer swap não serve para nada no slide.

Cada corrida do `bench.sh` grava um `batch_id` novo em `results.csv` (podes
nomeá-lo: `BATCH_ID=fase2-run2 SIDES=qwen ./bench.sh`). O `score.py` agrega,
por omissão, só o batch mais recente por tarefa/lado — uma segunda passagem
nunca se mistura silenciosamente com a primeira. Usa `--all-batches` se
quiseres mesmo juntar tudo.

As pastas de run e os logs ficam por batch: `runs/<batch_id>/` e
`logs/<batch_id>/`. Correr a mesma tarefa noutro batch já não apaga as provas
do anterior. Para completar um batch existente sem refazer as runs que já tem,
usa `K_START`: `BATCH_ID=<batch> K_START=2 K=3 ./bench.sh` corre só as runs 2 e 3.
Runs anteriores a 2026-09-24 ficam na raiz de `runs/` e `logs/`.

### Fase 3 — agregar

```bash
python3 score.py
python3 score.py --json dashboard/summary.json
xdg-open dashboard/index.html     # carrega o results.csv à mão
```

### Fase 4 — palco

```bash
tmux new-session \; split-window -h
# pane esquerdo:
cd runs/claude-code-claude-a1-bugfix-1 && claude
# pane direito:
cd runs/claude-code-qwen-a1-bugfix-1 \
  && export ANTHROPIC_BASE_URL=http://localhost:11434 ANTHROPIC_AUTH_TOKEN=ollama ANTHROPIC_API_KEY= \
  && claude --model qwen3.8
```

Usa **shells separados**. Se as variáveis do Ollama ficarem exportadas no shell
errado, o lado Claude vai em silêncio para o modelo local e só descobres em
palco.

Cuidado com `VAR=valor cmd1 && cmd2`: isso define `VAR` só para `cmd1`, nunca
para `cmd2` — é por isso que o `export` acima está separado do `cd` e vem
antes do `claude`. Antes de ires para o palco, confirma no pane direito:

```bash
echo "$ANTHROPIC_BASE_URL"   # tem de mostrar http://localhost:11434
```

Se vier vazio, o pane direito vai falar com a API real da Anthropic em vez do
Ollama local, e só descobres isso a meio da demo.

Grava vídeo de backup das duas runs antes do dia.

---

## 4. Orçamento de tempo (conta com isto)

No Strix Halo, com um modelo verboso a 15–25 tok/s, conta **20–50 minutos por
tarefa**. Quatro tarefas × 3 runs × 2 lados ≈ 8 a 20 horas de máquina, e o lado
Claude é uma fração pequena disso. Planeia noites, não tardes.

Cada `SIDES` local adicional multiplica isto quase linearmente — `qwen` +
`qwen3-coder` já são ~16 a 40 horas de máquina, não 8 a 20. `qwen3-coder:30b`
é maior que o `qwen3.8` pinado mas com a mesma política de quant (Q4_K_M),
por isso conta com tok/s pior, não melhor. `qwen3.8-flash-next` (176.9B,
IQ2_S) não entra nesta conta — corre-se à parte, com `K` baixo primeiro (ver
§Fase 2), porque tanto o tempo por run como o risco de swap são
desconhecidos até correres.

Se alargares ao Terminal-Bench (89 tarefas), uma passagem completa são 45 a 90
horas. Nesse caso usa um subconjunto fixo de 20–30 tarefas com seed publicada e
**diz que é um subconjunto**. Um subconjunto declarado é ciência; 89 prometidas
e nunca corridas são uma talk que não acontece.

---

## 5. Fase 2 — outros harnesses

O `bench.sh` corre as quatro tarefas deste repo com `AGENT=pi` e
`AGENT=prime-agent` (o Prime Agent é um fork do pi, mesmo CLI e mesmo stream
JSON):

```bash
AGENT=pi          SIDES=qwen TASKS=v1-polygon K=1 ./bench.sh
AGENT=prime-agent SIDES=qwen TASKS=v1-polygon K=1 ./bench.sh
```

- Config própria em `harness/pi/` e `harness/prime-agent/` — nunca o `~/.pi`
  ou `~/.prime` do utilizador. Modelos Ollama sem `samplingParams`, para ficar
  a temperatura por omissão do Ollama, como no lado claude-code.
- Sem extensões, skills, AGENTS.md nem templates: o harness nu.
- `PI_THINKING` (omissão `medium`) vai como `reasoning_effort` para o Ollama.
  Com o qwen3.8 os níveis dão todos o mesmo raciocínio, e sem o parâmetro o
  modelo já raciocina. **`PI_THINKING=off` não desliga o raciocínio**: o pi
  deixa de enviar o parâmetro e o Ollama raciocina por omissão (ver
  `RESULTS.md` §6.1).
- O Prime Agent corre **sem** `--autonomous-gate`: um gate com o verificador
  mostrava ao agente o critério que os outros harnesses não veem.
- Nenhum dos dois tem modo de permissões. O `ipython` do Prime Agent corre com
  as permissões do utilizador — ver a nota de sandbox abaixo.
- O lado `claude` com estes harnesses precisa de `ANTHROPIC_API_KEY` e é pago
  por token, fora da quota da subscrição.
- Os eventos crus ficam em `logs/*.events.jsonl`; `harness/pi_summary.py`
  resume-os nos mesmos campos do `--output-format json` do Claude Code.

### `AGENT=pi-sol` — pi + SoL-Pi (NVIDIA)

O [SoL-Pi](https://github.com/NVlabs/SoL-Pi) é uma extensão do pi que corta
tokens (o paper reporta 45–49% menos tráfego com a mesma taxa de sucesso, medido
só com Opus 5 e GPT-5.6 Sol). `pi-sol` é **o mesmo pi global** mais a extensão,
por isso a comparação com `AGENT=pi` isola o efeito da extensão:

```bash
harness/get-sol-pi.sh      # clona o SoL-Pi no commit fixado e corre a suite deles
AGENT=pi-sol SIDES=qwen TASKS=v1-polygon K=1 ./bench.sh
```

- Os quatro mecanismos ligados, como no paper: Action Fusion (`edit`/`write`
  ganham `then_run`), ObservationPack (`obs_recall`), Evidence-Preserving
  Reducer e Online Context Compact (`update_plan`).
- O redutor usa **por omissão um modelo remoto** (`openai-codex/gpt-5.6-luna`).
  O `bench.sh` gera um `sol-pi.json` por run que o fixa ao mesmo modelo do
  side. Sem isso, uma run "local" chamaria o GPT.
- O redutor e a compactação fazem chamadas extra ao mesmo modelo local. Contam
  no tempo de parede — é o custo real do mecanismo neste hardware.
- O SoL-Pi exige sessão persistente: a sessão e os artefactos ficam em
  `logs/*.events.jsonl.sessions/`, fora do run dir.
- O SoL-Pi é testado contra o pi 0.85.1 e declara compatibilidade com o
  0.84.2 (o pinado aqui). Carregamento e ferramentas confirmados no 0.84.2.

O ramo `AGENT=opencode` ainda não está pronto para medir (sem provider Ollama
configurado, sem `--format json`, sem modelo no lado claude).

Para o Terminal-Bench e harnesses que não estão aqui, **não escrevas runner
próprio** — usa o Harbor, que é a framework oficial do Terminal-Bench e corre
agentes arbitrários sobre os mesmos datasets:

```bash
uv tool install harbor
harbor datasets list
harbor run -d "terminal-bench@2.0" -m "<modelo>" -a "<agente>"
```

Duas notas:

- O **Prime Agent** não é sandbox: os processos correm com as permissões do
  utilizador local. Não o corras no mini-PC onde tens o teu trabalho — container
  ou VM descartável.
- O resultado mais interessante desta fase não é "local vs frontier". É quanto
  do desempenho é o modelo e quanto é o scaffold. Já há casos publicados de um
  harness terceiro a bater o de origem no modelo do próprio fabricante. Isso é
  material de artigo, não de apresentação de almoço.

---

## 6. Os checkers foram validados nos dois sentidos

```bash
make check-reference
```

Corre os três verificadores contra implementações de referência em `verify/`.
Todos passam. E todos rejeitam versões partidas — o V2, por exemplo, apanha um
período de Marte errado através da 3.ª lei de Kepler mesmo quando a animação
continua bonita.

Isto não é cerimónia. Um checker que ninguém consegue passar não mede
capacidade, mede a tua especificação mal escrita; e um que aceita tudo não mede
nada. As referências ficam fora de `tasks/` de propósito: o `bench.sh` só copia
`tasks/<task>/fixture/` para o run dir, portanto o agente nunca as vê.

---

## 7. Regras que não se negoceiam

1. **Dois eixos, nunca somados.** Correção é automática e binária. Estética é
   voto cego e mede preferência, não capacidade. Não faças média das duas.
2. **k ≥ 3.** O `score.py` marca as tarefas em que as runs discordam. É
   exatamente aí que uma run isolada te teria mentido.
   **Um pass fora de tempo não é um pass.** Uma run cortada pelo `TIMEOUT_S`
   ainda é pontuada: se os ficheiros estavam certos no instante em que o
   processo foi morto, o verificador dá PASS com o agente ainda a iterar. O
   `score.py` e o dashboard separam `pass@1 limpo` (o número citável) de
   `pass@1 largo`. Cita o limpo.
3. **Fixture limpo por run.** Já está no `bench.sh`. Não contornes.
4. **Sem rubricas 1–5.** Uma pontuação que dás depois de veres o output é
   post-hoc e não sobrevive ao Q&A.
5. **Publica tudo** — protocolo, prompts, logs crus, CSV. Um benchmark que
   ninguém pode contestar não é um benchmark.
