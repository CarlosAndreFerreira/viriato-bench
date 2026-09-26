.PHONY: setup smoke claude qwen score dash slides arena check-reference clean

setup:            ## verifica o ambiente
	./setup.sh

smoke:            ## run unica, so lado local, tarefa mais rapida
	K=1 TASKS=a1-bugfix SIDES=qwen ./bench.sh

claude:           ## lado Claude, k=3 (CORRE DIAS ANTES: gasta quota)
	SIDES=claude K=3 ./bench.sh

qwen:             ## lado local, k=3
	SIDES=qwen K=3 ./bench.sh

score:            ## agrega em pass@1
	python3 score.py
	python3 score.py --json dashboard/summary.json

dash:             ## abre o dashboard
	xdg-open dashboard/index.html

slides:           ## abre a apresentacao (serve o repo em 127.0.0.1:8765 para os iframes)
	@python3 -m http.server 8765 --bind 127.0.0.1 >/dev/null 2>&1 & sleep 1; \
	 xdg-open http://127.0.0.1:8765/slides/presentation_viriato_en.html; \
	 echo "servidor em 127.0.0.1:8765 - para parar: pkill -f 'http.server 8765'"

arena:            ## abre o explorador interativo da arena multi-modelo
	xdg-open arena/index.html


check-reference:  ## prova que os 3 checkers sao passaveis (V1, V2, V3)
	@rm -rf /tmp/lb-ref && mkdir -p /tmp/lb-ref/v1 /tmp/lb-ref/v2 /tmp/lb-ref/v3
	@cp verify/reference_v1.html /tmp/lb-ref/v1/index.html
	@cp verify/reference_v2.html /tmp/lb-ref/v2/index.html
	@cp verify/reference_maze.py /tmp/lb-ref/v3/maze.py
	@cd /tmp/lb-ref/v3 && python3 $(CURDIR)/tasks/v3-viriato/verify.py
	@cd /tmp/lb-ref/v1 && python3 $(CURDIR)/tasks/v1-polygon/verify.py
	@cd /tmp/lb-ref/v2 && python3 $(CURDIR)/tasks/v2-solar/verify.py

clean:            ## apaga runs e logs, mantem results.csv
	rm -rf runs logs
