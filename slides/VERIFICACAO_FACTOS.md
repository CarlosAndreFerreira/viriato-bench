# Verificação de factos — `presentation_en.html` / `OUTLINE_EN.md`

Data: 2026-09-26. Cada linha diz o que o deck afirma, o veredicto e a prova.
As provas internas apontam para `RESULTS.md`, `results.csv` e `logs/`; as
externas para a página do artigo (arXiv) ou o cartão do modelo.

Legenda: ✅ correto · ⚠️ impreciso ou sem prova suficiente · ❌ errado

## 1. Artigos citados

| Afirmação no deck | Veredicto | Prova |
|---|---|---|
| SoL-Pi, arXiv:2609.20519, 4 mecanismos, "45–49% menos tokens" | ✅ (precisar) | Abstract: *"reducing recorded token traffic by 44.7-49.0% and API cost by about one third"*; avaliado no **EdgeBench (51 tarefas)** com **GPT-5.6 Sol e Opus 5**. Autores: Haozhe Liu, …, Enze Xie, Song Han (repo NVlabs). O deck diz "long coding horizons" — o artigo diz EdgeBench. |
| Agentless, arXiv:2407.01489, **"Gu et al., 2024"** | ❌ autores errados | Autores: **Chunqiu Steven Xia, Yinlin Deng, Soren Dunn, Lingming Zhang**. Afirmação do abstract: o Agentless *"is able to achieve both the highest performance (32.00%, 96 correct fixes) and low cost ($0.70)"* no SWE-bench Lite, entre agentes open-source. |
| "SWE-bench & SWE-rebench (Jimenez et al., ICLR 2024)" | ❌ dois artigos misturados | SWE-bench: Jimenez, Yang, Wettig, Yao, Pei, Press, Narasimhan — ICLR 2024, arXiv:2310.06770 — **não introduz o SWE-rebench**. SWE-rebench: **Badertdinov et al., 2025, arXiv:2505.20411** (pipeline automático e descontaminado, >21 000 tarefas). |
| "Terminal-Bench 2.0 & Harbor (2025/2026)", sem referência | ⚠️ falta a citação | Artigo: *Terminal-Bench: Benchmarking Agents on Hard, Realistic Tasks in Command Line Interfaces*, **arXiv:2601.11868** (Merrill et al.), 89 tarefas; "frontier models and agents score less than 65%". O Harbor é o harness onde as tarefas correm (`harbor run -d terminal-bench@2.0`). |
| "Overthinking in Reasoning Models: studies on…" (sem artigo) | ⚠️ sem citação | Existe o artigo exato para o nosso achado: **Cuadron et al., 2025, arXiv:2502.08235**, *The Danger of Overthinking: Examining the Reasoning-Action Dilemma in Agentic Tasks* (ver §3). |

## 2. Números e afirmações sobre os nossos dados

| Afirmação no deck | Veredicto | Prova |
|---|---|---|
| Título: "Can **$1,800** Hardware…" | ⚠️ sem prova | O preço da máquina não está registado em nenhum ficheiro do repo. Usar só se tiveres a fatura. |
| Slide 3: "16c/32t, Radeon 8060S 40 CUs, LPDDR5X" | ✅ parcial | `lscpu` → 32 CPUs; PROTOCOL §2 → "AMD RYZEN AI MAX+ 395 w/ Radeon 8060S", 123 GiB. Os 40 CUs e o LPDDR5X não estão medidos no repo. |
| "Q4_K_M evita a penalização de 50% do Q8_0" | ⚠️ não medido | PROTOCOL §6 justifica-o ("corta o throughput quase a metade"), mas nunca foi medido neste bench. Apresentar como razão, não como resultado. |
| Claude 12/12 a `high`, 11/12 a `medium`, −25% custo | ✅ | RESULTS §6.5: 25.06 $ vs 18.72 $; a falha é um `NameError: MAX_CORRIDOR` no v3. |
| `qwen3.8` temp. 1: a1 3/3, visuais 0/9, p = 0.00002 | ✅ | RESULTS §1. |
| "113 000–122 000 caracteres de raciocínio sem ferramentas" | ✅ | `pi-qwen-v2-solar-1` (113 162) e `pi-sol-qwen-v2-solar-1` (122 194), 0 turnos, 0 ferramentas. |
| "Com 0.2 os ciclos **desaparecem completamente**" | ❌ exagero | 3 das 12 runs a 0.2 (pi+pi-sol) falharam; o prime-agent a 0.2 voltou a ter turnos de 54–93 mil caracteres (RESULTS §3.1). |
| 0/5 → 9/12, p = 0.009 | ✅ | RESULTS §2. |
| `presence_penalty 1.5`: "late passes after **27 turns**" | ❌ | A run `qwen3.8-pp15` teve **18 turnos** (`results.csv`, batch `sampling-v1`). Os 27 turnos são de uma run do `qwen3.8-t02`. |
| Coder: "**13 balls flew 4607 px** outside" | ❌ leitura errada | O verificador diz *"13 amostras com bola fora do poligono (pior: -4607.7 px)"*: 13 **amostras** (de 60) com alguma bola fora, pior caso 4607.7 px. E o modelo era o `qwen3-coder-t02` (temp. 0.2), K=1. |
| "Fast code without reasoning is confident hallucination" | ⚠️ generalização de K=1 | Uma única run. |
| Slide 6: "**Kepler's 3rd Law violated: Mars period off by 23%**" | ❌ inventado | O `.score` da run tem **um único problema**: *"no dia 972 (regresso a Terra) a nave esta a 1.75 UA da posicao real esperada (tolerancia 0.35 UA)"*. Não há violação de Kepler nem "23%". |
| "LLMs memorized the visual appearance of a solar system" | ⚠️ especulação | Não testado. |
| Slide 7: 9/12 vs 0/6, p = 0.0045 | ✅ | RESULTS §3.3. |
| "monopolizing the single **GPU/NPU** slot" | ❌ | O Ollama corre na GPU; o NPU não é usado. |
| "89 KB prompt… creates severe **TTFT** latency (~30 min on turn 1)" | ❌ | Medido nos logs do Ollama: o prompt é processado depressa (1420 tokens em 4.7 s, ~300 tok/s); os ~30 min são **geração** (raciocínio), não tempo até ao primeiro token. |
| "The Fix: … 3/3 valid files and the first clean local pass" | ⚠️ desatualizado | Com `--effort medium` + sem pedidos secundários: 1/3 limpos (p = 0.5, não significativo). **O que resolveu foi o pedido "magro"** (batch `cc-lean-t02-k3`, 2026-09-26): **3/3 limpos**, p = 0.018 contra 1/9. |
| Slide 8: "frontier models have strong priors… 27B ignores optional fields without fine-tuning" | ⚠️ hipótese apresentada como explicação | Medido: 0/44 `then_run`, 0 chamadas às ferramentas, 0 artefactos. **Dois dos quatro mecanismos são passivos** (ObservationPack, redutor): não disparar indica que as sessões eram curtas (≤ 264 KB), não um problema de "priors". Nada foi testado com fine-tuning. |
| Prime-agent 54k–93k vs 9k–22k, p = 0.012 | ✅ | RESULTS §3.1. A explicação ("over-plans in the REPL") é hipótese. |
| Slide 11: "Measuring Strix Halo **at the Socket**" | ❌ | O sensor é o `amdgpu` **PPT** (potência do SoC), não a tomada. O próprio slide diz-o numa nota — o título contradiz a nota. |
| "86–95 °C" | ⚠️ | Medido: 88–94 °C (máximos por run). |
| a1: 2.8–3.9 Wh (pi) vs 16–26.7 Wh (claude-code): "**5x–7x strictly due to scaffold overhead**" | ❌ causa mal atribuída | As duas séries diferem em **harness e temperatura** (pi + `qwen3.8-t02` vs claude-code + `qwen3.8` a temp. 1). Não se pode atribuir só ao scaffold. |
| Slide 12: "100 runs/dia → **$6,200/mês**; payback **< 15 dias**" | ❌ sem base | Nenhum dado do bench mede isto. Os $2.08/run são custo *equivalente* de API reportado pelo CLI da subscrição; e o local só resolveu tarefas visuais a 67% e 2–6× mais devagar. Pode ser apresentado como **cenário com pressupostos explícitos**, nunca como resultado. Os 0.50 $/dia de eletricidade usam só a potência do SoC. |
| Slide 13: demo "Qwen on **pi**" com `export ANTHROPIC_BASE_URL` | ❌ inconsistente | Essa variável é do claude-code, não do pi. E o pi com `qwen3.8-t02` resolve o a1 em 91–123 s (mediana 121 s), praticamente o mesmo que o Claude (138 s): o guião "se o local demorar 3 minutos" está desatualizado. |
| Conclusão: "temp 0.2 is **mathematically essential**" | ❌ exagero | Provado: melhora significativamente nos harnesses leves, nas nossas tarefas (p = 0.009). Não é "matemático" nem geral — e contraria a recomendação oficial (§3). |
| Conclusão: "lightweight scaffolds are **mandatory**" | ❌ exagero | Provado: o pedido de origem do claude-code prejudica o modelo local; com um pedido magro o claude-code também passa (3/3). O problema é o tamanho do pedido, não "scaffolds pesados" em geral. |
| Conclusão: "energy efficiency can **match the frontier cloud**" | ❌ | Não há medida de energia do lado Claude (corre na cloud). Só a **velocidade** no a1 empatou (121 vs 138 s, K=3). |
| Conclusão: "code-specialized models… **Refuted**" | ❌ | Uma run (K=1) não refuta uma afirmação geral. |

## 3. Artigos mais recentes que se aplicam (verificados)

| Artigo | O que diz (citação/abstract) | Como se liga aos nossos dados |
|---|---|---|
| **Cuadron et al., 2025** — *The Danger of Overthinking: Examining the Reasoning-Action Dilemma in Agentic Tasks*, arXiv:2502.08235 | Modelos de raciocínio *"favor extended internal reasoning chains over environmental interaction"*; padrões: **Analysis Paralysis**, Rogue Actions, Premature Disengagement; 4018 trajetórias no SWE-bench Verified; *"higher overthinking scores correlate with decreased performance"*; escolher soluções com menos overthinking: **~30% melhor, −43% custo**. | É o nome científico do nosso modo de falha: 113–122 mil caracteres de raciocínio com **0 chamadas a ferramentas** é *Analysis Paralysis* em estado puro. |
| **Cartão oficial do Qwen3.8-27B** (Hugging Face) | Modo de raciocínio: **temperature=1.0**, top_p=0.95, top_k=20; *"lower reasoning effort does not always reduce overall task completion time"* em tarefas agênticas multi-turno; recomenda até 262 144 tokens de raciocínio. | A nossa temperatura 0.2 **desvia-se da recomendação oficial** — tem de ser dito no slide. O limite de `max_tokens: 32000` do Claude Code está muito abaixo do que o fabricante recomenda; o primeiro turno do claude-code a `high` gerou ~32 000 tokens (bateu no limite). |
| **Documentação Qwen3** (quickstart) | *"DO NOT use greedy decoding, as it can lead to performance degradation and endless repetitions."* | Responde à pergunta "e temperatura 0?": o fabricante desaconselha; não foi testado aqui. |
| **Yang et al., 2024** — *SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering*, arXiv:2405.15793 | O desenho da interface agente-computador (ACI) muda o desempenho com o mesmo modelo; 12.5% pass@1 no SWE-bench na altura. | Enquadramento direto do nosso "harness conta": mesmo modelo, 0/6 vs 9/12, e o pedido magro do claude-code a passar 3/3. |
| **Sengupta & Wang, 2026** — *HARBOR: Automated Harness Optimization*, arXiv:2604.20938 | *"harness design is a first-class machine-learning problem"*; a complexidade dos agentes vem sobretudo *"not by their underlying model but by the harness that wraps it"*. | Consistente com a sequência de experiências do claude-code (default → sem pedidos secundários → `medium` → pedido magro). Só li o abstract; não citar números dele. |
| **Merrill et al., 2026** — *Terminal-Bench*, arXiv:2601.11868 | 89 tarefas difíceis em terminal; modelos de fronteira < 65%. | Próximo passo natural (via Harbor) para sair das 4 tarefas. |
| **Badertdinov et al., 2025** — *SWE-rebench*, arXiv:2505.20411 | Tarefas mineradas continuamente, marcadas contra a data de lançamento dos modelos para detetar contaminação. | Justifica tarefas novas/alteradas (v1 com parâmetros mudados, v3 original). |

## 4. O que corrigi no deck novo (`presentation_viriato_en.html`)

Todos os ❌ e ⚠️ acima: autores e artigos corrigidos, "Kepler 23%" removido,
"socket" → "SoC (PPT)", TTFT → geração, TCO passa a cenário interativo com
pressupostos visíveis, conclusões com o p-value e o âmbito exatos, e o
resultado novo do claude-code magro (3/3).
