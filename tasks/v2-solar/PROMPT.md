Cria um ficheiro `index.html` autónomo (HTML + CSS + JavaScript num único
ficheiro, sem dependências externas, sem CDN) que anime o sistema solar interior
e uma missão tripulada Terra–Marte de ida e volta.

Requisitos visuais:

- Sol ao centro, e os planetas Mercúrio, Vénus, Terra e Marte em órbitas
  circulares, com os raios orbitais em escala relativa correta (Terra = 1 AU).
- Cada órbita desenhada como traço, cada planeta com etiqueta de nome e cor
  plausível, tamanhos relativos distinguíveis (não à escala real, mas ordenados
  corretamente).
- Os períodos orbitais têm de estar corretos entre si: um ano de Marte demora
  cerca de 1.88 anos da Terra.
- Contador de FPS instantâneo e FPS médio visíveis no ecrã.
- Uma nave que parte da Terra na janela de lançamento correta, faz a
  transferência de Hohmann até Marte, espera na superfície de Marte até à
  janela de regresso, e volta à Terra. O trajeto da nave é desenhado.
- Escala de tempo controlável e indicação do dia da missão.

Requisitos de cálculo — é aqui que a tarefa se decide:

- A transferência de Hohmann Terra→Marte demora cerca de 259 dias.
- O alinhamento de lançamento exige que Marte esteja cerca de 44 graus à frente
  da Terra no momento da partida.
- Depois de chegar, a tripulação tem de esperar cerca de 455 dias em Marte pela
  janela de regresso.
- A missão completa ronda os 970 dias.
- A nave tem de chegar efetivamente à posição do planeta, não a um ponto
  arbitrário da órbita.

Contrato de verificação — obrigatório, o teste automático depende disto:

Expõe em `window.__bench` um objeto com este formato exato:

```js
window.__bench = {
  bodies: [
    { name: "Mercury", auRadius: <num>, periodDays: <num>, angleDeg0: <num> },
    { name: "Venus",   auRadius: <num>, periodDays: <num>, angleDeg0: <num> },
    { name: "Earth",   auRadius: 1.0,   periodDays: <num>, angleDeg0: <num> },
    { name: "Mars",    auRadius: <num>, periodDays: <num>, angleDeg0: <num> }
  ],
  mission: {
    departurePhaseAngleDeg: <ângulo Marte-Sol-Terra à partida, em graus>,
    outboundDays:  <duração da transferência de ida>,
    stayDays:      <espera em Marte>,
    returnDays:    <duração da transferência de volta>,
    totalDays:     <total da missão>
  },
  setMissionDay(day) {
    // Salta a simulação de forma determinística para o dia de missão `day`
    // (usado pelo teste para verificar a posição da nave em dias concretos
    // sem depender de tempo real). getState() logo a seguir tem de refletir
    // esse dia e a posição real da nave nesse instante. A animação normal
    // continua a avançar por si própria via requestAnimationFrame quando
    // setMissionDay não é chamado.
  },
  getState() {
    return { missionDay: <num>, shipAU: { x: <num>, y: <num> } };
  }
};
```

`angleDeg0` é o ângulo do corpo, em graus, medido a partir do eixo +x, sentido
anti-horário, no instante `missionDay = 0`. A posição de qualquer corpo (e da
Terra e Marte em particular) num dia `d` é então:

```
angulo(d) = angleDeg0 + 360 * d / periodDays        (mod 360, graus)
x(d) = auRadius * cos(angulo(d) em radianos)
y(d) = auRadius * sin(angulo(d) em radianos)
```

O verificador usa isto para confirmar que a nave chega **fisicamente** perto
da posição real de Marte no dia de chegada (não a um ponto qualquer da
órbita), fica junto a Marte durante a espera, e regressa perto da posição
real da Terra no fim da missão — e não apenas que os números declarados em
`mission` são coerentes entre si.

Entrega apenas o ficheiro `index.html`. Não escrevas explicações fora do
ficheiro.
