"""
Página de IR + QA — placeholder. Será implementada na Fase 3 e 4.
"""

import streamlit as st

st.markdown("""
<h1 style="font-size:2rem; margin-bottom:4px;">🤖 Pesquisa de Artigos + QA</h1>
<p style="color:rgba(255,255,255,0.5); margin-bottom:24px;">
    Information Retrieval e Question Answering — em breve!
</p>
""", unsafe_allow_html=True)

st.markdown("""
<div class="glass-card" style="text-align:center; padding:60px 40px;">
    <div style="font-size:4rem; margin-bottom:16px;">🚧</div>
    <h2>Em Construção</h2>
    <p>Esta secção será implementada nas Fases 3 e 4.<br>
    O motor de IR (TF-IDF/SBERT) e o modelo BERT de QA serão integrados aqui.</p>
</div>
""", unsafe_allow_html=True)

# Capturar query vinda da página de pesquisa
if "ir_query" in st.session_state:
    st.info(f"🔍 Query recebida da Pesquisa: **{st.session_state['ir_query']}**")
