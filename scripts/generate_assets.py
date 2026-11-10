#!/usr/bin/env python3
"""Gera docs/painel_exemplo.svg e renderiza docs/exemplo.png via headless Chrome/Chromium."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys

raiz = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(raiz / "src"))

from climatizacao_nbr16401.calculator import calcular_climatizacao_nbr16401
from climatizacao_nbr16401.codecs import decodificar_espaco_json
from climatizacao_nbr16401.svg_generator import gerar_painel_svg


def encontrar_chrome() -> str | None:
    for nome in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        caminho = shutil.which(nome)
        if caminho:
            return caminho
    return None


def main() -> int:
    arquivo_exemplo = raiz / "examples" / "escritorio_corporativo_paulista.json"
    if not arquivo_exemplo.exists():
        print(f"Erro: Arquivo {arquivo_exemplo} não encontrado.")
        return 1

    espaco = decodificar_espaco_json(arquivo_exemplo.read_text(encoding="utf-8"))
    resultado = calcular_climatizacao_nbr16401(espaco)
    svg_conteudo = gerar_painel_svg(resultado)

    docs_dir = raiz / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    caminho_svg = docs_dir / "painel_exemplo.svg"
    caminho_svg.write_text(svg_conteudo, encoding="utf-8")
    print(f"SVG gravado em: {caminho_svg}")

    caminho_png = docs_dir / "exemplo.png"
    chrome_bin = encontrar_chrome()
    if not chrome_bin:
        print("Aviso: Google Chrome / Chromium não encontrado para capturar PNG.")
        return 0

    cmd = [
        chrome_bin,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--window-size=1440,900",
        f"--screenshot={caminho_png}",
        str(caminho_svg),
    ]

    print(f"Executando renderização com {chrome_bin}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and caminho_png.exists():
        tamanho = caminho_png.stat().st_size
        print(f"Screenshot PNG gerado com sucesso: {caminho_png} ({tamanho} bytes)")
    else:
        print(f"Aviso na geração de PNG: {res.stderr}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
