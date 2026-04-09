import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection # NOWOŚĆ: Import modułu GSheets

st.set_page_config(page_title="SQM | System Logistyczny", page_icon="🚛", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp { background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI', sans-serif; }
    h1, h2, h3 { color: #38bdf8 !important; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    div[data-testid="metric-container"] { background-color: #1e293b !important; border-left: 5px solid #38bdf8 !important; border-radius: 8px !important; padding: 15px !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important; }
    div[data-testid="metric-container"] label { color: #94a3b8 !important; font-size: 1.1rem !important; }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #ffffff !important; font-weight: bold !important; }
    div.stButton > button:first-child { background-color: #0284c7; color: white; border: none; border-radius: 6px; font-weight: bold; transition: all 0.2s; height: 50px; }
    div.stButton > button:first-child:hover { background-color: #38bdf8; color: #0f172a; }
    section[data-testid="stSidebar"] { background-color: #1e293b !important; }
    section[data-testid="stSidebar"] label { color: #f8fafc !important; font-weight: 600 !important; }
    span[data-baseweb="tag"] { background-color: #0284c7 !important; color: white !important; border-radius: 4px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. POŁĄCZENIE Z GOOGLE SHEETS
# ==========================================
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = 'menu' 

# Nawiązanie połączenia z Arkuszem
conn = st.connection("gsheets", type=GSheetsConnection)

wymagane_kolumny = ['Event', 'Naczepa', 'Rząd', 'Układ', 'Projekt_1', 'Zawartosc_1', 'Projekt_2', 'Zawartosc_2', 'Uwagi']

# Zamiast pustej bazy, POBIERAMY DANE Z GOOGLE SHEETS!
if 'cargo_db' not in st.session_state:
    try:
        # Pobieranie danych z zakładki "ZALADUNEK", ttl=0 oznacza brak cache (zawsze świeże dane)
        df_sheet = conn.read(worksheet="ZALADUNEK", ttl=0)
        df_sheet = df_sheet.dropna(how='all') # Usuwa puste wiersze
        
        # Jeśli arkusz jest zupełnie pusty, tworzymy szkielet
        if df_sheet.empty:
            st.session_state.cargo_db = pd.DataFrame(columns=wymagane_kolumny)
        else:
            st.session_state.cargo_db = df_sheet
    except Exception as e:
        st.error(f"Błąd połączenia z Google Sheets: Sprawdź zakładkę ZALADUNEK i uprawnienia. ({e})")
        st.session_state.cargo_db = pd.DataFrame(columns=wymagane_kolumny)

# BAZY LOGISTYKA (Słowniki na ten moment zostawiamy w pamięci, ale docelowo też mogą być osobnymi zakładkami w GSheets)
if 'events_list' not in st.session_state: st.session_state.events_list = ["Hannover Messe 2026", "ISE Barcelona 2026"]
if 'fleet_list' not in st.session_state: st.session_state.fleet_list = ["PO 1234A (Mega)", "WA 9876C (Standard)", "KR 5555X (Standard)"]
if 'projects_db' not in st.session_state:
    st.session_state.projects_db = pd.DataFrame([
        {"Event": "Hannover Messe 2026", "ID": "21374", "Nazwa": "Hannover Główny", "Kolor": "#0ea5e9"},
        {"Event": "Hannover Messe 2026", "ID": "21375", "Nazwa": "Stoisko BMW", "Kolor": "#f59e0b"},
        {"Event": "ISE Barcelona 2026", "ID": "24001", "Nazwa": "Samsung", "Kolor": "#ef4444"}
    ])

uklady_lista = ["🟩 Pełny rząd (1 Projekt)", "🔲 Podzielony: Lewa / Prawa", "🟰 Piętrowany: Dół / Góra"]
kategorie_sprzetu = ["Dioda", "Kablarki", "TV", "Procesory", "Rozdzielnie", "Monitory", "Głośniki", "Wzmacniacze", "Lampy", "Krata", "Drabiny", "Rusztowanie", "Szary plastik. Box", "Niebieski Plastik box", "Kartony", "Statywy", "LAN", "Narzędziówka", "PC", "Gravity", "Paleta", "TRAP"]

def get_project_color(project_string):
    if project_string in ["Brak", "MIX - Drobnica"]: return "#64748b"
    proj_id = project_string.split(" - ")[0]
    match = st.session_state.projects_db[st.session_state.projects_db['ID'] == proj_id]
    if not match.empty: return match.iloc[0]['Kolor']
    return "#64748b"

def sync_to_google_sheets():
    """Funkcja zapisująca aktualny stan do Google Sheets"""
    try:
        conn.update(worksheet="ZALADUNEK", data=st.session_state.cargo_db)
    except Exception as e:
        st.error(f"Nie udało się zapisać w Google Sheets: {e}")

# ==========================================
# 3. SILNIK RENDEROWANIA 3D (Bez zmian)
# ==========================================
def render_3d_trailer(df_current_auto):
    fig3d = go.Figure()
    W, L, H = 2.45, 13.6, 2.7
    ROW_L = L / 15
    fig3d.add_trace(go.Mesh3d(x=[0, W, W, 0], y=[0, 0, L, L], z=[0, 0, 0, 0], i=[0, 0], j=[1, 2], k=[2, 3], color='#334155', opacity=1.0, hoverinfo='skip'))
    fig3d.add_trace(go.Scatter3d(x=[0, W, W, 0, 0, 0, W, W, 0, 0], y=[0, 0, L, L, 0, 0, 0, L, L, 0], z=[0, 0, 0, 0, 0, H, H, H, H, H], mode='lines', line=dict(color='#7dd3fc', width=4), hoverinfo='skip'))

    def draw_block(fig, x_range, y_range, z_range, color, hover_text, label_text):
        x, y, z = [x_range[0], x_range[0], x_range[1], x_range[1], x_range[0], x_range[0], x_range[1], x_range[1]], [y_range[0], y_range[1], y_range[1], y_range[0], y_range[0], y_range[1], y_range[1], y_range[0]], [z_range[0], z_range[0], z_range[0], z_range[0], z_range[1], z_range[1], z_range[1], z_range[1]]
        i, j, k = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
        fig.add_trace(go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color=color, opacity=1.0, hoverinfo='text', text=hover_text, flatshading=True, lighting=dict(ambient=0.8, diffuse=0.9, roughness=0.5, specular=0.2)))
        x_center, y_center, z_center = (x_range[0] + x_range[1]) / 2, (y_range[0] + y_range[1]) / 2, z_range[1] + 0.1
        fig.add_trace(go.Scatter3d(x=[x_center], y=[y_center], z=[z_center], mode='text', text=[label_text], textfont=dict(color='white', size=11, family="Arial"), textposition='middle center', hoverinfo='skip', showlegend=False))

    def format_zawartosc_3d(zaw):
        if zaw == "Nie określono" or not zaw: return ""
        items = zaw.split(", ")
        return f"📦 {items[0]}, {items[1]}..." if len(items) > 2 else f"📦 {zaw}"

    for idx, row in df_current_auto.iterrows():
        y_start, y_end = (row['Rząd'] - 1) * ROW_L, row['Rząd'] * ROW_L - 0.05 
        p1, p2, z1, z2 = row['Projekt_1'], row['Projekt_2'], row['Zawartosc_1'], row['Zawartosc_2']
        c1, c2 = get_project_color(p1), get_project_color(p2)
        nazwa_p1 = p1.split(" - ")[-1] if " - " in p1 else p1
        nazwa_p2 = p2.split(" - ")[-1] if " - " in p2 else p2
        hover_base = f"<b>RZĄD {row['Rząd']}</b><br>Układ: {row['Układ']}<br>Uwagi: {row['Uwagi']}"
        h_info_1, h_info_2 = f"Projekt: {p1}<br>Sprzęt: {z1}", f"Projekt: {p2}<br>Sprzęt: {z2}"
        lab_1, lab_2 = f"<b>{nazwa_p1}</b><br>{format_zawartosc_3d(z1)}", f"<b>{nazwa_p2}</b><br>{format_zawartosc_3d(z2)}"

        if "Pełny" in row['Układ']: draw_block(fig3d, [0.05, W-0.05], [y_start, y_end], [0, H*0.8], c1, f"{hover_base}<br>{h_info_1}", lab_1)
        elif "Lewa / Prawa" in row['Układ']:
            draw_block(fig3d, [0.05, W/2-0.05], [y_start, y_end], [0, H*0.8], c1, f"{hover_base}<br>[LEWA] {h_info_1}", lab_1)
            if p2 != "Brak": draw_block(fig3d, [W/2+0.05, W-0.05], [y_start, y_end], [0, H*0.8], c2, f"{hover_base}<br>[PRAWA] {h_info_2}", lab_2)
        elif "Dół / Góra" in row['Układ']:
            draw_block(fig3d, [0.05, W-0.05], [y_start, y_end], [0, H*0.4], c1, f"{hover_base}<br>[DÓŁ] {h_info_1}", lab_1)
            if p2 != "Brak": draw_block(fig3d, [0.05, W-0.05], [y_start, y_end], [H*0.4+0.05, H*0.8], c2, f"{hover_base}<br>[GÓRA] {h_info_2}", lab_2)

    fig3d.update_layout(scene=dict(aspectmode='data', xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False), camera=dict(eye=dict(x=-2.5, y=-1.8, z=1.5))), margin=dict(l=0, r=0, t=0, b=0), height=700, showlegend=False, paper_bgcolor='rgba(0,0,0,0)')
    return fig3d

# ==========================================
# 4. WIDOK: MENU GŁÓWNE
# ==========================================
if st.session_state.app_mode == 'menu':
    st.markdown("<h1 style='text-align: center; font-size: 4rem; margin-top: 5vh;'>SQM TERMINAL</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #94a3b8 !important;'>Wybierz profil autoryzacji</h3>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 1])
    with col2:
        if st.button("👨‍💼 BIURO (LOGISTYKA)", use_container_width=True): st.session_state.app_mode = 'admin'; st.rerun()
    with col3:
        if st.button("📦 MAGAZYN (ZAŁADUNEK)", use_container_width=True): st.session_state.app_mode = 'load'; st.rerun()
    with col4:
        if st.button("📥 TARGI (ROZŁADUNEK)", use_container_width=True): st.session_state.app_mode = 'unload'; st.rerun()

# ==========================================
# 5. WIDOK: BIURO / LOGISTYKA
# ==========================================
elif st.session_state.app_mode == 'admin':
    with st.sidebar:
        if st.button("🔙 WRÓĆ DO MENU", use_container_width=True): st.session_state.app_mode = 'menu'; st.rerun()
        st.markdown("---")
        st.info("MODUŁ PLANOWANIA: Słowniki Eventów i Floty.")

    st.title("👨‍💼 PANEL LOGISTYKA")
    tab1, tab2, tab3 = st.tabs(["🎪 Słownik Eventów", "🚛 Słownik Floty", "📂 Baza Projektów"])

    with tab1:
        nowy_event = st.text_input("Dodaj nowy Event:")
        if st.button("➕ Dodaj Event") and nowy_event:
            if nowy_event not in st.session_state.events_list: st.session_state.events_list.append(nowy_event); st.rerun()
        for ev in st.session_state.events_list: st.write(f"- {ev}")

    with tab2:
        nowe_auto = st.text_input("Dodaj Auto:")
        if st.button("➕ Dodaj Auto") and nowe_auto:
            if nowe_auto not in st.session_state.fleet_list: st.session_state.fleet_list.append(nowe_auto); st.rerun()
        for auto in st.session_state.fleet_list: st.write(f"- {auto}")

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
            st.session_state.projects_db = edited_projects
            st.rerun()

# ==========================================
# 6. WIDOK: MAGAZYN (ZAŁADUNEK) Z GOOGLE SHEETS
# ==========================================
elif st.session_state.app_mode == 'load':
    with st.sidebar:
        if st.button("🔙 WRÓĆ DO MENU", use_container_width=True): st.session_state.app_mode = 'menu'; st.rerun()
        
        st.markdown("---")
        st.markdown("<h3 style='color: white !important;'>📍 KONTEKST</h3>", unsafe_allow_html=True)
        wybrany_event = st.selectbox("Wybierz Event:", st.session_state.events_list)
        wybrana_naczepa = st.selectbox("Wybierz Auto:", st.session_state.fleet_list)
        
        df_projekty_eventu = st.session_state.projects_db[st.session_state.projects_db['Event'] == wybrany_event]
        dynamiczna_lista_projektow = ["Brak", "MIX - Drobnica"] + [f"{row['ID']} - {row['Nazwa']}" for _, row in df_projekty_eventu.iterrows()]
        df_current_auto = st.session_state.cargo_db[(st.session_state.cargo_db['Event'] == wybrany_event) & (st.session_state.cargo_db['Naczepa'] == wybrana_naczepa)]
        
        st.markdown("---")
        st.markdown("<h3 style='color: white !important;'>⚡ KREATOR RZĘDU</h3>", unsafe_allow_html=True)
        with st.form("add_row_form", clear_on_submit=True):
            rzad = st.number_input("Rząd (od kabiny):", min_value=1, max_value=15, value=len(df_current_auto)+1)
            uklad = st.selectbox("Szablon Układu:", uklady_lista)
            p1 = st.selectbox("Projekt Główny / Lewy / Dół:", dynamiczna_lista_projektow)
            zaw1 = st.multiselect("📦 Sprzęt (P1):", kategorie_sprzetu)
            
            if "Pełny" not in uklad:
                p2 = st.selectbox("Projekt Dodatkowy / Prawy / Góra:", dynamiczna_lista_projektow)
                zaw2 = st.multiselect("📦 Sprzęt (P2):", kategorie_sprzetu)
            else:
                p2, zaw2 = "Brak", []

            uwagi = st.text_input("Uwagi:", placeholder="np. Wózek z boku")
            
            if st.form_submit_button("🔽 DODAJ DO NACZEPY", use_container_width=True):
                z1_text = ", ".join(zaw1) if zaw1 else "Nie określono"
                z2_text = ", ".join(zaw2) if zaw2 else "Nie określono"
                nowe_dane = pd.DataFrame([{'Event': wybrany_event, 'Naczepa': wybrana_naczepa, 'Rząd': rzad, 'Układ': uklad, 'Projekt_1': p1, 'Zawartosc_1': z1_text, 'Projekt_2': p2, 'Zawartosc_2': z2_text, 'Uwagi': uwagi}])
                
                # Zapis lokalny i WYSYŁKA DO GOOGLE SHEETS
                st.session_state.cargo_db = pd.concat([st.session_state.cargo_db, nowe_dane], ignore_index=True)
                sync_to_google_sheets()
                st.rerun()

        if not df_current_auto.empty:
            if st.button("↩️ COFNIJ OSTATNI RZĄD", use_container_width=True):
                st.session_state.cargo_db = st.session_state.cargo_db.drop(df_current_auto.index[-1])
                sync_to_google_sheets() # Aktualizacja Google po cofnięciu
                st.rerun()

    st.title(f"📦 ZAŁADUNEK | {wybrana_naczepa}")
    c1, c2, c3 = st.columns(3)
    zajete = len(df_current_auto['Rząd'].unique())
    c1.metric("Przestrzeń LDM", f"{zajete} / 15")
    c2.metric("Ostatni dodany rząd", f"Rząd {zajete}" if zajete > 0 else "Brak")
    
    # Przycisk pobierania na żywo z chmury
    if c3.button("🔄 POBIERZ ŚWIEŻE DANE Z CHMURY"):
        del st.session_state.cargo_db
        st.rerun()
        
    st.plotly_chart(render_3d_trailer(df_current_auto), use_container_width=True)

    with st.expander("🛠️ TRYB KOREKTY"):
        edited_df = st.data_editor(df_current_auto.drop(columns=['Event', 'Naczepa']), num_rows="dynamic", use_container_width=True)
        if st.button("💾 ZAPISZ KOREKTĘ W GOOGLE SHEETS", type="primary"):
            edited_df['Event'], edited_df['Naczepa'] = wybrany_event, wybrana_naczepa
            mask = ~((st.session_state.cargo_db['Event'] == wybrany_event) & (st.session_state.cargo_db['Naczepa'] == wybrana_naczepa))
            st.session_state.cargo_db = st.session_state.cargo_db[mask]
            st.session_state.cargo_db = pd.concat([st.session_state.cargo_db, edited_df], ignore_index=True)
            sync_to_google_sheets()
            st.success("Baza uaktualniona!")
            st.rerun()

# ==========================================
# 7. WIDOK: TARGI (ROZŁADUNEK)
# ==========================================
elif st.session_state.app_mode == 'unload':
    with st.sidebar:
        if st.button("🔙 WRÓĆ DO MENU", use_container_width=True): st.session_state.app_mode = 'menu'; st.rerun()
        st.markdown("---")
        wybrany_event = st.selectbox("Gdzie jesteś?:", st.session_state.events_list)
        wybrana_naczepa = st.selectbox("Które auto rozładowujesz?:", st.session_state.fleet_list)
        st.info("Tryb Read-Only.")

    df_current_auto = st.session_state.cargo_db[(st.session_state.cargo_db['Event'] == wybrany_event) & (st.session_state.cargo_db['Naczepa'] == wybrana_naczepa)]
    st.title(f"📥 ROZŁADUNEK | {wybrana_naczepa}")
    
    # Przycisk pobierania na żywo z chmury (ważne dla ekipy rozładunkowej)
    if st.button("🔄 POBIERZ ŚWIEŻE DANE Z CHMURY", use_container_width=True):
        del st.session_state.cargo_db
        st.rerun()
        
    st.plotly_chart(render_3d_trailer(df_current_auto), use_container_width=True)
    st.markdown("### 📋 MANIFEST ROZŁADUNKOWY (LIFO)")
    if not df_current_auto.empty:
        kolumny_do_tabeli = ['Rząd', 'Układ', 'Projekt_1', 'Zawartosc_1', 'Projekt_2', 'Zawartosc_2', 'Uwagi']
        df_rozladunek = df_current_auto[kolumny_do_tabeli].sort_values(by='Rząd', ascending=False).reset_index(drop=True)
        st.dataframe(df_rozladunek, use_container_width=True, hide_index=True)
