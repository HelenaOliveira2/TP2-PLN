"""
Dashboard — visão geral e estatísticas do dicionário médico.
Redesign premium: estética editorial clara, verde-floresta, tipografia Lora + Outfit.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.data_manager import get_stats, get_data

# ── Paleta para gráficos ──────────────────────────────────────────────────────
FOREST_SCALE = [
    [0.0,  "#eaf4ec"],
    [0.25, "#c8e6c9"],
    [0.55, "#4a7c5e"],
    [1.0,  "#1a2e1c"],
]
MULTI_COLORS = ["#4a7c5e", "#81b894", "#b8d9c0", "#2e6b44", "#c8e6c9", "#6aab7f"]
PLOT_LAYOUT  = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Outfit, system-ui, sans-serif", color="#9aaa9c", size=11),
    margin=dict(l=0, r=0, t=10, b=0),
)

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:28px 0 24px;">
    <div style="display:flex; align-items:baseline; gap:12px; margin-bottom:6px;">
        <h1 style="font-family:'Lora',serif; font-size:2rem; font-weight:600;
            color:#1a2e1c; margin:0; letter-spacing:-0.02em;">Dashboard</h1>
        <span style="font-size:0.7rem; font-weight:600; letter-spacing:0.1em;
            text-transform:uppercase; color:#2e6b44; background:#eaf4ec;
            border:1px solid #c8e6c9; padding:3px 9px; border-radius:20px;">ao vivo</span>
    </div>
    <p style="color:#9aaa9c; font-size:0.85rem; margin:0;">
        Visão geral do dicionário médico multilingue
    </p>
</div>
""", unsafe_allow_html=True)

with st.spinner(""):
    stats = get_stats()

# ── Métricas ──────────────────────────────────────────────────────────────────
cols = st.columns(5)
metrics = [
    (cols[0], "#2e6b44", "T",   f"{stats['total']:,}",          "Termos Totais",  None),
    (cols[1], "#3b5998", "D",   f"{stats['com_definicao']:,}",  "Com Definição",  f"{stats['pct_definicao']}% cobertura"),
    (cols[2], "#8a5e00", "S",   f"{stats['com_sinonimos']:,}",  "Com Sinónimos",  f"{stats['pct_sinonimos']}% cobertura"),
    (cols[3], "#8b1a35", "EN",  f"{stats['com_ingles']:,}",     "Inglês",          None),
    (cols[4], "#5e3b1a", "ES",  f"{stats['com_espanhol']:,}",   "Espanhol",        None),
]
for col, accent, badge, val, lbl, sub in metrics:
    with col:
        sub_html = f'<div class="metric-sub">{sub}</div>' if sub else ""
        st.markdown(f"""
        <div class="metric-card">
            <div style="
                display:inline-flex; align-items:center; justify-content:center;
                width:28px; height:28px; border-radius:7px;
                background:{accent}18; color:{accent};
                font-size:0.72rem; font-weight:700; letter-spacing:0.03em;
                margin-bottom:4px;
            ">{badge}</div>
            <div class="metric-number">{val}</div>
            <div class="metric-label">{lbl}</div>
            {sub_html}
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

def section_lbl(txt):
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:12px; margin:24px 0 16px;">
        <span style="font-size:0.68rem; font-weight:600; letter-spacing:0.1em;
            text-transform:uppercase; color:#9aaa9c; white-space:nowrap;">{txt}</span>
        <div style="flex:1; height:1px; background:#e8e3da;"></div>
    </div>
    """, unsafe_allow_html=True)

# ── Top Categorias + Cobertura ────────────────────────────────────────────────
section_lbl("Distribuição por categoria")
col_left, col_right = st.columns([3, 2])

with col_left:
    cats, counts = zip(*stats["top_categorias"]) if stats["top_categorias"] else ([], [])

    fig = go.Figure(go.Bar(
        x=list(counts),
        y=list(cats),
        orientation="h",
        marker=dict(
            color=list(counts),
            colorscale=FOREST_SCALE,
            showscale=False,
            line=dict(width=0),
        ),
        hovertemplate="<b>%{y}</b><br>%{x} termos<extra></extra>",
    ))
    fig.update_layout(
        **PLOT_LAYOUT,
        height=420,
        xaxis=dict(
            gridcolor="#f0ece4",
            tickfont=dict(size=10),
            zeroline=False,
        ),
        yaxis=dict(
            gridcolor="rgba(0,0,0,0)",
            tickfont=dict(size=11, color="#4a5c4e"),
            automargin=True,
        ),
        bargap=0.35,
    )
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    section_lbl("Cobertura dos campos")

    fields = ["Definição", "Sinónimos", "Categoria", "Inglês", "Espanhol"]
    values = [
        stats["pct_definicao"],
        stats["pct_sinonimos"],
        round(stats["com_categoria"] / stats["total"] * 100, 1),
        round(stats["com_ingles"]    / stats["total"] * 100, 1),
        round(stats["com_espanhol"]  / stats["total"] * 100, 1),
    ]

    fig2 = go.Figure()
    for f, v, c in zip(fields, values, MULTI_COLORS):
        fig2.add_trace(go.Bar(
            x=[v], y=[f], orientation="h",
            marker=dict(color=c, line=dict(width=0)),
            showlegend=False,
            hovertemplate=f"<b>{f}</b>: {v}%<extra></extra>",
        ))
    fig2.update_layout(
        **PLOT_LAYOUT,
        height=260,
        xaxis=dict(
            range=[0, 118], ticksuffix="%",
            gridcolor="#f0ece4",
            tickfont=dict(size=10),
            zeroline=False,
        ),
        yaxis=dict(
            gridcolor="rgba(0,0,0,0)",
            tickfont=dict(size=11, color="#4a5c4e"),
        ),
        bargap=0.4,
    )
    for f, v in zip(fields, values):
        fig2.add_annotation(
            x=v + 2, y=f, text=f"{v}%",
            showarrow=False, xanchor="left",
            font=dict(size=10, color="#9aaa9c"),
        )
    st.plotly_chart(fig2, use_container_width=True)

    # ── Donut línguas ──────────────────────────────────────────────────────────
    section_lbl("Línguas disponíveis")

    data_raw = get_data()
    lang_counts = {}
    for e in data_raw.values():
        for lang, vals in e.get("traducoes", {}).items():
            if vals:
                k = {"pt": "Português", "en": "Inglês", "es": "Espanhol"}.get(lang, lang)
                lang_counts[k] = lang_counts.get(k, 0) + 1

    fig3 = go.Figure(go.Pie(
        labels=list(lang_counts.keys()),
        values=list(lang_counts.values()),
        hole=0.68,
        marker=dict(
            colors=["#4a7c5e", "#81b894", "#c8e6c9"],
            line=dict(color="#f7f5f0", width=3),
        ),
        textinfo="label+percent",
        textfont=dict(size=11, color="#7a8c7c"),
        hovertemplate="<b>%{label}</b><br>%{value:,} termos (%{percent})<extra></extra>",
    ))
    fig3.update_layout(
        **PLOT_LAYOUT,
        height=210,
        showlegend=False,
    )
    st.plotly_chart(fig3, use_container_width=True)

# ── Barras por fonte ──────────────────────────────────────────────────────────
section_lbl("Distribuição por fonte")

data_raw = get_data()
src_counts: dict[str, int] = {}
for e in data_raw.values():
    for s in e.get("fontes", []):
        src = s.split("/")[0].replace("_", " ").title()
        src_counts[src] = src_counts.get(src, 0) + 1

df_src = pd.DataFrame(
    sorted(src_counts.items(), key=lambda x: x[1]),
    columns=["Fonte", "Termos"]
)

fig4 = go.Figure(go.Bar(
    x=df_src["Termos"],
    y=df_src["Fonte"],
    orientation="h",
    marker=dict(
        color=df_src["Termos"],
        colorscale=FOREST_SCALE,
        showscale=False,
        line=dict(width=0),
    ),
    text=df_src["Termos"].apply(lambda v: f"{v:,}"),
    textposition="outside",
    textfont=dict(size=11, color="#7a8c7c"),
    hovertemplate="<b>%{y}</b><br>%{x:,} termos<extra></extra>",
))
fig4.update_layout(
    **PLOT_LAYOUT,
    height=320,
    xaxis=dict(
        gridcolor="#f0ece4",
        tickfont=dict(size=10),
        zeroline=False,
    ),
    yaxis=dict(
        gridcolor="rgba(0,0,0,0)",
        tickfont=dict(size=11, color="#4a5c4e"),
        automargin=True,
    ),
    bargap=0.3,
)
st.plotly_chart(fig4, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:40px; padding-top:18px; border-top:1px solid #e8e3da;
    display:flex; align-items:center; justify-content:space-between;">
    <span style="font-size:0.7rem; color:#c5d0c7; letter-spacing:0.06em; text-transform:uppercase;">
        MedLex Explorer · PLN 2025/2026
    </span>
    <span style="font-size:0.7rem; color:#c5d0c7;">Dashboard v2.0</span>
</div>
""", unsafe_allow_html=True)