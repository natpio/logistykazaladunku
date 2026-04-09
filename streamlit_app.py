# streamlit_app.py
import streamlit as st
import pandas as pd
from config import UKLADY_LISTA, KATEGORIE_SPRZETU
from db_manager import init_db, sync_db, aggregate_equipment
from visuals import load_ui, draw_3d

init_db()
load_ui()

# --- MENU GŁÓWNE ---
if st.session_state.app_mode == 'menu':
    st.markdown("<h1 style='text-align: center; font-size: 3rem;'>SQM LOGISTICS TERMINAL</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("👨‍💼 BIURO", use_container_width=True): st.session_state.app_mode = 'admin'; st.rerun()
    if c2.button("📦 MAGAZYN", use_container_width=True): st.session_state.app_mode = 'load'; st.rerun()
    if c3.button("📥 TARGI", use_container_width=True): st.session_state.app_mode = 'unload'; st.rerun()

# --- MODUŁ BIURO ---
elif st.session_state.app_mode == 'admin':
    st.sidebar.button("🔙 POWRÓT", on_click=lambda: st.session_state.update(app_mode='menu'))
    st.title("👨‍💼 PANEL LOGISTYKA")
    t1, t2, t3 = st.tabs(["Eventy", "Flota", "Projekty"])
    with t1:
        ev = st.text_input("Nowy Event:")
        if st.button("Dodaj") and ev: st.session_state.events_list.append(ev); st.rerun()
        st.write(st.session_state.events_list)
    with t2:
        st.session_state.fleet_db = st.data_editor(st.session_state.fleet_db, num_rows="dynamic", use_container_width=True)
    with t3:
        st.session_state.projects_db = st.data_editor(st.session_state.projects_db, num_rows="dynamic", use_container_width=True)

# --- MODUŁ MAGAZYN ---
elif st.session_state.app_mode == 'load':
    st.sidebar.button("🔙 POWRÓĆ", on_click=lambda: st.session_state.update(app_mode='menu'))
    ev = st.sidebar.selectbox("Event:", st.session_state.events_list)
    auta = st.session_state.fleet_db[st.session_state.fleet_db['Event'] == ev]['Auto'].tolist()
    if auta:
        auto = st.sidebar.selectbox("Auto:", auta)
        df_c = st.session_state.cargo_db[(st.session_state.cargo_db['Event'] == ev) & (st.session_state.cargo_db['Naczepa'] == auto)]
        
        with st.sidebar.form("add"):
            st.write("### DODAJ RZĄD")
            rz = st.number_input("Rząd:", value=len(df_c)+1)
            uk = st.selectbox("Układ:", UKLADY_LISTA)
            
            # Projekt 1 i Sprzęt
            projs = ["Brak", "MIX - Drobnica"] + [f"{r['ID']} - {r['Nazwa']}" for _, r in st.session_state.projects_db[st.session_state.projects_db['Event']==ev].iterrows()]
            p1 = st.selectbox("Projekt 1:", projs)
            z1_s = st.multiselect("Sprzęt 1:", KATEGORIE_SPRZETU)
            z1_d = {s: st.number_input(f"Ilość {s}:", min_value=1, key=f"z1{s}") for s in z1_s}
            
            p2, z2_d = "Brak", {}
            if "Pełny" not in uk:
                p2 = st.selectbox("Projekt 2:", projs)
                z2_s = st.multiselect("Sprzęt 2:", KATEGORIE_SPRZETU)
                z2_d = {s: st.number_input(f"Ilość {s}:", min_value=1, key=f"z2{s}") for s in z2_s}
            
            uw = st.text_input("Uwagi:")
            if st.form_submit_button("DODAJ"):
                z1_t = ", ".join([f"{k}: {v}" for k,v in z1_d.items()])
                z2_t = ", ".join([f"{k}: {v}" for k,v in z2_d.items()])
                row = pd.DataFrame([{'Event':ev, 'Naczepa':auto, 'Rząd':rz, 'Układ':uk, 'Projekt_1':p1, 'Zawartosc_1':z1_t, 'Projekt_2':p2, 'Zawartosc_2':z2_t, 'Uwagi':uw}])
                st.session_state.cargo_db = pd.concat([st.session_state.cargo_db, row], ignore_index=True)
                sync_db(); st.rerun()

        st.title(f"📦 ZAŁADUNEK: {auto}")
        st.plotly_chart(draw_3d(df_c), use_container_width=True)
    else: st.warning("Brak aut dla tego eventu.")

# --- MODUŁ TARGI ---
elif st.session_state.app_mode == 'unload':
    st.sidebar.button("🔙 POWRÓT", on_click=lambda: st.session_state.update(app_mode='menu'))
    ev = st.sidebar.selectbox("Event:", st.session_state.events_list)
    auta = st.session_state.fleet_db[st.session_state.fleet_db['Event'] == ev]['Auto'].tolist()
    if auta:
        auto = st.sidebar.selectbox("Auto:", auta)
        if st.sidebar.button("🔄 ODSWIEŻ"): st.session_state.pop('cargo_db'); st.rerun()
        df_c = st.session_state.cargo_db[(st.session_state.cargo_db['Event'] == ev) & (st.session_state.cargo_db['Naczepa'] == auto)]
        st.title(f"📥 ROZŁADUNEK: {auto}")
        t1, t2, t3 = st.tabs(["Widok 3D", "Manifest LIFO", "Podsumowanie"])
        with t1: st.plotly_chart(draw_3d(df_c), use_container_width=True)
        with t2: st.dataframe(df_c.sort_values("Rząd", ascending=False), hide_index=True)
        with t3: st.dataframe(aggregate_equipment(df_c), use_container_width=True, hide_index=True)
