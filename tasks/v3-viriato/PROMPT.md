Implementa o gerador procedural de labirintos do jogo "Viriato's Maze", um
arcade 2D tipo Pac-Man com tema da Guerra Lusitana.

Cria um ficheiro `maze.py` na raiz, com uma função de topo:

```python
def generate_maze(seed: int) -> list[list[int]]:
    """Devolve uma grelha 36 linhas x 28 colunas.
    0 = corredor (transitável), 1 = parede.
    """
```

Restrições que o labirinto tem de cumprir, para qualquer seed:

1. **Dimensões**: exatamente 36 linhas por 28 colunas.
2. **Bordadura**: toda a linha 0, a linha 35, a coluna 0 e a coluna 27 são
   parede, com a exceção dos túneis laterais descritos em (6).
3. **Simetria horizontal**: a grelha é simétrica em espelho no eixo vertical,
   ou seja `grid[r][c] == grid[r][27 - c]` para todos os r e c.
4. **Sem dead ends**: nenhuma célula de corredor pode ter apenas um vizinho de
   corredor na vizinhança de 4 (norte, sul, este, oeste). Todo o corredor tem
   de ter 2 ou mais saídas.
5. **Componente conexo único**: todas as células de corredor formam uma única
   componente conexa na vizinhança de 4.
6. **Castrum central**: existe uma zona retangular sólida de parede com
   exatamente 6 colunas de largura por 4 linhas de altura, horizontalmente
   centrada (colunas 11 a 16 inclusive), colocada entre as linhas 15 e 18
   inclusive. O castrum é rodeado de corredor em todos os lados.
7. **Túneis laterais**: existe exatamente uma linha em que a coluna 0 e a
   coluna 27 são corredor, formando o túnel de wrap-around esquerda–direita.
   Essa linha não pode atravessar o castrum.
8. **Densidade**: entre 35% e 60% das células da grelha são corredor.
9. **Determinismo**: a mesma seed produz sempre exatamente a mesma grelha, e
   seeds diferentes produzem grelhas diferentes.

Escreve também uma função `render(grid) -> str` que devolva a grelha como texto
ASCII, usando `#` para parede e espaço para corredor, uma linha por linha.

Se `maze.py` for executado diretamente, deve imprimir o labirinto da seed 1.

Não uses bibliotecas fora da standard library.
