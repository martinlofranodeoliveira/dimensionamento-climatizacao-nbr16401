#!/usr/bin/env python3
"""Inspeciona pacotes gerados em dist/ (sdist tar.gz e bdist wheel) validando estrutura e arquivos."""

from __future__ import annotations

from pathlib import Path
import sys
import tarfile
import zipfile


def verificar_sdist(caminho: Path) -> None:
    print(f"Verificando sdist: {caminho.name}")
    with tarfile.open(caminho, "r:gz") as tar:
        nomes = tar.getnames()
        obrigatorios = ["pyproject.toml", "LICENSE", "src/climatizacao_nbr16401/__init__.py"]
        for ob in obrigatorios:
            if not any(n.endswith(ob) for n in nomes):
                raise AssertionError(f"Arquivo obrigatório '{ob}' ausente no sdist {caminho.name}.")
    print("  -> sdist verificado com sucesso.")


def verificar_wheel(caminho: Path) -> None:
    print(f"Verificando wheel: {caminho.name}")
    with zipfile.ZipFile(caminho, "r") as zf:
        nomes = zf.namelist()
        obrigatorios = [
            "climatizacao_nbr16401/__init__.py",
            "climatizacao_nbr16401/py.typed",
            "climatizacao_nbr16401/calculator.py",
            "climatizacao_nbr16401/models.py",
        ]
        for ob in obrigatorios:
            if ob not in nomes:
                raise AssertionError(f"Arquivo obrigatório '{ob}' ausente no wheel {caminho.name}.")
    print("  -> wheel verificado com sucesso.")


def main() -> int:
    raiz = Path(__file__).resolve().parent.parent
    dist_dir = raiz / "dist"
    if not dist_dir.exists():
        print("Erro: pasta dist/ não encontrada.")
        return 1

    sdists = list(dist_dir.glob("*.tar.gz"))
    wheels = list(dist_dir.glob("*.whl"))

    if not sdists or not wheels:
        print("Erro: Nenhum sdist ou wheel encontrado em dist/.")
        return 1

    for s in sdists:
        verificar_sdist(s)
    for w in wheels:
        verificar_wheel(w)

    print("Todos os pacotes em dist/ foram validados com êxito!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
