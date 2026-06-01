"""
Gestor de dados — carrega, guarda e manipula o dicionário médico.
Toda a persistência passa por aqui para garantir que nenhuma alteração se perde.
"""

import json
import os
from pathlib import Path
import streamlit as st

# Raiz do projeto = pasta onde está data_manager.py/../  (utils/../)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = str(_PROJECT_ROOT / "DICIONARIO_GIGANTE_FINAL.json")


@st.cache_data(show_spinner=False)
def _load_raw() -> dict:
    """Carrega o JSON do disco (com cache do Streamlit)."""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_data() -> dict:
    """Devolve o dicionário a partir do session_state (fonte de verdade em runtime)."""
    if "dicionario" not in st.session_state:
        st.session_state["dicionario"] = _load_raw()
    return st.session_state["dicionario"]


def save_data() -> None:
    """Persiste o dicionário atual no disco."""
    data = st.session_state.get("dicionario", {})
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # Limpa o cache para que um novo load reflita as alterações
    _load_raw.clear()


def add_term(key: str, entry: dict) -> bool:
    """
    Adiciona um novo termo. Devolve True se criado, False se já existia.
    """
    data = get_data()
    norm = key.strip().lower()
    if norm in data:
        return False
    data[norm] = entry
    save_data()
    return True


def update_term(key: str, entry: dict) -> None:
    """Atualiza um termo existente e guarda."""
    data = get_data()
    data[key] = entry
    save_data()


def delete_term(key: str) -> bool:
    """Apaga um termo. Devolve True se apagado, False se não existia."""
    data = get_data()
    if key not in data:
        return False
    del data[key]
    save_data()
    return True


def get_all_categories() -> list[str]:
    """Devolve todas as categorias únicas presentes no dicionário."""
    cats = set()
    for entry in get_data().values():
        for c in entry.get("categorias", []):
            cats.update(c.strip().split())
    return sorted(cats)


def get_all_sources() -> list[str]:
    """Devolve todas as fontes únicas."""
    sources = set()
    for entry in get_data().values():
        for s in entry.get("fontes", []):
            sources.add(s.split("/")[0])
    return sorted(sources)


def get_stats() -> dict:
    """Calcula estatísticas gerais do dicionário."""
    data = get_data()
    total = len(data)
    with_def = sum(1 for e in data.values() if e.get("definicoes"))
    with_syn = sum(1 for e in data.values() if e.get("sinonimos"))
    with_cat = sum(1 for e in data.values() if e.get("categorias"))
    with_en = sum(1 for e in data.values() if e.get("traducoes", {}).get("en"))
    with_es = sum(1 for e in data.values() if e.get("traducoes", {}).get("es"))

    cat_counts: dict[str, int] = {}
    all_langs = set()
    for entry in data.values():
        # Contar categorias
        for c in entry.get("categorias", []):
            for word in c.strip().split():
                cat_counts[word] = cat_counts.get(word, 0) + 1
        # Contar línguas
        for lang in entry.get("traducoes", {}).keys():
            if lang and lang != ",":
                all_langs.add(lang)

    top_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:15]

    return {
        "total": total,
        "com_definicao": with_def,
        "com_sinonimos": with_syn,
        "com_categoria": with_cat,
        "com_ingles": with_en,
        "com_espanhol": with_es,
        "total_linguas": len(all_langs),
        "top_categorias": top_cats,
        "pct_definicao": round(with_def / total * 100, 1),
        "pct_sinonimos": round(with_syn / total * 100, 1),
    }
