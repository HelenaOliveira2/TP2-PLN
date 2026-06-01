"""
MedLex Explorer — Aplicação Flask principal.
Rotas: /, /dashboard, /pesquisa, /gestao, /ir_qa
CRUD: /gestao/add, /gestao/update, /gestao/delete
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from pathlib import Path
from utils.enricher import enrich_term_data
from utils.scraper import scrape_and_save_articles, load_articles

# ══════════════════════════════════════════════════════════════════════════════
# Configurações e Dados (Antigo data_manager.py)
# ══════════════════════════════════════════════════════════════════════════════

app = Flask(__name__)
app.secret_key = "medlex-secret-2025"   # necessário para flash messages

_PROJECT_ROOT = Path(__file__).resolve().parent
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
            if c.strip():
                cats.add(c.strip())
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
            cat = c.strip()
            if cat:
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
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


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def split_comma(s: str) -> list[str]:
    return [x.strip() for x in s.split(",") if x.strip()]

def split_space(s: str) -> list[str]:
    return [x.strip() for x in s.split() if x.strip()]

def score_entry(key: str, entry: dict, q: str) -> int:
    q = q.lower()
    score = 0
    if q in key:                                              score += 10
    if q in entry.get("termo_principal", "").lower():         score += 8
    for syn in entry.get("sinonimos", []):
        if q in syn.lower():                                  score += 6
    for d in entry.get("definicoes", []):
        if q in d.lower():                                    score += 4
    for lang_vals in entry.get("traducoes", {}).values():
        for t in (lang_vals if isinstance(lang_vals, list) else [lang_vals]):
            if q in str(t).lower():                           score += 3
    return score


# ══════════════════════════════════════════════════════════════════════════════
# Homepage
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/")
def index():
    stats = get_stats()
    return render_template("index.html", active_page="home", stats=stats)


# ══════════════════════════════════════════════════════════════════════════════
# Dashboard
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/dashboard")
def dashboard():
    stats = get_stats()

    # Dados para os gráficos — enviados como listas para o Jinja → JS
    top_cats    = stats["top_categorias"]
    cat_labels  = [c[0] for c in top_cats]
    cat_values  = [c[1] for c in top_cats]

    data        = get_data()
    lang_map    = {"pt": "Português", "en": "Inglês", "es": "Espanhol",
                   "fr": "Francês",   "la": "Latim",  "ar": "Árabe",
                   "de": "Alemão",    "zh": "Chinês",  "ja": "Japonês"}
    lang_counts: dict[str, int] = {}
    for entry in data.values():
        for lang, vals in entry.get("traducoes", {}).items():
            if vals and lang and lang != ",":
                lang_counts[lang] = lang_counts.get(lang, 0) + 1

    # Agrupamos línguas: mantemos apenas as top 5 e o resto vai para "Outras"
    lang_sorted = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)
    lang_labels, lang_values = [], []
    outras = 0
    for i, (lang, cnt) in enumerate(lang_sorted):
        if i < 5:
            lang_labels.append(lang_map.get(lang, lang.upper()))
            lang_values.append(cnt)
        else:
            outras += cnt
    if outras:
        lang_labels.append("Outras")
        lang_values.append(outras)

    src_sorted  = stats["src_counts"]
    src_labels  = [s[0] for s in src_sorted]
    src_values  = [s[1] for s in src_sorted]

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        stats=stats,
        cat_labels=cat_labels, cat_values=cat_values,
        lang_labels=lang_labels, lang_values=lang_values,
        src_labels=src_labels, src_values=src_values,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Pesquisa
# ══════════════════════════════════════════════════════════════════════════════

PAGE_SIZE = 20

@app.get("/pesquisa")
def pesquisa():
    data        = get_data()
    all_cats    = get_all_categories()
    all_srcs    = get_all_sources()

    query       = request.args.get("q", "").strip()
    cat_filter  = request.args.get("cat", "")
    src_filter  = request.args.get("src", "")
    lang_filter = request.args.get("lang", "")
    sort        = request.args.get("sort", "rel")
    has_def     = bool(request.args.get("has_def"))
    has_syn     = bool(request.args.get("has_syn"))
    page        = max(1, int(request.args.get("p", 1)))

    results = []
    for key, entry in data.items():
        # Pontuação de relevância
        if query:
            s = score_entry(key, entry, query)
            if s == 0:
                continue
        else:
            s = 0

        # Filtros
        if cat_filter:
            entry_cats = " ".join(entry.get("categorias", []))
            if cat_filter not in entry_cats:
                continue
        if src_filter:
            entry_srcs = [f.split("/")[0] for f in entry.get("fontes", [])]
            if src_filter not in entry_srcs:
                continue
        if lang_filter:
            if not entry.get("traducoes", {}).get(lang_filter):
                continue
        if has_def and not entry.get("definicoes"):
            continue
        if has_syn and not entry.get("sinonimos"):
            continue

        results.append((key, entry, s))

    # Ordenação
    if sort == "rel" and query:
        results.sort(key=lambda x: x[2], reverse=True)
    elif sort == "az":
        results.sort(key=lambda x: x[0])
    elif sort == "za":
        results.sort(key=lambda x: x[0], reverse=True)

    total       = len(results)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page        = min(page, total_pages)
    page_results = [(k, e) for k, e, _ in results[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]]

    # Query string para paginação (sem o 'p')
    qs_parts = []
    for k, v in [("q", query), ("cat", cat_filter), ("src", src_filter),
                  ("lang", lang_filter), ("sort", sort)]:
        if v:
            qs_parts.append(f"{k}={v}")
    if has_def: qs_parts.append("has_def=1")
    if has_syn: qs_parts.append("has_syn=1")
    pagination_qs = "&".join(qs_parts)

    return render_template(
        "pesquisa.html",
        active_page="pesquisa",
        query=query,
        cat_filter=cat_filter, src_filter=src_filter,
        lang_filter=lang_filter, sort=sort,
        has_def=has_def, has_syn=has_syn,
        all_cats=all_cats, all_srcs=all_srcs,
        results=page_results,
        total=total, page=page, total_pages=total_pages,
        pagination_qs=pagination_qs,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Gestão (CRUD)
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/gestao")
def gestao():
    data        = get_data()
    active_tab  = request.args.get("tab", "add")

    # ── Editar ──────────────────────────────────────────────
    edit_search  = request.args.get("edit", "").strip().lower()
    edit_key     = request.args.get("edit_key", "")
    edit_matches = []
    edit_entry   = None

    if edit_search:
        edit_matches = [k for k in data if edit_search in k][:20]
        if not edit_key and edit_matches:
            edit_key = edit_matches[0]
        if edit_key and edit_key in data:
            edit_entry = data[edit_key]

    # ── Apagar ──────────────────────────────────────────────
    del_search  = request.args.get("del", "").strip().lower()
    del_key     = request.args.get("del_key", "")
    del_matches = []
    del_entry   = None

    if del_search:
        del_matches = [k for k in data if del_search in k][:20]
        if not del_key and del_matches:
            del_key = del_matches[0]
        if del_key and del_key in data:
            del_entry = data[del_key]

    return render_template(
        "gestao.html",
        active_page="gestao",
        active_tab=active_tab,
        data=data,
        edit_search=edit_search, edit_key=edit_key,
        edit_matches=edit_matches, edit_entry=edit_entry,
        del_search=del_search, del_key=del_key,
        del_matches=del_matches, del_entry=del_entry,
    )


@app.post("/gestao/add")
def gestao_add():
    termo     = request.form.get("termo", "").strip()
    if not termo:
        flash("O campo 'Termo Principal' é obrigatório.", "warning")
        return redirect(url_for("gestao"))

    entry = {
        "termo_principal":  termo,
        "categorias":       split_space(request.form.get("categorias", "")),
        "definicoes":       [request.form["definicao"].strip()] if request.form.get("definicao", "").strip() else [],
        "sinonimos":        split_comma(request.form.get("sinonimos", "")),
        "siglas":           split_comma(request.form.get("siglas", "")),
        "termos_relacionados": split_comma(request.form.get("termos_rel", "")),
        "traducoes": {
            "pt": split_comma(request.form.get("pt", "")),
            "en": split_comma(request.form.get("en", "")),
            "es": split_comma(request.form.get("es", "")),
        },
        "fontes": ["utilizador"],
    }
    genero = request.form.get("genero", "")
    if genero:
        entry["genero"] = genero

    key = termo.lower()
    if add_term(key, entry):
        flash(f"Termo \"{termo}\" adicionado com sucesso!", "success")
    else:
        flash(f"O termo \"{termo}\" já existe. Usa a aba Editar para modificar.", "warning")

    return redirect(url_for("gestao"))


@app.post("/gestao/update")
def gestao_update():
    key   = request.form.get("key", "")
    termo = request.form.get("termo", "").strip()

    data  = get_data()
    if key not in data:
        flash("Termo não encontrado.", "danger")
        return redirect(url_for("gestao", tab="edit"))

    entry = data[key].copy()
    entry["termo_principal"]    = termo
    entry["categorias"]         = split_space(request.form.get("categorias", ""))
    entry["definicoes"]         = [request.form["definicao"].strip()] if request.form.get("definicao", "").strip() else []
    entry["sinonimos"]          = split_comma(request.form.get("sinonimos", ""))
    entry["siglas"]             = split_comma(request.form.get("siglas", ""))
    entry["termos_relacionados"]= split_comma(request.form.get("termos_rel", ""))
    entry["traducoes"]          = {
        "pt": split_comma(request.form.get("pt", "")),
        "en": split_comma(request.form.get("en", "")),
        "es": split_comma(request.form.get("es", "")),
    }
    genero = request.form.get("genero", "")
    if genero:
        entry["genero"] = genero

    update_term(key, entry)
    flash(f"Termo \"{termo}\" atualizado e guardado!", "success")
    return redirect(url_for("gestao", tab="edit"))


@app.post("/gestao/delete")
def gestao_delete():
    key     = request.form.get("key", "")
    confirm = request.form.get("confirm")

    if not confirm:
        flash("Tens de confirmar antes de apagar.", "warning")
        return redirect(url_for("gestao", tab="delete"))

    data = get_data()
    nome = data.get(key, {}).get("termo_principal", key)

    if delete_term(key):
        flash(f"Termo \"{nome}\" apagado com sucesso!", "success")
    else:
        flash("Erro ao apagar o termo.", "danger")

    return redirect(url_for("gestao", tab="delete"))


# ══════════════════════════════════════════════════════════════════════════════
# API de Enriquecimento
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/enrich")
def api_enrich():
    term = request.args.get("term", "").strip()
    if not term:
        return {"error": "Nenhum termo fornecido"}, 400
    try:
        enrichment = enrich_term_data(term)
        return enrichment
    except Exception as e:
        return {"error": str(e)}, 500


# ══════════════════════════════════════════════════════════════════════════════
# IR + QA (Fase 3 e 4)
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/ir_qa")
def ir_qa():
    articles = load_articles()
    articles_count = len(articles)
    return render_template("ir_qa.html", active_page="ir_qa", articles_count=articles_count)


# ══════════════════════════════════════════════════════════════════════════════
# API de Web Scraping do PubMed
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/scrape")
def api_scrape():
    query = request.form.get("query", "").strip()
    limit = request.form.get("limit", "5").strip()
    
    if not query:
        return {"error": "Termo de pesquisa obrigatório"}, 400
        
    try:
        max_results = int(limit)
    except ValueError:
        max_results = 5
        
    try:
        new_added = scrape_and_save_articles(query, max_results)
        articles = load_articles()
        return {
            "success": True,
            "new_added": new_added,
            "total_articles": len(articles)
        }
    except Exception as e:
        return {"error": str(e)}, 500


# ══════════════════════════════════════════════════════════════════════════════
# Arranque
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app.run(debug=True, port=5000)
