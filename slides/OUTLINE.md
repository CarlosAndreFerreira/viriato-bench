# Estrutura da apresentação

Regra geral: cada afirmação no ecrã tem de ter uma linha no `results.csv` por
trás. Se não tem, sai.

## 1. Abertura (2 min) — a piada que também é um aviso
Pelicano em POV-Ray nos dois lados. Resultados absurdos, ovo a flutuar incluído.
Fecho: "isto é divertido e não mede nada. É por isso que o resto da talk tem
verificadores."

## 2. O setup (3 min)
Mini-PC, 128 GB UMA, Qwen3.8-27B Q4_K_M local contra Claude via subscrição.
**Mesma harness, mesmos prompts, mesmas permissões, mesmo timeout.** Só mudam
os pesos. Mostra as duas linhas de comando lado a lado — é o slide que prova
que a comparação é honesta.

## 3. Assimetrias, antes que perguntem (2 min)
- A harness está afinada para modelos Claude. Favorece o lado Claude.
- Sem controlo de seed nem temperatura do lado Claude. Daí o k=3.
- `reasoning_effort` fixo em medium por causa do tempo → **não** cito índices
  públicos, que são medidos em xhigh.
- Q4_K_M e não Q8: o Strix Halo é bandwidth-bound.

Antecipares-te aqui vale mais do que qualquer gráfico depois.

## 4. Resultados (6 min)
Tabela do `score.py`. Uma coluna que interessa: **pass@1**, não "passou".
Destaca as tarefas instáveis — é onde uma run isolada teria mentido.

## 5. Bonito ≠ correto (5 min) — o núcleo
As duas versões do V2 projetadas. Ambas bonitas. Votação cega da sala.
Só depois: o verificador. Janela de regresso, 3.ª lei de Kepler.
Fecho: "a sala votou no visual. O verificador votou na física. Se só tivessem
o visual, tinham escolhido o errado."

## 6. Custo e latência (4 min)
tok/s, watts, medianas de wall-clock, custo equivalente em API.
É aqui que o local ganha, e a medição é incontestável.

## 7. Ao vivo (5 min)
`a1-bugfix` em tmux, dois panes. Vídeo de backup pronto.
Se o local demorar, fala por cima — a espera é o dado.

## 8. O que vem a seguir (3 min)
Harness ≠ modelo. Harbor, matriz agente × modelo, Terminal-Bench em subconjunto
declarado, SWE-rebench para contaminação. Isto é trabalho de artigo.

## 9. Q&A
Repo público no ecrã: protocolo, prompts, logs crus, CSV.
"Está tudo aqui, contestem."
