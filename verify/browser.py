"""Utilitarios Playwright partilhados pelos verificadores V1 e V2.

Se o Playwright nao estiver instalado, os verificadores devolvem exit code 2
(SKIP), que o bench.sh distingue de falha. Um skip nunca conta como pass.
"""
from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path

SKIP = 2


def require_playwright():
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
    except ImportError:
        print("SKIP: playwright nao instalado. Ver README, seccao 'Pre-requisitos'.")
        sys.exit(SKIP)
    return sync_playwright


@contextmanager
def page_for(index_html: str = "index.html", frames_dir: str | None = None):
    """Abre index.html do run dir num Chromium headless.

    Devolve a page. Falha com exit 1 se o ficheiro nao existir ou se a pagina
    lancar erros de JavaScript.
    """
    sync_playwright = require_playwright()
    path = Path(index_html).resolve()
    if not path.exists():
        print(f"FAIL: {index_html} nao existe no run dir")
        sys.exit(1)

    errors: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.goto(path.as_uri())
        page.wait_for_timeout(1200)
        try:
            yield page, errors
        finally:
            if frames_dir:
                Path(frames_dir).mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(Path(frames_dir) / "final.png"))
            browser.close()


def has_bench(page) -> bool:
    return bool(page.evaluate("() => !!(window.__bench)"))
