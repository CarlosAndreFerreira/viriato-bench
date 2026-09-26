import json, os

mazes_data = open('arena_mazes.json').read()

sched_orig = open('tasks/a1-bugfix/fixture/schedule.py').read()
sched_flash = open('runs/claude-code-qwen3.8-flash-next-a1-bugfix-1/schedule.py').read()
sched_qwen = open('runs/claude-code-qwen-a1-bugfix-1/schedule.py').read()
sched_sonnet = open('runs/claude-code-claude-sonnet-4-6-a1-bugfix-1/schedule.py').read()
sched_opus = open('runs/claude-code-claude-opus-4-8-a1-bugfix-1/schedule.py').read()

check_maze_code = open('runs/claude-code-qwen3.8-flash-next-v3-viriato-1/check_maze.py').read()
maze_flash_code = open('runs/claude-code-qwen3.8-flash-next-v3-viriato-1/maze.py').read()
maze_claude_code = open('runs/claude-code-claude-v3-viriato-1/maze.py').read()

template = """<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lusitano Arena · Multi-Model Interactive Explorer</title>
<style>
  :root {
    --bg: #090b10;
    --surface: #111420;
    --surface-card: #161b2a;
    --border: #232a3e;
    --border-bright: #384260;
    --text: #f1f5f9;
    --muted: #94a3b8;
    --primary: #6366f1;
    --primary-light: #818cf8;
    --cyan: #06b6d4;
    --pass: #10b981;
    --fail: #ef4444;
    --warn: #f59e0b;
    --purple: #a855f7;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    line-height: 1.5;
    padding: 0;
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
  }

  header {
    background: rgba(17, 20, 32, 0.95);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    padding: 10px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
    z-index: 50;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .brand-title {
    font-size: 18px;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(135deg, #fff 30%, #818cf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .badge-tag {
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 6px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border: 1px solid var(--border-bright);
    background: rgba(99, 102, 241, 0.12);
    color: var(--primary-light);
  }

  .nav-tabs {
    display: flex;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 3px;
    gap: 2px;
  }

  .nav-tab {
    padding: 6px 14px;
    font-size: 13px;
    font-weight: 600;
    color: var(--muted);
    background: transparent;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .nav-tab:hover {
    color: #fff;
    background: rgba(255, 255, 255, 0.05);
  }

  .nav-tab.active {
    color: #fff;
    background: var(--primary);
    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4);
  }

  .top-links {
    display: flex;
    gap: 8px;
  }

  .pill-link {
    font-size: 12px;
    font-weight: 600;
    padding: 5px 10px;
    border-radius: 6px;
    text-decoration: none;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border);
    color: var(--muted);
    transition: all 0.15s;
    display: flex;
    align-items: center;
    gap: 5px;
  }

  .pill-link:hover {
    color: #fff;
    border-color: var(--primary-light);
  }

  main {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
  }

  .tab-pane {
    display: none;
    max-width: 1400px;
    margin: 0 auto;
  }

  .tab-pane.active {
    display: block;
  }

  .grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }

  .grid-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }

  .grid-4 {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
  }

  .card {
    background: var(--surface-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    position: relative;
    overflow: hidden;
  }

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }

  .card-title {
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .status-badge {
    font-size: 11px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 99px;
  }

  .status-pass {
    background: rgba(16, 185, 129, 0.15);
    color: var(--pass);
    border: 1px solid rgba(16, 185, 129, 0.3);
  }

  .status-fail {
    background: rgba(239, 68, 68, 0.15);
    color: var(--fail);
    border: 1px solid rgba(239, 68, 68, 0.3);
  }

  .sim-container {
    border: 1px solid var(--border-bright);
    border-radius: 8px;
    background: #000;
    overflow: hidden;
    height: 520px;
    position: relative;
  }

  .sim-container iframe {
    width: 100%;
    height: 100%;
    border: none;
    display: block;
  }

  .sim-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: var(--surface);
    border-top: 1px solid var(--border);
    font-size: 12px;
  }

  pre.code-view {
    background: #0d1117;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 12px;
    line-height: 1.45;
    color: #e6edf3;
    overflow-x: auto;
    height: 480px;
    white-space: pre;
  }

  .maze-canvas-wrap {
    background: #0a0d14;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  canvas.maze-canvas {
    display: block;
    background: #0f1422;
    border-radius: 4px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }

  .btn-group {
    display: flex;
    gap: 4px;
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 3px;
    border-radius: 6px;
  }

  .btn-sub {
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 600;
    color: var(--muted);
    background: transparent;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s;
  }

  .btn-sub.active {
    background: var(--border-bright);
    color: #fff;
  }

  .callout {
    background: rgba(99, 102, 241, 0.08);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 13.5px;
    line-height: 1.6;
    margin-top: 14px;
  }

  .metric-box {
    background: rgba(255,255,255,0.02);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px;
    text-align: center;
  }

  .metric-val {
    font-size: 22px;
    font-weight: 800;
    color: #fff;
    line-height: 1.1;
  }

  .metric-sub {
    font-size: 11px;
    color: var(--muted);
    margin-top: 2px;
  }

  table.arena-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13.5px;
    margin-top: 10px;
  }

  table.arena-table th, table.arena-table td {
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    text-align: left;
  }

  table.arena-table th {
    font-size: 11.5px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--muted);
    letter-spacing: 0.05em;
  }

  tr.highlight-row {
    background: rgba(99, 102, 241, 0.07);
  }
</style>
</head>
<body>

<header>
  <div class="brand">
    <span class="brand-title">Lusitano Arena</span>
    <span class="badge-tag">AMD Strix Halo · 128 GB UMA</span>
  </div>

  <div class="nav-tabs">
    <button class="nav-tab active" data-tab="tab-overview">⚔️ Visão 360°</button>
    <button class="nav-tab" data-tab="tab-a1">🐛 a1-bugfix</button>
    <button class="nav-tab" data-tab="tab-v1">🌀 v1-polygon</button>
    <button class="nav-tab" data-tab="tab-v2">🪐 v2-solar</button>
    <button class="nav-tab" data-tab="tab-v3">🏰 v3-viriato</button>
  </div>

  <div class="top-links">
    <a class="pill-link" href="../slides/presentation.html" target="_blank">📽 Slides de Palco</a>
    <a class="pill-link" href="../dashboard/index.html" target="_blank">📊 Dashboard CSV</a>
  </div>
</header>

<main>

  <!-- TAB 1: VISÃO 360° -->
  <section class="tab-pane active" id="tab-overview">
    <div style="margin-bottom: 18px;">
      <h1 style="font-size: 24px; font-weight: 800; letter-spacing: -0.02em;">O Grande Duelo: Frontier Cloud vs Modelos Locais</h1>
      <p style="color: var(--muted); font-size: 14px;">Medição empírica, append-only e sem truques na mesma harness do Claude Code em AMD Ryzen AI MAX+ 395.</p>
    </div>

    <div class="grid-4" style="margin-bottom: 20px;">
      <div class="metric-box">
        <div class="metric-val" style="color: var(--pass);">4 / 4</div>
        <div class="metric-sub">Tarefas Verificadas com Sucesso</div>
      </div>
      <div class="metric-box">
        <div class="metric-val" style="color: var(--primary-light);">128 GB</div>
        <div class="metric-sub">Memória Unificada (0 B Swap)</div>
      </div>
      <div class="metric-box">
        <div class="metric-val" style="color: var(--warn);">$0.00</div>
        <div class="metric-sub">Custo Marginal de Tokens Locais</div>
      </div>
      <div class="metric-box">
        <div class="metric-val" style="color: var(--cyan);">~55 W</div>
        <div class="metric-sub">Potência Medida em Carga Local</div>
      </div>
    </div>

    <div class="card" style="margin-bottom: 20px;">
      <div class="card-header">
        <div class="card-title">Matriz Consolidada de Resultados (pass@1)</div>
        <span class="badge-tag">Atualizado a 20 de Setembro de 2026</span>
      </div>
      <table class="arena-table">
        <thead>
          <tr>
            <th>Tarefa</th>
            <th>Competência</th>
            <th>Claude Opus 5 (Cloud)</th>
            <th>Qwen3.8-Flash-Next (177B Local)</th>
            <th>Qwen3.8:latest (27B Q4 Local)</th>
            <th>Destaque Técnico</th>
          </tr>
        </thead>
        <tbody>
          <tr class="highlight-row">
            <td><strong>a1-bugfix</strong></td>
            <td>Debugging agêntico de 2 camadas</td>
            <td><span class="status-badge status-pass">PASS · 1.0 (134s · $0.92)</span></td>
            <td><span class="status-badge status-pass">PASS · 1.0 (618s · 7 turnos · $0)</span></td>
            <td><span class="status-badge status-pass">PASS · 1.0 (571s · 12 turnos · $0)</span></td>
            <td><strong>Flash-Next bateu Claude em economia de turnos (7 vs 10)!</strong></td>
          </tr>
          <tr>
            <td><strong>v1-polygon</strong></td>
            <td>Física de colisões com paredes móveis</td>
            <td><span class="status-badge status-pass">PASS · 1.0 (429s · $1.99)</span></td>
            <td><span class="status-badge status-fail">TIMEOUT (3,000s · 8t TTFT)</span></td>
            <td><span class="status-badge status-fail">TIMEOUT (3,000s · Loop)</span></td>
            <td>Cloud necessária para síntese gráfica rápida sem TTFT local.</td>
          </tr>
          <tr>
            <td><strong>v2-solar</strong></td>
            <td>Astrofísica orbital de Kepler vs Visual</td>
            <td><span class="status-badge status-pass">PASS · 1.0 (458s · $2.77)</span></td>
            <td><span class="status-badge status-fail">TIMEOUT (3,000s · Barreira HTTP 300s)</span></td>
            <td><span class="status-badge status-fail">TIMEOUT (3,000s · Loop)</span></td>
            <td>Descoberta da barreira dos 300 segundos da camada HTTP local.</td>
          </tr>
          <tr class="highlight-row">
            <td><strong>v3-viriato</strong></td>
            <td>Síntese algorítmica sob SRS rígido</td>
            <td><span class="status-badge status-pass">PASS · 1.0 (444s · $2.15)</span></td>
            <td><span class="status-badge status-pass">PASS · 1.0 (~3,000s · Auto-TDD · $0)</span></td>
            <td><span class="status-badge status-fail">TIMEOUT (3,001s · 32k th)</span></td>
            <td><strong>Flash-Next criou os seus próprios testes e corrigiu o bug da borda!</strong></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-title">O Paradoxo dos Tokens por Segundo</div>
        <p style="font-size: 13px; color: var(--muted); margin: 8px 0 12px;">Na geração pura de código no motor Ollama, a APU debita taxas impressionantes:</p>
        <ul style="font-size: 13px; color: #cbd5e1; padding-left: 18px; line-height: 1.8;">
          <li><strong>Qwen 27B:</strong> até <strong>24.1 tokens/segundo</strong> em geração pura.</li>
          <li><strong>Qwen Flash-Next 177B MoE:</strong> <strong>16.8 – 17.0 tokens/segundo</strong> a inferir 94 GB de pesos!</li>
          <li><strong>Por que a sessão demora mais?</strong> Porque reingerir 25.000 tokens de prompt acumulado no Ollama demora ~100s/turno (TTFT). O gargalo local é a reingestão de contexto, não a geração!</li>
        </ul>
      </div>

      <div class="card">
        <div class="card-title">Retorno do Investimento (ROI) em Hardware</div>
        <p style="font-size: 13px; color: var(--muted); margin: 8px 0 12px;">Comparação de custos reais para equipas de desenvolvimento:</p>
        <ul style="font-size: 13px; color: #cbd5e1; padding-left: 18px; line-height: 1.8;">
          <li><strong>100 tarefas agênticas/dia na Cloud (Opus):</strong> ~$215 por dia → <strong>~$4.500 / mês</strong>.</li>
          <li><strong>Workstation 128 GB UMA local:</strong> ~55W potência média → <strong>~3€ / mês em eletricidade</strong>.</li>
          <li><strong>Payback:</strong> O hardware de 1.800€ amortiza-se em <strong>menos de 3 semanas</strong> para tarefas de CI e debugging.</li>
        </ul>
      </div>
    </div>
  </section>

  <!-- TAB 2: A1-BUGFIX -->
  <section class="tab-pane" id="tab-a1">
    <div style="margin-bottom: 16px;">
      <h2 style="font-size: 20px; font-weight: 800;">a1-bugfix · Arena de Debugging Agêntico</h2>
      <p style="color: var(--muted); font-size: 13px;">O desafio de 2 camadas: eliminar o ValueError em meses curtos (Camada 1) e corrigir a deriva de cálculo cumulativo (Camada 2).</p>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <div class="card-title">Código da Solução do Agente</div>
          <div class="btn-group" id="a1-code-btns">
            <button class="btn-sub active" data-src="flash">Flash-Next (7t)</button>
            <button class="btn-sub" data-src="qwen">Qwen 27B (12t)</button>
            <button class="btn-sub" data-src="sonnet">Sonnet 4.6 (26s)</button>
            <button class="btn-sub" data-src="orig">Original (Buggy)</button>
          </div>
        </div>
        <pre class="code-view" id="a1-code-display"></pre>
      </div>

      <div class="card">
        <div class="card-title">Análise de Eficiência e Telemetria</div>
        <table class="arena-table" style="margin-top: 10px;">
          <thead>
            <tr>
              <th>Modelo</th>
              <th>Turnos</th>
              <th>Tempo Real</th>
              <th>Tokens Gastos</th>
              <th>Custo</th>
            </tr>
          </thead>
          <tbody>
            <tr class="highlight-row">
              <td><strong>Flash-Next (177B)</strong></td>
              <td><strong style="color:var(--pass);">7 turnos</strong></td>
              <td>618s (~10m)</td>
              <td><strong>1,582 tokens</strong></td>
              <td><strong>$0.00</strong></td>
            </tr>
            <tr>
              <td><strong>Claude Sonnet 4.6</strong></td>
              <td>8 turnos</td>
              <td><strong>26s</strong></td>
              <td>1,815 tokens</td>
              <td>$0.28</td>
            </tr>
            <tr>
              <td><strong>Claude Opus 4.8</strong></td>
              <td>10 turnos</td>
              <td>134s</td>
              <td>3,789 tokens</td>
              <td>$0.92</td>
            </tr>
            <tr>
              <td><strong>Qwen3.8 (27B)</strong></td>
              <td>12 turnos</td>
              <td>571s (~9.5m)</td>
              <td>3,635 tokens</td>
              <td><strong>$0.00</strong></td>
            </tr>
            <tr>
              <td><strong>Claude Haiku 4.5</strong></td>
              <td>13 turnos</td>
              <td>37s</td>
              <td>4,345 tokens</td>
              <td>$0.14</td>
            </tr>
          </tbody>
        </table>

        <div class="callout" style="margin-top: 20px;">
          <strong>Destaque para o Palco:</strong> O Flash-Next 177B precisou de <strong>quase 3× menos tokens</strong> que o Haiku (1.582 vs 4.345) e menos turnos que o próprio Claude Opus. Densidade de raciocínio supera velocidade bruta de geração!
        </div>
      </div>
    </div>
  </section>

  <!-- TAB 3: V1-POLYGON -->
  <section class="tab-pane" id="tab-v1">
    <div style="margin-bottom: 16px;">
      <h2 style="font-size: 20px; font-weight: 800;">v1-polygon · Física e Colisão com Paredes Móveis</h2>
      <p style="color: var(--muted); font-size: 13px;">13 bolas numeradas dentro de um nonágono a rodar 360° em 7s com impulso tangencial.</p>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <div class="card-title">Solução Claude Opus 5 (Passou com 1.0)</div>
          <span class="status-badge status-pass">PASS · Playwright</span>
        </div>
        <div class="sim-container">
          <iframe id="iframe-v1-claude" src="../runs/claude-code-claude-v1-polygon-1/index.html"></iframe>
        </div>
        <div class="sim-controls">
          <span>Nonágono: 9 lados · Período: 7s · 13 bolas</span>
          <button class="btn-sub" onclick="document.getElementById('iframe-v1-claude').src += ''">🔄 Reiniciar</button>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <div class="card-title">Implementação Canónica de Referência</div>
          <span class="status-badge status-pass">Referência Física</span>
        </div>
        <div class="sim-container">
          <iframe id="iframe-v1-ref" src="../verify/reference_v1.html"></iframe>
        </div>
        <div class="sim-controls">
          <span>Física Analítica Determinística</span>
          <button class="btn-sub" onclick="document.getElementById('iframe-v1-ref').src += ''">🔄 Reiniciar</button>
        </div>
      </div>
    </div>

    <div class="card" style="margin-top: 16px;">
      <div class="card-title">Diagnóstico Forense: Por Que Falharam os Modelos Locais no V1?</div>
      <div class="grid-2" style="margin-top: 10px;">
        <div style="font-size: 13.5px; line-height: 1.6; color: #cbd5e1;">
          <strong style="color: var(--fail);">Qwen 27B:</strong> Bloqueou num loop de reflexão profunda fechado. Tentou derivar as matrizes de rotação e conservação de momento angular mentalmente e atingiu os 50 minutos num único turno.
        </div>
        <div style="font-size: 13.5px; line-height: 1.6; color: #cbd5e1;">
          <strong style="color: var(--warn);">Flash-Next 177B:</strong> Executou 8 turnos de reconhecimento exaustivo (leu o Playwright, o harness e o código de referência). O modelo demorou ~100s por turno em TTFT e gerou 59.296 chars de raciocínio. Atingiu os 3.000s no turno 9 exatamente quando ia emitir a escrita do ficheiro!
        </div>
      </div>
    </div>
  </section>

  <!-- TAB 4: V2-SOLAR -->
  <section class="tab-pane" id="tab-v2">
    <div style="margin-bottom: 16px;">
      <h2 style="font-size: 20px; font-weight: 800;">v2-solar · Astrofísica Orbital vs Ilusão Visual</h2>
      <p style="color: var(--muted); font-size: 13px;">O experimento da votação cega: 3.ª Lei de Kepler (T² / a³ = const) e transferência de Hohmann Terra-Marte.</p>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <div class="card-title">Solução Claude Opus 5 (Física Correta)</div>
          <span class="status-badge status-pass">PASS · 1.0 (Kepler)</span>
        </div>
        <div class="sim-container">
          <iframe id="iframe-v2-claude" src="../runs/claude-code-claude-v2-solar-1/index.html"></iframe>
        </div>
        <div class="sim-controls">
          <span>Órbitas circulares com raio em escala AU e Hohmann de 970 dias</span>
          <button class="btn-sub" onclick="document.getElementById('iframe-v2-claude').src += ''">🔄 Reiniciar</button>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <div class="card-title">Implementação de Referência</div>
          <span class="status-badge status-pass">Referência</span>
        </div>
        <div class="sim-container">
          <iframe id="iframe-v2-ref" src="../verify/reference_v2.html"></iframe>
        </div>
        <div class="sim-controls">
          <span>Kepler + Ângulo de partida de 44° + Espera de 455 dias em Marte</span>
          <button class="btn-sub" onclick="document.getElementById('iframe-v2-ref').src += ''">🔄 Reiniciar</button>
        </div>
      </div>
    </div>

    <div class="card" style="margin-top: 16px;">
      <div class="card-title">Descoberta de Engenharia: A Barreira dos 300 Segundos na Camada HTTP Local</div>
      <p style="font-size: 13.5px; color: #cbd5e1; margin-top: 8px; line-height: 1.6;">
        Na execução do Flash-Next no V2, os logs do Ollama provam que o modelo gerou a <strong>17.02 tokens/s</strong> e produziu mais de <strong>5.053 tokens de raciocínio num único turno</strong>. No entanto, 5.000 tokens a 17 tok/s mais a ingestão de contexto demoram cerca de 5 minutos, colidindo com o limite de <strong>300 segundos da ligação HTTP</strong> do Claude Code CLI (erro HTTP 500). Isso forçou o cliente a reiniciar a tentativa 3 vezes em loop até esgotar o benchmark!
      </p>
    </div>
  </section>

  <!-- TAB 5: V3-VIRIATO -->
  <section class="tab-pane" id="tab-v3">
    <div style="margin-bottom: 16px;">
      <h2 style="font-size: 20px; font-weight: 800;">v3-viriato · Síntese Algorítmica de Labirintos sob SRS</h2>
      <p style="color: var(--muted); font-size: 13px;">Grelha 36×28, simetria horizontal estrita, Castrum central 6×4, 0 becos sem saída, verificado em 4 seeds.</p>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <div class="card-title">Visualizador Gráfico do Labirinto Gerado</div>
          <div style="display: flex; gap: 6px;">
            <div class="btn-group" id="v3-model-btns">
              <button class="btn-sub active" data-model="flash_next">Flash-Next 177B (PASS)</button>
              <button class="btn-sub" data-model="claude_opus">Claude Opus 5 (PASS)</button>
              <button class="btn-sub" data-model="reference">Referência</button>
            </div>
            <div class="btn-group" id="v3-seed-btns">
              <button class="btn-sub active" data-seed="1">Seed 1</button>
              <button class="btn-sub" data-seed="7">Seed 7</button>
              <button class="btn-sub" data-seed="42">Seed 42</button>
              <button class="btn-sub" data-seed="1234">Seed 1234</button>
            </div>
          </div>
        </div>

        <div class="maze-canvas-wrap">
          <canvas class="maze-canvas" id="mazeCanvas" width="448" height="576"></canvas>
        </div>

        <div style="display: flex; justify-content: space-between; font-size: 12px; color: var(--muted); margin-top: 8px;">
          <span>⬛ Castrum Central 6×4 (Dourado)</span>
          <span>🟦 Túnel Lateral Wrap-Around (Ciano)</span>
          <span>⬜ Paredes Simétricas (Branco/Cinza)</span>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <div class="card-title">A Proeza do Auto-TDD do Flash-Next</div>
          <div class="btn-group" id="v3-code-btns">
            <button class="btn-sub active" data-v3src="check">check_maze.py (Auto-TDD)</button>
            <button class="btn-sub" data-v3src="flash">maze.py (Flash-Next)</button>
            <button class="btn-sub" data-v3src="claude">maze.py (Claude Opus)</button>
          </div>
        </div>
        <pre class="code-view" id="v3-code-display"></pre>
      </div>
    </div>

    <div class="callout" style="margin-top: 16px;">
      <strong>O Veredito do V3:</strong> O Claude Opus 5 resolveu o problema em 10 turnos e 7.4 minutos com custo de $2.15 USD. O Flash-Next 177B MoE local alcançou <strong>exatamente o mesmo 100% de sucesso nas 4 seeds</strong> com custo zero de tokens, demonstrando capacidade de auto-validação e reparação de código.
    </div>
  </section>

</main>

<script>
  // Tabs Navigation
  const tabs = document.querySelectorAll('.nav-tab');
  const panes = document.querySelectorAll('.tab-pane');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      panes.forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(tab.dataset.tab).classList.add('active');
      if (tab.dataset.tab === 'tab-v3') {
        renderMaze();
      }
    });
  });

  // A1 Code Snippets Data
  const A1_CODES = {
    flash: %FLASH_SCHED%,
    qwen: %QWEN_SCHED%,
    sonnet: %SONNET_SCHED%,
    orig: %ORIG_SCHED%
  };

  const a1Display = document.getElementById('a1-code-display');
  const a1Btns = document.querySelectorAll('#a1-code-btns .btn-sub');

  function updateA1Code(key) {
    a1Display.textContent = A1_CODES[key] || '';
  }
  updateA1Code('flash');

  a1Btns.forEach(btn => {
    btn.addEventListener('click', () => {
      a1Btns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      updateA1Code(btn.dataset.src);
    });
  });

  // V3 Maze Data
  const MAZE_DATA = %MAZE_JSON%;

  let currentMazeModel = 'flash_next';
  let currentMazeSeed = '1';

  const v3ModelBtns = document.querySelectorAll('#v3-model-btns .btn-sub');
  const v3SeedBtns = document.querySelectorAll('#v3-seed-btns .btn-sub');
  const canvas = document.getElementById('mazeCanvas');
  const ctx = canvas.getContext('2d');

  function renderMaze() {
    const grid = MAZE_DATA[currentMazeModel]?.[currentMazeSeed];
    if (!grid) return;

    const rows = grid.length;
    const cols = grid[0].length;
    const cellW = canvas.width / cols;
    const cellH = canvas.height / rows;

    ctx.fillStyle = '#0f1422';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const val = grid[r][c];
        const isCastrum = (r >= 15 && r <= 18 && c >= 11 && c <= 16);
        const isTunnel = (c === 0 || c === 27) && val === 0;

        if (isCastrum) {
          ctx.fillStyle = '#f59e0b'; // Amber Gold for Castrum
          ctx.fillRect(c * cellW, r * cellH, cellW, cellH);
        } else if (isTunnel) {
          ctx.fillStyle = '#06b6d4'; // Cyan for tunnel
          ctx.fillRect(c * cellW, r * cellH, cellW, cellH);
        } else if (val === 1) {
          ctx.fillStyle = '#334155'; // Slate wall
          ctx.fillRect(c * cellW, r * cellH, cellW - 0.5, cellH - 0.5);
        } else {
          ctx.fillStyle = '#020617'; // Floor path
          ctx.fillRect(c * cellW, r * cellH, cellW, cellH);
        }
      }}

    // Symmetry axis line
    ctx.strokeStyle = 'rgba(99, 102, 241, 0.4)';
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(canvas.width / 2, 0);
    ctx.lineTo(canvas.width / 2, canvas.height);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  v3ModelBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      v3ModelBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentMazeModel = btn.dataset.model;
      renderMaze();
    });
  });

  v3SeedBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      v3SeedBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentMazeSeed = btn.dataset.seed;
      renderMaze();
    });
  });

  // V3 Code view
  const V3_CODES = {
    check: %CHECK_MAZE_JSON%,
    flash: %FLASH_MAZE_JSON%,
    claude: %CLAUDE_MAZE_JSON%
  };

  const v3Display = document.getElementById('v3-code-display');
  const v3Btns = document.querySelectorAll('#v3-code-btns .btn-sub');

  function updateV3Code(key) {
    v3Display.textContent = V3_CODES[key] || '';
  }
  updateV3Code('check');

  v3Btns.forEach(btn => {
    btn.addEventListener('click', () => {
      v3Btns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      updateV3Code(btn.dataset.v3src);
    });
  });

  // Initial maze render
  renderMaze();
</script>
</body>
</html>
"""

final_html = template.replace('%FLASH_SCHED%', json.dumps(sched_flash))
final_html = final_html.replace('%QWEN_SCHED%', json.dumps(sched_qwen))
final_html = final_html.replace('%SONNET_SCHED%', json.dumps(sched_sonnet))
final_html = final_html.replace('%ORIG_SCHED%', json.dumps(sched_orig))
final_html = final_html.replace('%MAZE_JSON%', mazes_data)
final_html = final_html.replace('%CHECK_MAZE_JSON%', json.dumps(check_maze_code))
final_html = final_html.replace('%FLASH_MAZE_JSON%', json.dumps(maze_flash_code))
final_html = final_html.replace('%CLAUDE_MAZE_JSON%', json.dumps(maze_claude_code))

with open('arena/index.html', 'w') as f:
    f.write(final_html)

print('arena/index.html generated successfully!')
