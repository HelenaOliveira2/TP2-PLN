"""
Gestor de dados — carrega, guarda e manipula o dicionário médico.
Versão Flask: sem dependências de Streamlit.
"""

import json
import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = _PROJECT_ROOT / "DICIONARIO_GIGANTE_FINAL.json"

# Cache simples em memória (dict mutável)
_cache: dict | None = None


def _load_raw() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_data() -> dict:
    global _cache
    if _cache is None:
        _cache = _load_raw()
    return _cache


def save_data(data: dict) -> None:
    global _cache
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    _cache = data


def add_term(key: str, entry: dict) -> bool:
    data = get_data()
    if key in data:
        return False
    data[key] = entry
    save_data(data)
    return True


def update_term(key: str, entry: dict) -> bool:
    data = get_data()
    data[key] = entry
    save_data(data)
    return True


def delete_term(key: str) -> bool:
    data = get_data()
    if key not in data:
        return False
    del data[key]
    save_data(data)
    return True


def get_all_categories() -> list[str]:
    cats = set()
    for entry in get_data().values():
        for c in entry.get("categorias", []):
            cats.update(c.strip().split())
    return sorted(cats)


def get_all_sources() -> list[str]:
    sources = set()
    for entry in get_data().values():
        for s in entry.get("fontes", []):
            sources.add(s.split("/")[0])
    return sorted(sources)


def get_stats() -> dict:
    data = get_data()
    total = len(data)
    with_def  = sum(1 for e in data.values() if e.get("definicoes"))
    with_syn  = sum(1 for e in data.values() if e.get("sinonimos"))
    with_cat  = sum(1 for e in data.values() if e.get("categorias"))
    with_en   = sum(1 for e in data.values() if e.get("traducoes", {}).get("en"))
    with_es   = sum(1 for e in data.values() if e.get("traducoes", {}).get("es"))

    cat_counts: dict[str, int] = {}
    all_langs: set[str] = set()
    src_counts: dict[str, int] = {}

    for entry in data.values():
        for c in entry.get("categorias", []):
            for word in c.strip().split():
                cat_counts[word] = cat_counts.get(word, 0) + 1
        for lang in entry.get("traducoes", {}).keys():
            if lang and lang != ",":
                all_langs.add(lang)
        for s in entry.get("fontes", []):
            src = s.split("/")[0].replace("_", " ").title()
            src_counts[src] = src_counts.get(src, 0) + 1

    top_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    src_sorted = sorted(src_counts.items(), key=lambda x: x[1])

    return {
        "total":          total,
        "com_definicao":  with_def,
        "com_sinonimos":  with_syn,
        "com_categoria":  with_cat,
        "com_ingles":     with_en,
        "com_espanhol":   with_es,
        "total_linguas":  len(all_langs),
        "top_categorias": top_cats,
        "src_counts":     src_sorted,
        "pct_definicao":  round(with_def / total * 100, 1) if total else 0,
        "pct_sinonimos":  round(with_syn / total * 100, 1) if total else 0,
    }
