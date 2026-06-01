"""
Ponto de entrada da plataforma web — MedLex Explorer.
Redesign premium: estética editorial clara, verde-floresta, tipografia Lora + Outfit.
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from utils.data_manager import get_stats

st.set_page_config(
    page_title="MedLex Explorer",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;0,600;1,400;1,500;1,600&family=Outfit:wght@300;400;500;600&display=swap');

:root {
    --cream:        #f7f5f0;
    --cream-border: #e8e3da;
    --white:        #ffffff;
    --forest:       #2e6b44;
    --forest-light: #4a7c5e;
    --forest-pale:  #eaf4ec;
    --forest-mid:   #c8e6c9;
    --text-dark:    #1a2e1c;
    --text-mid:     #4a5c4e;
    --text-muted:   #7a8c7c;
    --text-faint:   #9aaa9c;
    --amber-pale:   #fef3e2;
    --amber-border: #f5d89c;
    --font-serif:   'Lora', Georgia, serif;
    --font-sans:    'Outfit', system-ui, sans-serif;
    --radius-md:    10px;
    --radius-lg:    14px;
}

html, body, [class*="css"] { font-family: var(--font-sans) !important; }
.stApp { background: var(--cream) !important; }

section[data-testid="stSidebar"] {
    background: var(--white) !important;
    border-right: 1px solid var(--cream-border) !important;
}
section[data-testid="stSidebar"] * { font-family: var(--font-sans) !important; color: var(--text-mid) !important; }
section[data-testid="stSidebar"] a { color: var(--forest) !important; }

h1, h2, h3 { font-family: var(--font-serif) !important; color: var(--text-dark) !important; letter-spacing: -0.02em !important; }
p, li, span { font-family: var(--font-sans) !important; color: var(--text-muted) !important; }

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: var(--white) !important;
    border: 1px solid var(--cream-border) !important;
    border-radius: var(--radius-md) !important;
    color: var(--text-dark) !important;
    font-family: var(--font-sans) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--forest-light) !important;
    box-shadow: 0 0 0 3px rgba(74,124,94,0.12) !important;
}

.stButton > button {
    background: var(--forest) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    font-family: var(--font-sans) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: var(--forest-light) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(46,107,68,0.25) !important;
}

hr { border: none !important; border-top: 1px solid var(--cream-border) !important; margin: 28px 0 !important; }
.stProgress > div > div > div { background: var(--forest) !important; border-radius: 4px !important; }

.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid var(--cream-border) !important; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: var(--text-muted) !important; font-family: var(--font-sans) !important; font-size: 0.85rem !important; padding: 10px 20px !important; border-bottom: 2px solid transparent !important; }
.stTabs [aria-selected="true"] { color: var(--forest) !important; border-bottom-color: var(--forest) !important; background: transparent !important; }

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--cream-border); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: var(--forest-mid); }

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0 !important; max-width: 1100px !important; }

.module-row {
    background: var(--white);
    border-bottom: 1px solid var(--cream-border);
    padding: 18px 22px;
    display: flex;
    align-items: center;
    gap: 16px;
    cursor: pointer;
    transition: background 0.15s;
}
.module-row:hover { background: #f4faf6; }
.module-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; flex-shrink: 0; }
.module-name { font-size: 0.9rem; font-weight: 600; color: var(--text-dark); margin-bottom: 2px; }
.module-desc { font-size: 0.78rem; color: var(--text-muted); }
.module-tag { font-size: 0.7rem; font-weight: 500; color: var(--text-faint); white-space: nowrap; margin-left: auto; padding-right: 8px; }

.stat-card { background: var(--white); border: 1px solid var(--cream-border); border-radius: var(--radius-lg); padding: 18px 20px; }
.stat-val { font-family: var(--font-serif); font-size: 2rem; color: var(--text-dark); font-weight: 500; line-height: 1; margin-bottom: 5px; }
.stat-val-accent { color: var(--forest-light); font-size: 1.1rem; }
.stat-lbl { font-size: 0.7rem; color: var(--text-faint); text-transform: uppercase; letter-spacing: 0.08em; font-weight: 500; }

.metric-card { background: var(--white); border: 1px solid var(--cream-border); border-radius: var(--radius-lg); padding: 20px; border-top: 3px solid var(--forest-mid); }
.metric-number { font-family: var(--font-serif); font-size: 2rem; color: var(--text-dark); font-weight: 500; line-height: 1; margin: 8px 0 6px; }
.metric-label { font-size: 0.7rem; color: var(--text-faint); text-transform: uppercase; letter-spacing: 0.08em; font-weight: 500; }
.metric-sub { font-size: 0.75rem; color: var(--forest-light); margin-top: 5px; }

.entry-card { background: var(--white); border: 1px solid var(--cream-border); border-left: 3px solid var(--forest-mid); border-radius: 0 var(--radius-md) var(--radius-md) 0; padding: 14px 18px; margin-bottom: 8px; cursor: pointer; transition: all 0.15s; }
.entry-card:hover { border-left-color: var(--forest); background: #f4faf6; }
.entry-title { font-size: 0.9rem; font-weight: 600; color: var(--text-dark); }
.entry-meta { font-size: 0.75rem; color: var(--text-faint); margin-top: 3px; }

.badge { display: inline-flex; align-items: center; background: var(--forest-pale); border: 1px solid var(--forest-mid); border-radius: 20px; padding: 3px 10px; font-size: 0.72rem; color: var(--forest); font-weight: 500; letter-spacing: 0.02em; margin: 2px; }
.badge-amber { background: var(--amber-pale); border-color: var(--amber-border); color: #8a5e00; }

.section-lbl { font-size: 0.68rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-faint); margin-bottom: 14px; display: block; }

.info-bar { background: var(--forest-pale); border: 1px solid var(--forest-mid); border-radius: var(--radius-md); padding: 12px 18px; display: flex; align-items: center; gap: 10px; }
.info-dot { width: 7px; height: 7px; background: var(--forest); border-radius: 50%; flex-shrink: 0; }
</style>
""", unsafe_allow_html=True)

# ─── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#fff; border-bottom:1px solid #e8e3da; padding:16px 0; margin-bottom:0;">
    <div style="display:flex; align-items:center; justify-content:space-between; max-width:1100px; margin:0 auto; padding:0 2rem;">
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="width:34px; height:34px; background:#c8e6c9; border-radius:8px;
                display:flex; align-items:center; justify-content:center; font-size:1rem;">🩺</div>
            <span style="font-family:'Lora',serif; font-size:1.1rem; font-weight:600;
                color:#1a2e1c; letter-spacing:-0.01em;">Med<em style="color:#4a7c5e;">Lex</em> Explorer</span>
        </div>
        <span style="font-size:0.72rem; font-weight:500; color:#9aaa9c;
            letter-spacing:0.08em; text-transform:uppercase;">PLN 2025/2026 · TP2</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Hero ──────────────────────────────────────────────────────────────────────
col_hero, col_stats = st.columns([3, 2], gap="large")

with col_hero:
    st.markdown("""
    <div style="padding: 48px 0 32px;">
        <div style="display:inline-flex; align-items:center; gap:7px;
            background:#fef3e2; border:1px solid #f5d89c; border-radius:20px;
            padding:4px 12px; font-size:0.72rem; font-weight:500; color:#8a5e00; margin-bottom:22px;">
            <div style="width:6px;height:6px;background:#f0a500;border-radius:50%;"></div>
            Dicionário médico multilingue
        </div>
        <h1 style="font-family:'Lora',serif; font-size:3rem; font-weight:600;
            color:#1a2e1c; line-height:1.12; letter-spacing:-0.03em; margin:0 0 16px;">
            Terminologia<br>clínica <em style="color:#4a7c5e;">explorada</em>
        </h1>
        <p style="font-size:0.95rem; color:#7a8c7c; line-height:1.75; margin:0 0 30px;
            max-width:400px; font-weight:300;">
            Pesquisa, gere e descobre relações entre termos em
            português, inglês e espanhol com suporte de IA.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_stats:
    _s = get_stats()
    st.markdown("<div style='padding-top:48px;'>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="stat-card" style="margin-bottom:10px;">
        <div class="stat-lbl">Termos totais</div>
        <div class="stat-val">{_s['total']:,}</div>
    </div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-lbl">Com definição</div>
            <div class="stat-val" style="font-size:1.5rem;">{_s['pct_definicao']}<span class="stat-val-accent" style="font-size:0.9rem;">%</span></div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-lbl">Línguas</div>
            <div class="stat-val" style="font-size:1.5rem;">{_s['total_linguas']}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ─── Módulos ───────────────────────────────────────────────────────────────────
st.markdown('<span class="section-lbl">Módulos disponíveis</span>', unsafe_allow_html=True)

modules = [
    ("📊", "#eaf4ec", "#2e6b44", "Dashboard", "Estatísticas e visão geral do dataset",        "Gráficos interativos", "pages/1_Dashboard.py"),
    ("🔍", "#e8f0fe", "#3b5998", "Pesquisa",  "Filtra e explora termos por idioma ou texto",  "Busca + filtros",      "pages/2_Pesquisa.py"),
    ("✏️", "#fff3e0", "#8a5e00", "Gestão",   "Adiciona, edita e remove termos do dicionário", "CRUD completo",        "pages/3_Gestão.py"),
    ("🤖", "#fce4ec", "#8b1a35", "IR + QA",  "Pesquisa de artigos e perguntas à IA",          "LLM-powered",          "pages/4_IR_QA.py"),
]

cols = st.columns(4, gap="medium")
for col, (icon, bg, accent, name, desc, tag, page) in zip(cols, modules):
    with col:
        st.markdown(f"""
        <div style="
            background: var(--white);
            border: 1px solid var(--cream-border);
            border-top: 3px solid {accent}55;
            border-radius: var(--radius-lg);
            padding: 22px 18px 14px;
            margin-bottom: 8px;
        ">
            <div style="
                width: 42px; height: 42px;
                background: {bg};
                border-radius: 10px;
                display: flex; align-items: center; justify-content: center;
                font-size: 1.2rem; margin-bottom: 14px;
            ">{icon}</div>
            <div style="font-family:'Lora',serif; font-size:1rem; font-weight:600;
                color: var(--text-dark); margin-bottom: 6px;">{name}</div>
            <div style="font-size:0.78rem; color: var(--text-muted);
                line-height:1.5; margin-bottom:14px;">{desc}</div>
            <div style="font-size:0.68rem; font-weight:600; letter-spacing:0.08em;
                text-transform:uppercase; color:{accent};">{tag}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Abrir →", key=f"nav_{name}", use_container_width=True):
            st.switch_page(page)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Status ──────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="info-bar">
    <div class="info-dot"></div>
    <span style="font-size:0.8rem; color:#4a7c5e; font-weight:400;">
        Sistema operacional — clica num módulo acima ou usa o menu lateral.
    </span>
</div>
""", unsafe_allow_html=True)