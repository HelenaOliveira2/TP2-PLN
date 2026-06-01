"""
Página de Gestão (CRUD) — adicionar, editar e apagar termos do dicionário.
Todas as alterações são imediatamente persistidas no ficheiro JSON.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from utils.data_manager import get_data, add_term, update_term, delete_term

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:28px 0 24px;">
    <h1 style="font-family:'Lora',serif; font-size:2rem; font-weight:600;
        color:#1a2e1c; margin:0 0 6px; letter-spacing:-0.02em;">Gestão do Dicionário</h1>
    <p style="color:#9aaa9c; font-size:0.85rem; margin:0;">
        Adiciona, edita ou remove termos. Todas as alterações são guardadas automaticamente.
    </p>
</div>
""", unsafe_allow_html=True)

tab_add, tab_edit, tab_delete = st.tabs(["Adicionar Termo", "Editar Termo", "Apagar Termo"])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — ADICIONAR
# ════════════════════════════════════════════════════════════════════════════════
with tab_add:
    st.markdown("### Novo Termo")
    st.markdown("""
    <div class="glass-card">
    """, unsafe_allow_html=True)

    with st.form("form_add", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            new_termo = st.text_input("Termo Principal *", placeholder="ex: Fémur")
            new_genero = st.selectbox("Género", ["", "masculino", "feminino", "neutro"])
            new_cats = st.text_input("Categorias", placeholder="ex: Anatomia Ortopedia (separadas por espaço)")
            new_sinonimos = st.text_input("Sinónimos", placeholder="ex: Osso da coxa (separados por vírgula)")
            new_siglas = st.text_input("Siglas", placeholder="ex: GABA (separadas por vírgula)")

        with col2:
            new_def = st.text_area("Definição", placeholder="Escreve a definição do termo...", height=120)
            new_pt = st.text_input("Tradução PT", placeholder="ex: fémur")
            new_en = st.text_input("Tradução EN", placeholder="ex: femur")
            new_es = st.text_input("Tradução ES", placeholder="ex: fémur")
            new_termos_rel = st.text_input("Termos Relacionados", placeholder="ex: Tíbia, Rótula (separados por vírgula)")

        submitted = st.form_submit_button("💾 Guardar Novo Termo", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        if not new_termo.strip():
            st.error("O campo 'Termo Principal' é obrigatório.")
        else:
            def split_comma(s): return [x.strip() for x in s.split(",") if x.strip()]
            def split_space(s): return [x.strip() for x in s.split() if x.strip()]

            entry = {
                "termo_principal": new_termo.strip(),
                "categorias": split_space(new_cats) if new_cats else [],
                "definicoes": [new_def.strip()] if new_def.strip() else [],
                "sinonimos": split_comma(new_sinonimos) if new_sinonimos else [],
                "siglas": split_comma(new_siglas) if new_siglas else [],
                "termos_relacionados": split_comma(new_termos_rel) if new_termos_rel else [],
                "traducoes": {
                    "pt": [new_pt.strip()] if new_pt.strip() else [],
                    "en": [new_en.strip()] if new_en.strip() else [],
                    "es": [new_es.strip()] if new_es.strip() else [],
                },
                "fontes": ["utilizador"],
            }
            if new_genero:
                entry["genero"] = new_genero

            key = new_termo.strip().lower()
            ok = add_term(key, entry)
            if ok:
                st.success(f"✅ Termo **{new_termo}** adicionado com sucesso!")
            else:
                st.warning(f"⚠️ O termo **{new_termo}** já existe no dicionário. Usa a aba **Editar** para o modificar.")


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — EDITAR
# ════════════════════════════════════════════════════════════════════════════════
with tab_edit:
    st.markdown("### Editar Termo Existente")

    data = get_data()

    # Pré-selecionar se veio da página de Pesquisa
    default_key = st.session_state.get("edit_key", "")

    search_edit = st.text_input(
        "Pesquisar termo para editar",
        value=default_key,
        placeholder="Escreve o nome do termo...",
        key="edit_search",
    )

    if search_edit:
        # Encontrar chaves correspondentes
        matches = [k for k in data if search_edit.lower() in k][:20]

        if not matches:
            st.info("Nenhum termo encontrado.")
        else:
            selected_key = st.selectbox("Seleciona o termo", matches, format_func=lambda k: data[k].get("termo_principal", k))

            if selected_key:
                entry = data[selected_key].copy()
                st.markdown("---")
                st.markdown(f"**A editar:** `{entry.get('termo_principal', selected_key)}`")

                with st.form("form_edit"):
                    col1, col2 = st.columns(2)

                    def list_to_str(lst, sep=", "):
                        return sep.join(lst) if isinstance(lst, list) else str(lst or "")

                    with col1:
                        e_termo = st.text_input("Termo Principal", value=entry.get("termo_principal", ""))
                        e_genero = st.selectbox(
                            "Género",
                            ["", "masculino", "feminino", "neutro"],
                            index=["", "masculino", "feminino", "neutro"].index(entry.get("genero", "")) if entry.get("genero", "") in ["", "masculino", "feminino", "neutro"] else 0
                        )
                        e_cats = st.text_input("Categorias (separadas por espaço)", value=list_to_str(entry.get("categorias", []), " "))
                        e_sinonimos = st.text_input("Sinónimos (sep. por vírgula)", value=list_to_str(entry.get("sinonimos", [])))
                        e_siglas = st.text_input("Siglas (sep. por vírgula)", value=list_to_str(entry.get("siglas", [])))
                        e_termos_rel = st.text_input("Termos Relacionados (sep. por vírgula)", value=list_to_str(entry.get("termos_relacionados", [])))

                    with col2:
                        current_defs = entry.get("definicoes", [])
                        e_def = st.text_area(
                            "Definição",
                            value=current_defs[0] if current_defs else "",
                            height=120,
                        )
                        trad = entry.get("traducoes", {})
                        e_pt = st.text_input("Tradução PT", value=list_to_str(trad.get("pt", [])))
                        e_en = st.text_input("Tradução EN", value=list_to_str(trad.get("en", [])))
                        e_es = st.text_input("Tradução ES", value=list_to_str(trad.get("es", [])))

                    save_edit = st.form_submit_button("💾 Guardar Alterações", use_container_width=True)

                if save_edit:
                    def split_comma(s): return [x.strip() for x in s.split(",") if x.strip()]
                    def split_space(s): return [x.strip() for x in s.split() if x.strip()]

                    entry["termo_principal"] = e_termo.strip()
                    entry["categorias"] = split_space(e_cats)
                    entry["definicoes"] = [e_def.strip()] if e_def.strip() else []
                    entry["sinonimos"] = split_comma(e_sinonimos)
                    entry["siglas"] = split_comma(e_siglas)
                    entry["termos_relacionados"] = split_comma(e_termos_rel)
                    entry["traducoes"] = {
                        "pt": split_comma(e_pt),
                        "en": split_comma(e_en),
                        "es": split_comma(e_es),
                    }
                    if e_genero:
                        entry["genero"] = e_genero

                    update_term(selected_key, entry)
                    # Limpar pré-seleção da sessão
                    if "edit_key" in st.session_state:
                        del st.session_state["edit_key"]
                    st.success(f"✅ Termo **{e_termo}** atualizado e guardado!")
                    st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — APAGAR
# ════════════════════════════════════════════════════════════════════════════════
with tab_delete:
    st.markdown("### Apagar Termo")
    st.warning("⚠️ Esta ação é **permanente** e não pode ser desfeita.")

    data = get_data()

    search_del = st.text_input(
        "Pesquisar termo para apagar",
        placeholder="Escreve o nome do termo...",
        key="delete_search",
    )

    if search_del:
        matches_del = [k for k in data if search_del.lower() in k][:20]

        if not matches_del:
            st.info("Nenhum termo encontrado.")
        else:
            del_key = st.selectbox(
                "Seleciona o termo a apagar",
                matches_del,
                format_func=lambda k: data[k].get("termo_principal", k),
                key="del_select",
            )

            if del_key:
                entry = data[del_key]
                st.markdown(f"""
                <div class="glass-card" style="border-left: 3px solid #ef4444;">
                    <div class="entry-title">{entry.get("termo_principal", del_key)}</div>
                    <div class="entry-meta">
                        {" | ".join(entry.get("categorias", [])[:3])}
                    </div>
                    {"<p>" + entry.get("definicoes", [""])[0][:200] + "…</p>" if entry.get("definicoes") else ""}
                </div>
                """, unsafe_allow_html=True)

                # Confirmação com checkbox
                confirm = st.checkbox(f'Confirmo que quero apagar **"{entry.get("termo_principal", del_key)}"** permanentemente.')

                if confirm:
                    if st.button("🗑️ Apagar Definitivamente", type="primary"):
                        ok = delete_term(del_key)
                        if ok:
                            st.success(f"✅ Termo **{entry.get('termo_principal', del_key)}** apagado com sucesso!")
                            st.rerun()
                        else:
                            st.error("Erro ao apagar o termo.")
