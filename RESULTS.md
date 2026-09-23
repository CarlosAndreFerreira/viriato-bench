# Resultados

Estado a **2026-09-23**. Números gerados por `python3 score.py` a partir do
`results.csv`; os logs crus de cada run estão em `logs/`. O `PROTOCOL.md` é o
pré-registo e não muda com o que está aqui.

**Lê a coluna limpa.** Um run cortado pelo `TIMEOUT_S` ainda é pontuado: se os
ficheiros estavam certos no instante em que o processo foi morto, o verificador
dá PASS com o agente ainda a iterar. `score.py` separa:

- `pass_at_1_limpo` — passes com `timeout_hit=0`. **É este que se cita.**
- `pass_at_1` (largo) — inclui os passes fora de tempo, para se ver a diferença.

---

## 1. O resultado principal: a temperatura, não o harness

O `qwen3.8` corre a temperatura 1 (default do Modelfile, ver `PROTOCOL.md` §2.2).
A tag derivada `qwen3.8-t02` só muda isso para 0.2.

| Harness | Tarefa | Modelo | pass@1 limpo | Mediana |
|---|---|---|---|---|
| claude-code | v1-polygon | `qwen3.8` | 0/1 | 3000 s (timeout) |
| pi | v1-polygon | `qwen3.8` | 0/1 | 3000 s (timeout) |
| pi-sol | v1-polygon | `qwen3.8` | 0/1 | 3000 s (timeout) |
| **pi** | **v1-polygon** | **`qwen3.8-t02`** | **2/3** | **1280 s** |
| **pi-sol** | **v1-polygon** | **`qwen3.8-t02`** | **3/3** | **1079 s** |
| prime-agent | v1-polygon | `qwen3.8-t02` | 0/1 (pass fora de tempo) | 3001 s |
| claude-code | v2-solar | `qwen3.8` | 0/1 | 3000 s (timeout) |
| pi-sol | v2-solar | `qwen3.8` | 0/1 | 3001 s (timeout) |
| **pi** | **v2-solar** | **`qwen3.8-t02`** | **2/3** | **2087 s** |
| **pi-sol** | **v2-solar** | **`qwen3.8-t02`** | **2/3** | **2744 s** |
| claude-code | v1-polygon | `claude-opus-5` | 3/3 | 429 s, 6.15 $ |
| claude-code | v2-solar | `claude-opus-5` | 3/3 | 458 s, 6.89 $ |

**O modo de falha a temperatura 1 é raciocínio sem fim.** No `v1-polygon` com o
pi, o `qwen3.8` gastou os 3000 s num único turno, 117 mil caracteres de
pensamento, **zero chamadas a ferramentas e zero ficheiros escritos**. A 0.2 o
mesmo modelo faz 18 turnos e 22 mil caracteres de raciocínio, com o maior turno
em 6 mil: escreve, testa, corrige.

Três harnesses diferentes falharam da mesma maneira a temperatura 1. A mudança
de um parâmetro de amostragem pôs dois deles a passar. **Neste bench, a
amostragem pesou mais do que o scaffold.**

## 2. Harness: onde pesa e onde não pesa

| Harness | a1-bugfix (`qwen3.8`) | Turnos |
|---|---|---|
| claude-code | pass, 571 s (mediana de 3 batches: 450–827 s) | 12 |
| pi | pass, 166 s | 8 |
| prime-agent | pass, 166 s | 6 |
| pi-sol | pass, 144 s | 5 |

No `a1-bugfix` os harnesses leves foram 3 a 5 vezes mais rápidos que o
claude-code com o mesmo modelo. Nas tarefas visuais a temperatura 1, nenhum
salvou o modelo.

**O scaffold muda quanto o modelo raciocina.** Mesmo modelo, mesma
temperatura (`qwen3.8-t02`), mesmo `v1-polygon`, K=1 por célula:

| Harness | Ferramentas | Turnos | Raciocínio total | Maior turno | Resultado |
|---|---|---|---|---|---|
| pi | read/write/edit/bash | 18 | 29 mil | 10 mil | pass limpo, 1280 s |
| pi-sol | idem + obs_recall/update_plan | 8 | 11 mil | 9 mil | pass limpo, 1079 s |
| prime-agent | só `ipython` | 12 | **92 mil** | **54 mil** | pass fora de tempo, 3001 s |

O prime-agent raciocinou 3 a 8 vezes mais por run que os outros dois com o
mesmo modelo e a mesma temperatura, e voltou aos turnos gigantes (54 mil
caracteres) que a temperatura 0.2 tinha eliminado no pi. Escreveu um
`index.html` válido às 23:33 e continuou a mexer nele até ser morto às 23:57.
Uma ferramenta única (`ipython`, kernel persistente) parece empurrar o modelo
para planear dentro do turno em vez de iterar contra o disco. **É K=1: é uma
pista para investigar, não um resultado.**

**O SoL-Pi não mostra efeito atribuível.** Com `qwen3.8-t02` e K=3: 3/3 contra
2/3 no v1 (uma run de diferença), 2/3 contra 2/3 no v2. No `a1-bugfix` fez 5
turnos contra 8 do pi, mas **o modelo nunca usou o `then_run`**, que é o
mecanismo principal (Action Fusion) — logo a diferença de turnos não vem da
extensão. Os ganhos publicados (45–49% menos tokens) foram medidos com Opus 5 e
GPT-5.6 Sol, não com modelos locais.

## 3. O modelo especializado em código foi o único a entregar lixo

`qwen3-coder-t02` no `v1-polygon`: escreveu o `index.html` em **95 segundos**, 2
turnos, sem hesitar. O verificador: *13 amostras com bola fora do polígono, a
pior a 4607 px*. Não é lento nem indeciso — está errado.

No `v2-solar`, a run que o `pi-sol`/`qwen3.8-t02` falhou foi rejeitada por
*"no dia 972 (regresso à Terra) a nave está a 1.75 UA da posição real esperada,
tolerância 0.35 UA"*. A animação funcionava. Este é o material do slide
"bonito ≠ correto".

## 4. O que estes números NÃO suportam

- **Não suportam comparar harnesses entre si.** Com K=3, taxas de 2/3 e 3/3 têm
  intervalos de confiança que se sobrepõem quase por inteiro. Para afirmar que
  um harness é melhor que outro fazem falta K≥5 nas células que já existem.
- **Não suportam "o local iguala o frontier".** O Claude fez 3/3 limpos no v1 e
  no v2, em ~430–460 s. O local, no melhor caso, 3/3 no v1 a 1079 s de mediana,
  e 2/3 no v2.
- **Não suportam nada sobre o `claude-code` a 0.2.** Essa célula não foi corrida
  (ver §5). Hoje a afirmação defensável é "a 0.2 o modelo resolve o v1 **no
  pi**", não "resolve".
- **Não suportam o v3-viriato local.** O único pass local nessa tarefa
  (`qwen3.8-flash-next`) foi fora de tempo: limpo é 0/1.

Assimetrias já declaradas no `PROTOCOL.md`: amostragem diferente entre modelos
locais (§2.2), OOM que invalidou uma run do `qwen3-coder-t02` (§2.3), e a
harness do Claude Code estar afinada para modelos Claude (§7).

## 5. O que falta, por ordem de valor

| # | Experiência | Custo | O que responde |
|---|---|---|---|
| 1 | `claude-code` + `qwen3.8-t02`, v1 e v2, K=3 | ~4 h | A temperatura resolve em geral, ou só no pi? |
| 2 | K=5 nas células t02 de `pi` e `pi-sol` | ~6 h | O SoL-Pi tem efeito real ou é ruído? |
| 3 | `prime-agent` + `qwen3.8-t02`, v1, **K=3** | ~2.5 h | A triagem K=1 deu pass fora de tempo com 92 mil caracteres de raciocínio (§2). Confirma-se? |
| 4 | `opencode` | uma tarde + parser | Pouco, e com um confundidor por resolver (ver README §5) |

A triagem #3 a K=1 já correu (batch `prime-t02-v1`) e é o que motiva a nova
versão da linha.

Infraestrutura: pico de 50 GiB de RAM nas 12 runs do K=3
(`power-t02-k3-20260923.csv`), contra os 110 GiB que causaram o OOM antes de o
`bench.sh` passar a descarregar o modelo no fim de cada run.
