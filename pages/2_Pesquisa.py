"""
P�gina de Pesquisa — permite pesquisar e filtrar termos do dicionário médico.
Redesign: estética editorial clara, verde-floresta, tipografia Lora + Outfit.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from utils.data_manager import get_data, get_all_categories, get_all_sources

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:28px 0 24px;">
    <div style="display:flex; align-items:baseline; gap:12px; margin-bottom:6px;">
        <h1 style="font-family:'Lora',serif; font-size:2rem; font-weight:600;
            color:#1a2e1c; margin:0; letter-spacing:-0.02em;">Pesquisa de Termos</h1>
    </div>
    <p style="color:#9aaa9c; font-size:0.85rem; margin:0;">
        Pesquisa, filtra e explora o dicionário médico multilingue
    </p>
</div>
""", unsafe_allow_html=True)

# ── Barra de pesquisa principal ───────────────────────────────────────────────
query = st.text_input(
    "Pesquisar termo",
    placeholder="Escreve um termo, sinónimo ou definição...",
    key="search_query",
    label_visibility="collapsed",
)

# ── Filtros laterais ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:18px 0 10px;">
        <span style="font-size:0.68rem; font-weight:600; letter-spacing:0.1em;
            text-transform:uppercase; color:#9aaa9c;">Filtros</span>
    </div>
    """, unsafe_allow_html=True)

    all_cats = get_all_categories()
    selected_cats = st.multiselect(
        "Categorias",
        options=all_cats,
        placeholder="Todas as categorias",
    )

    all_srcs = get_all_sources()
    selected_srcs = st.multiselect(
        "Fonte",
        options=all_srcs,
        placeholder="Todas as fontes",
    )

    lang_filter = st.selectbox(
        "Tem tradução em",
        options=["Qualquer", "Inglês (en)", "Espanhol (es)"],
    )

    has_def = st.checkbox("Apenas com definição")
    has_syn = st.checkbox("Apenas com sinónimos")

    sort_by = st.radio(
        "Ordenar por",
        options=["Relevância", "Alfabética (A→Z)", "Alfabética (Z→A)"],
    )

    st.markdown("---")
    if st.button("Limpar filtros"):
        st.rerun()

# ── Lógica de pesquisa ────────────────────────────────────────────────────────
data = get_data()

def score_entry(key, entry, q):
    q = q.lower()
    score = 0
    if q in key: score += 10
    if q in entry.get("termo_principal", "").lower(): score += 8
    for syn in entry.get("sinonimos", []):
        if q in syn.lower(): score += 6
    for d in entry.get("definicoes", []):
        if q in d.lower(): score += 4
    for lang_vals in entry.get("traducoes", {}).values():
        for t in lang_vals:
            if q in t.lower(): score += 3
    return score

lang_map = {"Inglês (en)": "en", "Espanhol (es)": "es"}
results = []

for key, entry in data.items():
    if query:
        s = score_entry(key, entry, query)
        if s == 0: continue
    else:
        s = 0
    if selected_cats:
        entry_cats = " ".join(entry.get("categorias", []))
        if not any(c in entry_cats for c in selected_cats): continue
    if selected_srcs:
        entry_srcs = [f.split("/")[0] for f in entry.get("fontes", [])]
        if not any(sf in entry_srcs for sf in selected_srcs): continue
    if lang_filter != "Qualquer":
        lang_code = lang_map[lang_filter]
        if not entry.get("traducoes", {}).get(lang_code): continue
    if has_def and not entry.get("definicoes"): continue
    if has_syn and not entry.get("sinonimos"): continue
    results.append((key, entry, s))

if sort_by == "Relevância" and query:
    results.sort(key=lambda x: x[2], reverse=True)
elif sort_by == "Alfabética (A→Z)":
    results.sort(key=lambda x: x[0])
elif sort_by == "Alfabética (Z→A)":
    results.sort(key=lambda x: x[0], reverse=True)

# ── Barra de resultados ───────────────────────────────────────────────────────
total = len(results)

if not query and not selected_cats and not selected_srcs and lang_filter == "Qualquer" and not has_def and not has_syn:
    st.markdown("""
    <div style="background:#fff; border:1px solid #e8e3da; border-radius:14px;
        padding:48px 32px; text-align:center; margin-top:12px;">
        <div style="font-size:2.5rem; margin-bottom:14px; opacity:0.4;">🔍</div>
        <p style="font-family:'Lora',serif; font-size:1.1rem; color:#4a5c4e;
            font-style:italic; margin:0 0 8px;">Começa por escrever um termo</p>
        <p style="font-size:0.82rem; color:#9aaa9c; margin:0;">
            Pesquisa por nome, sinónimo, definição ou tradução
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Contador de resultados
st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:space-between;
    padding:10px 0 16px;">
    <span style="font-size:0.8rem; color:#9aaa9c;">
        <span style="font-weight:600; color:#2e6b44;">{total:,}</span>
        resultado{'s' if total != 1 else ''} encontrado{'s' if total != 1 else ''}
        {f'para <em style="color:#4a5c4e;">"{query}"</em>' if query else ''}
    </span>
</div>
""", unsafe_allow_html=True)

# ── Sem resultados ────────────────────────────────────────────────────────────
if not results:
    st.markdown("""
    <div style="background:#fff; border:1px solid #e8e3da; border-radius:14px;
        padding:48px 32px; text-align:center; margin-top:8px;">
        <div style="font-size:2.5rem; margin-bottom:14px; opacity:0.3;">🔍</div>
        <p style="font-family:'Lora',serif; font-size:1.1rem; color:#4a5c4e;
            font-style:italic; margin:0 0 8px;">Nenhum resultado encontrado</p>
        <p style="font-size:0.82rem; color:#9aaa9c; margin:0;">
            Tenta um termo diferente ou remove alguns filtros.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Paginação ─────────────────────────────────────────────────────────────────
PAGE_SIZE   = 20
total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

if total_pages > 1:
    col_pag, _ = st.columns([2, 5])
    with col_pag:
        page = st.number_input("Página", min_value=1, max_value=total_pages, value=1, step=1, label_visibility="collapsed")
else:
    page = 1

page_results = results[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]

# ── Lista de resultados ───────────────────────────────────────────────────────
lang_names = {"pt": "PT", "en": "EN", "es": "ES"}
lang_flags  = {"pt": "🇵🇹", "en": "🇬🇧", "es": "🇪🇸"}

for key, entry, _ in page_results:
    term  = entry.get("termo_principal", key)
    cats  = entry.get("categorias", [])
    defs  = entry.get("definicoes", [])
    syns  = entry.get("sinonimos", [])
    trad  = entry.get("traducoes", {})
    fontes = entry.get("fontes", [])

    cats_html = "".join(
        f'<span style="background:#eaf4ec; border:1px solid #c8e6c9; border-radius:20px; '
        f'padding:2px 9px; font-size:0.68rem; color:#2e6b44; font-weight:500; '
        f'margin-right:4px;">{c}</span>'
        for c in cats[:3]
    )

    has_en = bool(trad.get("en"))
    has_es = bool(trad.get("es"))
    flag_html = ""
    if has_en: flag_html += '<span style="font-size:0.85rem; margin-right:4px;">🇬🇧</span>'
    if has_es: flag_html += '<span style="font-size:0.85rem; margin-right:4px;">🇪🇸</span>'

    first_def = defs[0][:120] + "…" if defs and len(defs[0]) > 120 else (defs[0] if defs else "")

    with st.expander(f"{term}", expanded=False):
        # Header interno
        st.markdown(f"""
        <div style="display:flex; align-items:center; flex-wrap:wrap;
            gap:6px; margin-bottom:16px; padding-bottom:14px;
            border-bottom:1px solid #f0ece4;">
            <span style="font-family:'Lora',serif; font-size:1.25rem;
                font-weight:600; color:#1a2e1c; margin-right:4px;">{term}</span>
            {cats_html}
            <span style="margin-left:auto;">{flag_html}</span>
        </div>
        """, unsafe_allow_html=True)

        col_main, col_side = st.columns([3, 1])

        with col_main:
            if defs:
                st.markdown("""
                <div style="font-size:0.68rem; font-weight:600; letter-spacing:0.1em;
                    text-transform:uppercase; color:#9aaa9c; margin-bottom:8px;">Definição</div>
                """, unsafe_allow_html=True)
                for d in defs[:2]:
                    st.markdown(f"""
                    <div style="background:#f7f5f0; border-left:3px solid #c8e6c9;
                        border-radius:0 8px 8px 0; padding:12px 16px; margin-bottom:8px;
                        font-size:0.88rem; color:#4a5c4e; line-height:1.65;">{d}</div>
                    """, unsafe_allow_html=True)

            if syns:
                st.markdown("""
                <div style="font-size:0.68rem; font-weight:600; letter-spacing:0.1em;
                    text-transform:uppercase; color:#9aaa9c; margin:14px 0 8px;">Sinónimos</div>
                """, unsafe_allow_html=True)
                syns_html = "".join(
                    f'<span style="background:#fff; border:1px solid #e8e3da; border-radius:20px; '
                    f'padding:3px 10px; font-size:0.78rem; color:#4a5c4e; margin:2px 3px 2px 0; '
                    f'display:inline-block;">{s}</span>'
                    for s in syns
                )
                st.markdown(f'<div style="line-height:2;">{syns_html}</div>', unsafe_allow_html=True)

            termos_rel = entry.get("termos_relacionados", [])
            if termos_rel:
                st.markdown("""
                <div style="font-size:0.68rem; font-weight:600; letter-spacing:0.1em;
                    text-transform:uppercase; color:#9aaa9c; margin:14px 0 8px;">Termos relacionados</div>
                """, unsafe_allow_html=True)
                rel_html = "".join(
                    f'<span style="font-size:0.78rem; color:#4a7c5e; margin-right:10px;">→ {t}</span>'
                    for t in termos_rel[:5]
                )
                st.markdown(f'<div>{rel_html}</div>', unsafe_allow_html=True)

        with col_side:
            if any(trad.values()):
                st.markdown("""
                <div style="font-size:0.68rem; font-weight:600; letter-spacing:0.1em;
                    text-transform:uppercase; color:#9aaa9c; margin-bottom:10px;">Traduções</div>
                """, unsafe_allow_html=True)
                for lang, vals in trad.items():
                    if vals:
                        st.markdown(f"""
                        <div style="display:flex; align-items:flex-start; gap:8px;
                            padding:8px 0; border-bottom:1px solid #f0ece4;">
                            <span style="font-size:0.85rem; flex-shrink:0;">{lang_flags.get(lang,'')}</span>
                            <div>
                                <div style="font-size:0.65rem; font-weight:600; letter-spacing:0.06em;
                                    text-transform:uppercase; color:#c5d0c7; margin-bottom:1px;">{lang.upper()}</div>
                                <div style="font-size:0.82rem; color:#4a5c4e; font-style:italic;">{vals[0]}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            if fontes:
                st.markdown("""
                <div style="font-size:0.68rem; font-weight:600; letter-spacing:0.1em;
                    text-transform:uppercase; color:#9aaa9c; margin:14px 0 8px;">Fonte</div>
                """, unsafe_allow_html=True)
                for f in fontes[:2]:
                    st.markdown(f"""
                    <div style="font-size:0.75rem; color:#9aaa9c; padding:3px 0;">{f.split('/')[0]}</div>
                    """, unsafe_allow_html=True)

        # Ações
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        btn1, btn2, _ = st.columns([1, 1, 4])
        with btn1:
            if st.button("Editar", key=f"edit_{key}"):
                st.session_state["edit_key"] = key
                st.switch_page("pages/3_Gestão.py")
        with btn2:
            if st.button("Ver artigos", key=f"ir_{key}"):
                st.session_state["ir_query"] = term
                st.switch_page("pages/4_IR_QA.py")

# ── Footer de paginação ───────────────────────────────────────────────────────
if total_pages > 1:
    st.markdown(f"""
    <div style="text-align:center; padding:24px 0 8px;">
        <span style="font-size:0.78rem; color:#c5d0c7;">
            Página {page} de {total_pages} &nbsp;·&nbsp; {total:,} resultados
        </span>
    </div>
    """, unsafe_allow_html=True)