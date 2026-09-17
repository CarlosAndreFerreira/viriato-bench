Cria um ficheiro `index.html` autónomo (HTML + CSS + JavaScript num único
ficheiro, sem dependências externas, sem CDN) que simule bolas a saltar dentro
de um polígono em rotação.

Requisitos da simulação:

- O polígono é um **nonágono regular** (9 lados), centrado no canvas, com raio
  de 260 px, a rodar em torno do seu centro a **360 graus em 7 segundos**, no
  sentido horário.
- Há **13 bolas**, todas com raio 14 px, numeradas de 0 a 12. O número tem de
  estar desenhado por cima de cada bola e tem de rodar com a bola, para se ver
  o spin.
- Física implementada por ti: gravidade, fricção do ar, fricção de contacto,
  restituição (coeficiente 0.82) e colisão bola-bola e bola-parede. As paredes
  estão em movimento, portanto a resposta à colisão tem de contar com a
  velocidade da parede no ponto de impacto.
- As bolas nunca podem sair do polígono nem sobrepor-se entre si.
- As bolas começam todas próximas do centro, com velocidade nula.
- **Não uses nenhuma biblioteca de física.** Escreve a deteção e a resposta à
  colisão tu próprio.

Contrato de verificação — obrigatório, o teste automático depende disto:

Expõe em `window.__bench` um objeto com um método `getState()` que devolve o
estado atual da simulação neste formato exato:

```js
window.__bench = {
  getState() {
    return {
      t: <segundos decorridos desde o início, número>,
      poly: {
        n: 9,
        radius: 260,
        cx: <centro x>,
        cy: <centro y>,
        angle: <ângulo atual do polígono em radianos>,
        periodSec: 7
      },
      balls: [ { id: 0, x: <num>, y: <num>, r: 14, vx: <num>, vy: <num> }, ... ]
    };
  }
};
```

Todas as coordenadas no mesmo referencial do canvas, em pixels.

Adicionalmente, expõe `window.__bench.step(dtSeconds)` que avança a simulação
de forma determinística em `dtSeconds` (usado pelo teste para não depender do
`requestAnimationFrame`). A animação normal continua a correr via
`requestAnimationFrame` quando `step` não é chamado.

Entrega apenas o ficheiro `index.html`. Não escrevas explicações fora do
ficheiro.
