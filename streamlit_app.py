# streamlit_app.py
import streamlit as st
import pandas as pd
from config import UKLADY_LISTA, KATEGORIE_SPRZETU
from db_manager import init_db, sync_db, aggregate_equipment
from visuals import load_ui, render_3d

# Inicjalizacja systemu
init_db()
load_ui()

# --- ROUTING ---
if st.session_state.app_mode == 'menu':
    st.markdown("<h1 style='text-align: center; font-size: 3rem;'>SQM TERMINAL</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("👨‍💼 BIURO", use_container_width=True): st.session_state.app_mode = 'admin'; st.rerun()
    if c2.button("📦 MAGAZYN", use_container_width=True): st.session_state.app_mode = 'load'; st.rerun()
    if c3.button("📥 TARGI", use_container_width=True): st.session_state.app_mode = 'unload'; st.rerun()

elif st.session_state.app_mode == 'load':
    st.sidebar.button("🔙 MENU", on_click=lambda: st.session_state.update(app_mode='menu'))
    # Logika wybierania eventu i auta...
    ev = st.sidebar.selectbox("Event:", st.session_state.events_list)
    auta = st.session_state.fleet_db[st.session_state.fleet_db['Event'] == ev]['Auto'].tolist()
    
    if auta:
        auto = st.sidebar.selectbox("Auto:", auta)
        df_c = st.session_state.cargo_db[(st.session_state.cargo_db['Event'] == ev) & (st.session_state.cargo_db['Naczepa'] == auto)]
        
        with st.sidebar.form("add_row"):
            rz = st.number_input("Rząd:", value=len(df_c)+1)
            uk = st.selectbox("Układ:", UKLADY_LISTA)
            # Tu wstawiamy multiselect i pola ilości z poprzedniego kroku...
            if st.form_submit_button("DODAJ"):
                # sync_db() wywołujemy po dodaniu wiersza
                sync_db(); st.rerun()
        
        st.plotly_chart(render_3d(df_c), use_container_width=True)
