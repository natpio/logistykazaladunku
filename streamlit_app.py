import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. KONFIGURACJA I STYLE
# ==========================================
st.set_page_config(page_title="SQM LOGISTICS PRO", page_icon="🚛", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp { background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI', sans-serif; }
    h1, h2, h3 { color: #38bdf8 !important; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    div[data-testid="metric-container"] {
        background-color: #1e293b !important; border-left: 5px solid #38bdf8 !important;
        border-radius: 8px !important; padding: 15px !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important;
    }
    div.stButton > button:first-child { 
        background-color: #0284c7; color: white; border: none; border-radius: 6px; font-weight: bold; transition: all 0.2s; height: 50px; 
    }
    div.stButton > button:first-child:hover { background-color: #38bdf8; color: #0f172a; }
    section[data-testid="stSidebar"] { background-color: #1e293b !important; }
    section[data-testid="stSidebar"] label { color: #f8fafc !important; font-weight: 600 !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. STAŁE I SŁOWNIKI
# ==========================================
KATEGORIE_SPRZETU = [
    "Dioda", "Kablarki", "TV", "Procesory", "Rozdzielnie", "Monitory", "Głośniki", 
    "Wzmacniacze", "Lampy", "Krata", "Drabiny", "Rusztowanie", "Szary plastik. Box", 
    "Niebieski Plastik box", "Kartony", "Statywy", "LAN", "Narzędziówka", "PC", "Gravity", "Paleta", "TRAP"
]

UKLADY_LISTA = ["🟩 Pełny rząd (1 Projekt)", "🔲 Podzielony: Lewa / Prawa", "🟰 Piętrowany: Dół / Góra"]
WYMAGANE_KOLUMNY = ['Event', 'Naczepa', 'Rząd', 'Układ', 'Projekt_1', 'Zawartosc_1', 'Projekt_2', 'Zawartosc_2', 'Uwagi']

# ==========================================
# 3. LOGIKA BAZY DANYCH (GOOGLE SHEETS)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

if 'app_mode' not in st.session_state:
    st.session_state.app_mode = 'menu'

if 'cargo_db' not in st.session_state:
    try:
        df_sheet = conn.read(worksheet="ZALADUNEK", ttl=0)
        df_sheet = df_sheet.dropna(how='all')
        if df_sheet.empty:
            st.session_state.cargo_db = pd.DataFrame(columns=WYMAGANE_KOLUMNY)
        else:
            for kol in WYMAGANE_KOLUMNY:
                if kol not in df_sheet.columns: df_sheet[kol] = "Nie określono"
            st.session_state.cargo_db = df_sheet
    except:
        st.session_state.cargo_db = pd.DataFrame(columns=WYMAGANE_KOLUMNY)

# Słowniki pomocnicze (Biuro)
if 'events_list' not in st.session_state: st.session_state.events_list = ["Hannover Messe 2026", "ISE Barcelona 2026"]
if 'fleet_db' not in st.session_state:
    st.session_state.fleet_db = pd.DataFrame([
        {"Event": "Hannover Messe 2026", "Auto": "PO 1234A (Mega)"},
        {"Event": "ISE Barcelona 2026", "Auto": "KR 5555X (Standard)"}
    ])
if 'projects_db' not in st.session_state:
    st.session_state.projects_db = pd.DataFrame([
        {"Event": "Hannover Messe 2026", "ID": "21374", "Nazwa": "Hannover Główny", "Kolor": "#0ea5e9"}
    ])

def sync_db():
    try: conn.update(worksheet="ZALADUNEK", data=st.session_state.cargo_db)
    except Exception as e: st.error(f"Błąd zapisu: {e}")

def get_proj_color(proj_str):
    if proj_str in ["Brak", "MIX - Drobnica"]: return "#64748b"
    p_id = proj_str.split(" - ")[0]
    match = st.session_state.projects_db[st.session_state.projects_db['ID'] == str(p_id)]
    return match.iloc[0]['Kolor'] if not match.empty else "#64748b"

def aggregate_equipment(df_auto):
    summary = []
    for _, row in df_auto.iterrows():
        for z_col in ['Zawartosc_1', 'Zawartosc_2']:
            val = str(row[z_col])
            if ":" in val:
                for item in val.split(", "):
                    if ": " in item:
                        name, qty = item.split(": ")
                        summary.append({"Sprzęt": name, "Ilość": int(qty)})
    if summary: return pd.DataFrame(summary).groupby("Sprzęt")["Ilość"].sum().reset_index()
    return pd.DataFrame(columns=["Sprzęt", "Ilość"])

# ==========================================
# 4. SILNIK 3D
# ==========================================
def draw_3d(df_auto):
    fig = go.Figure()
    W, L, H = 2.45, 13.6, 2.7
    ROW_L = L / 15
    fig.add_trace(go.Mesh3d(x=[0,W,W,0], y=[0,0,L,L], z=[0,0,0,0], i=[0,0], j=[1,2], k=[2,3], color='#334155', opacity=1.0))
    fig.add_trace(go.Scatter3d(x=[0,W,W,0,0,0,W,W,0,0], y=[0,0,L,L,0,0,0,L,L,0], z=[0,0,0,0,0,H,H,H,H,H], mode='lines', line=dict(color='#7dd3fc', width=4)))

    for _, row in df_auto.iterrows():
        y_s, y_e = (row['Rząd'] - 1) * ROW_L, row['Rząd'] * ROW_L - 0.05
        def add_box(xr, yr, zr, color, txt, lbl):
            fig.add_trace(go.Mesh3d(x=[xr[0],xr[0],xr[1],xr[1],xr[0],xr[0],xr[1],xr[1]], y=[yr[0],yr[1],yr[1],yr[0],yr[0],yr[1],yr[1],yr[0]], z=[zr[0],zr[0],zr[0],zr[0],zr[1],zr[1],zr[1],zr[1]], i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6], color=color, flatshading=True, hoverinfo='text', text=txt))
            fig.add_trace(go.Scatter3d(x=[(xr[0]+xr[1])/2], y=[(yr[0]+yr[1])/2], z=[zr[1]+0.1], mode='text', text=[lbl], textfont=dict(color='white', size=10)))

        c1 = get_proj_color(row['Projekt_1'])
        n1 = str(row['Projekt_1']).split(" - ")[-1]
        if "Pełny" in row['Układ']:
            add_box([0.05, W-0.05], [y_s, y_e], [0, H*0.8], c1, f"{row['Projekt_1']}<br>{row['Zawartosc_1']}", n1)
        elif "Lewa / Prawa" in row['Układ']:
            add_box([0.05, W/2-0.05], [y_s, y_e], [0, H*0.8], c1, f"L: {n1}", n1)
            if row['Projekt_2'] != "Brak": add_box([W/2+0.05, W-0.05], [y_s, y_e], [0, H*0.8], get_proj_color(row['Projekt_2']), f"P: {row['Projekt_2']}", row['Projekt_2'].split(" - ")[-1])
        elif "Dół / Góra" in row['Układ']:
            add_box([0.05, W-0.05], [y_s, y_e], [0, H*0.4], c1, f"Dół: {n1}", n1)
            if row['Projekt_2'] != "Brak": add_box([0.05, W-0.05], [y_s, y_e], [H*0.4+0.05, H*0.8], get_proj_color(row['Projekt_2']), f"Góra: {row['Projekt_2']}", row['Projekt_2'].split(" - ")[-1])

    fig.update_layout(scene=dict(aspectmode='data', xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False), camera=dict(eye=dict(x=-2.5, y=-1.8, z=1.5))), margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)')
    return fig

# ==========================================
# 5. MODUŁY APLIKACJI
# ==========================================
if st.session_state.app_mode == 'menu':
    st.markdown("<h1 style='text-align: center; font-size: 3rem;'>SQM TERMINAL</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("👨‍💼 BIURO", use_container_width=True): st.session_state.app_mode = 'admin'; st.rerun()
    if c2.button("📦 MAGAZYN", use_container_width=True): st.session_state.app_mode = 'load'; st.rerun()
    if c3.button("📥 TARGI", use_container_width=True): st.session_state.app_mode = 'unload'; st.rerun()

elif st.session_state.app_mode == 'admin':
    st.sidebar.button("🔙 POWRÓT", on_click=lambda: st.session_state.update(app_mode='menu'))
    st.title("👨‍💼 PANEL LOGISTYKA")
    t1, t2, t3 = st.tabs(["Eventy", "Flota", "Projekty"])
    with t1:
        ev = st.text_input("Nowy Event:")
        if st.button("Dodaj") and ev: st.session_state.events_list.append(ev); st.rerun()
        st.write(st.session_state.events_list)
    with t2: st.session_state.fleet_db = st.data_editor(st.session_state.fleet_db, num_rows="dynamic", use_container_width=True)
    with t3: st.session_state.projects_db = st.data_editor(st.session_state.projects_db, num_rows="dynamic", use_container_width=True)

elif st.session_state.app_mode == 'load':
    st.sidebar.button("🔙 POWRÓT", on_click=lambda: st.session_state.update(app_mode='menu'))
    ev_sel = st.sidebar.selectbox("Event:", st.session_state.events_list)
    auta = st.session_state.fleet_db[st.session_state.fleet_db['Event'] == ev_sel]['Auto'].tolist()
    if auta:
        auto_sel = st.sidebar.selectbox("Auto:", auta)
        df_c = st.session_state.cargo_db[(st.session_state.cargo_db['Event'] == ev_sel) & (st.session_state.cargo_db['Naczepa'] == auto_sel)]
        with st.sidebar.form("add_form"):
            rz = st.number_input("Rząd:", value=len(df_c)+1)
            uk = st.selectbox("Układ:", UKLADY_LISTA)
            projs = ["Brak", "MIX - Drobnica"] + [f"{r['ID']} - {r['Nazwa']}" for _, r in st.session_state.projects_db[st.session_state.projects_db['Event']==ev_sel].iterrows()]
            p1 = st.selectbox("Projekt 1:", projs)
            z1_s = st.multiselect("Sprzęt 1:", KATEGORIE_SPRZETU)
            z1_qty = {s: st.number_input(f"Ilość {s}:", min_value=1, key=f"q1_{s}") for s in z1_s}
            p2, z2_qty = "Brak", {}
            if "Pełny" not in uk:
                p2 = st.selectbox("Projekt 2:", projs)
                z2_s = st.multiselect("Sprzęt 2:", KATEGORIE_SPRZETU)
                z2_qty = {s: st.number_input(f"Ilość {s}:", min_value=1, key=f"q2_{s}") for s in z2_s}
            uw = st.text_input("Uwagi:")
            if st.form_submit_button("DODAJ"):
                z1_t = ", ".join([f"{k}: {v}" for k,v in z1_qty.items()]); z2_t = ", ".join([f"{k}: {v}" for k,v in z2_qty.items()])
                row = pd.DataFrame([{'Event':ev_sel,'Naczepa':auto_sel,'Rząd':rz,'Układ':uk,'Projekt_1':p1,'Zawartosc_1':z1_t,'Projekt_2':p2,'Zawartosc_2':z2_t,'Uwagi':uw}])
                st.session_state.cargo_db = pd.concat([st.session_state.cargo_db, row], ignore_index=True); sync_db(); st.rerun()
        st.title(f"📦 ZAŁADUNEK: {auto_sel}")
        st.plotly_chart(draw_3d(df_c), use_container_width=True)
    else: st.warning("Brak aut dla tego eventu.")

elif st.session_state.app_mode == 'unload':
    st.sidebar.button("🔙 POWRÓT", on_click=lambda: st.session_state.update(app_mode='menu'))
    ev_sel = st.sidebar.selectbox("Event:", st.session_state.events_list)
    auta = st.session_state.fleet_db[st.session_state.fleet_db['Event'] == ev_sel]['Auto'].tolist()
    if auta:
        auto_sel = st.sidebar.selectbox("Auto:", auta)
        if st.sidebar.button("🔄 ODSWIEŻ"): st.session_state.pop('cargo_db'); st.rerun()
        df_c = st.session_state.cargo_db[(st.session_state.cargo_db['Event'] == ev_sel) & (st.session_state.cargo_db['Naczepa'] == auto_sel)]
        st.title(f"📥 ROZŁADUNEK: {auto_sel}")
        t1, t2, t3 = st.tabs(["Widok 3D", "Manifest LIFO", "Podsumowanie"])
        with t1: st.plotly_chart(draw_3d(df_c), use_container_width=True)
        with t2: st.dataframe(df_c.sort_values("Rząd", ascending=False), hide_index=True)
        with t3: st.dataframe(aggregate_equipment(df_c), use_container_width=True, hide_index=True)
