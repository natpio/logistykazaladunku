# streamlit_app.py
import streamlit as st
import pandas as pd

# Importy z naszych nowych modułów
from config import UKLADY_LISTA, KATEGORIE_SPRZETU
from db_manager import init_db, sync_to_google_sheets, aggregate_equipment
from visuals import load_css, render_3d_trailer

# 1. SETUP STRONY I BAZY
st.set_page_config(page_title="SQM | System Logistyczny", page_icon="🚛", layout="wide", initial_sidebar_state="expanded")
load_css()
init_db()

# 2. MENU GŁÓWNE BRAMKI
if st.session_state.app_mode == 'menu':
    st.markdown("<h1 style='text-align: center; font-size: 4rem; margin-top: 5vh;'>SQM TERMINAL</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #94a3b8 !important;'>Wybierz profil autoryzacji</h3><br>", unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 1])
    with col2:
        if st.button("👨‍💼 BIURO (LOGISTYKA)", use_container_width=True): st.session_state.app_mode = 'admin'; st.rerun()
    with col3:
        if st.button("📦 MAGAZYN (ZAŁADUNEK)", use_container_width=True): st.session_state.app_mode = 'load'; st.rerun()
    with col4:
        if st.button("📥 TARGI (ROZŁADUNEK)", use_container_width=True): st.session_state.app_mode = 'unload'; st.rerun()

# 3. WIDOK: BIURO / LOGISTYKA
elif st.session_state.app_mode == 'admin':
    with st.sidebar:
        if st.button("🔙 WRÓĆ DO MENU", use_container_width=True): st.session_state.app_mode = 'menu'; st.rerun()
        st.info("MODUŁ PLANOWANIA: Zmiany wprowadzane tutaj pojawią się u magazynierów.")

    st.title("👨‍💼 PANEL LOGISTYKA")
    tab1, tab2, tab3 = st.tabs(["🎪 Słownik Eventów", "🚛 Słownik Floty", "📂 Baza Projektów i Kolorów"])

    with tab1:
        nowy_event = st.text_input("Dodaj nowy Event:")
        if st.button("➕ Dodaj Event") and nowy_event not in st.session_state.events_list:
            st.session_state.events_list.append(nowy_event); st.rerun()
        for ev in st.session_state.events_list:
            st.write(f"- {ev}")

    with tab2:
        nowe_auto = st.text_input("Dodaj Auto (Rejestracja):")
        if st.button("➕ Dodaj Auto") and nowe_auto not in st.session_state.fleet_list:
            st.session_state.fleet_list.append(nowe_auto); st.rerun()
        for auto in st.session_state.fleet_list:
            st.write(f"- {auto}")

    with tab3:
        with st.form("dodaj_projekt", clear_on_submit=True):
            colA, colB, colC = st.columns(3)
            p_event = colA.selectbox("Przypisz do Eventu:", st.session_state.events_list)
            p_id = colB.text_input("ID Projektu (5 cyfr):")
            p_nazwa = colC.text_input("Nazwa Projektu:")
            p_kolor = st.color_picker("Wybierz kolor identyfikacyjny w 3D:", "#0ea5e9")
            if st.form_submit_button("💾 Zapisz Projekt w Bazie"):
                nowy_proj = pd.DataFrame([{"Event": p_event, "ID": p_id, "Nazwa": p_nazwa, "Kolor": p_kolor}])
                st.session_state.projects_db = pd.concat([st.session_state.projects_db, nowy_proj], ignore_index=True)
                st.rerun()
        edited_projects = st.data_editor(st.session_state.projects_db, num_rows="dynamic", use_container_width=True)
        if st.button("Aktualizuj Tabelę Projektów"):
            st.session_state.projects_db = edited_projects; st.success("Baza zaktualizowana!"); st.rerun()

# 4. WIDOK: MAGAZYN (ZAŁADUNEK)
elif st.session_state.app_mode == 'load':
    with st.sidebar:
        if st.button("🔙 WRÓĆ DO MENU", use_container_width=True): st.session_state.app_mode = 'menu'; st.rerun()
        st.markdown("---")
        st.markdown("<h3 style='color: white !important;'>📍 KONTEKST</h3>", unsafe_allow_html=True)
        wybrany_event = st.selectbox("Wybierz Event:", st.session_state.events_list)
        wybrana_naczepa = st.selectbox("Wybierz Auto:", st.session_state.fleet_list)
        
        df_projekty = st.session_state.projects_db[st.session_state.projects_db['Event'] == wybrany_event]
        dynamiczna_lista_projektow = ["Brak", "MIX - Drobnica"] + [f"{row['ID']} - {row['Nazwa']}" for _, row in df_projekty.iterrows()]
        df_current_auto = st.session_state.cargo_db[(st.session_state.cargo_db['Event'] == wybrany_event) & (st.session_state.cargo_db['Naczepa'] == wybrana_naczepa)]
        
        st.markdown("---")
        st.markdown("<h3 style='color: white !important;'>⚡ KREATOR RZĘDU</h3>", unsafe_allow_html=True)
        with st.form("add_row_form", clear_on_submit=True):
            rzad = st.number_input("Rząd (od kabiny):", min_value=1, max_value=15, value=len(df_current_auto)+1)
            uklad = st.selectbox("Szablon Układu:", UKLADY_LISTA)
            
            st.markdown("---")
            p1 = st.selectbox("Projekt Główny / Lewy / Dół:", dynamiczna_lista_projektow)
            zaw1 = st.multiselect("📦 Sprzęt (P1):", KATEGORIE_SPRZETU)
            z1_dict = {item: st.number_input(f"{item}", min_value=1, step=1, key=f"q1_{item}") for item in zaw1} if zaw1 else {}
            
            if "Pełny" not in uklad:
                st.markdown("---")
                p2 = st.selectbox("Projekt Dodatkowy / Prawy / Góra:", dynamiczna_lista_projektow)
                zaw2 = st.multiselect("📦 Sprzęt (P2):", KATEGORIE_SPRZETU)
                z2_dict = {item: st.number_input(f"{item}", min_value=1, step=1, key=f"q2_{item}") for item in zaw2} if zaw2 else {}
            else:
                p2, z2_dict = "Brak", {}

            uwagi = st.text_input("Uwagi:", placeholder="np. Wózek z boku")
            if st.form_submit_button("🔽 DODAJ DO NACZEPY", use_container_width=True):
                z1_text = ", ".join([f"{k}: {v}" for k, v in z1_dict.items()]) if z1_dict else "Nie określono"
                z2_text = ", ".join([f"{k}: {v}" for k, v in z2_dict.items()]) if z2_dict else "Nie określono"
                nowe_dane = pd.DataFrame([{'Event': wybrany_event, 'Naczepa': wybrana_naczepa, 'Rząd': rzad, 'Układ': uklad, 'Projekt_1': p1, 'Zawartosc_1': z1_text, 'Projekt_2': p2, 'Zawartosc_2': z2_text, 'Uwagi': uwagi}])
                st.session_state.cargo_db = pd.concat([st.session_state.cargo_db, nowe_dane], ignore_index=True)
                sync_to_google_sheets()
                st.rerun()

        if not df_current_auto.empty:
            if st.button("↩️ COFNIJ OSTATNI RZĄD", use_container_width=True):
                st.session_state.cargo_db = st.session_state.cargo_db.drop(df_current_auto.index[-1])
                sync_to_google_sheets()
                st.rerun()

    st.title(f"📦 ZAŁADUNEK | {wybrana_naczepa}")
    st.plotly_chart(render_3d_trailer(df_current_auto), use_container_width=True)

# 5. WIDOK: TARGI (ROZŁADUNEK)
elif st.session_state.app_mode == 'unload':
    with st.sidebar:
        if st.button("🔙 WRÓĆ DO MENU", use_container_width=True): st.session_state.app_mode = 'menu'; st.rerun()
        st.markdown("---")
        wybrany_event = st.selectbox("Gdzie jesteś?:", st.session_state.events_list)
        wybrana_naczepa = st.selectbox("Które auto rozładowujesz?:", st.session_state.fleet_list)
        st.info("Tryb Read-Only.")

    df_current_auto = st.session_state.cargo_db[(st.session_state.cargo_db['Event'] == wybrany_event) & (st.session_state.cargo_db['Naczepa'] == wybrana_naczepa)]
    st.title(f"📥 ROZŁADUNEK | {wybrana_naczepa}")
    
    col_a, col_b = st.columns([4, 1])
    if col_b.button("🔄 ODCZYTAJ DANE Z CHMURY", use_container_width=True):
        del st.session_state.cargo_db; st.rerun()
        
    tab_3d, tab_manifest, tab_podsumowanie = st.tabs(["🧊 WIZUALIZACJA 3D", "📋 MANIFEST (LIFO)", "📊 PODSUMOWANIE SPRZĘTU"])
    with tab_3d:
        st.plotly_chart(render_3d_trailer(df_current_auto), use_container_width=True)
    with tab_manifest:
        if not df_current_auto.empty:
            df_rozladunek = df_current_auto[['Rząd', 'Układ', 'Projekt_1', 'Zawartosc_1', 'Projekt_2', 'Zawartosc_2', 'Uwagi']].sort_values(by='Rząd', ascending=False).reset_index(drop=True)
            st.dataframe(df_rozladunek, use_container_width=True, hide_index=True)
    with tab_podsumowanie:
        if not df_current_auto.empty:
            st.dataframe(aggregate_equipment(df_current_auto), use_container_width=True, hide_index=True)
