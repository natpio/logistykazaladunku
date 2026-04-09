import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
import random

# ==========================================
# 1. KONFIGURACJA I STYLE
# ==========================================
st.set_page_config(page_title="SQM LOGISTICS PRO", page_icon="🚛", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp { background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI', sans-serif; }
    h1, h2, h3 { color: #38bdf8 !important; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    
    div[data-testid="stMetricValue"] > div { color: #ffffff !important; font-size: 2.2rem !important; font-weight: bold !important; }
    div[data-testid="stMetricLabel"] p { color: #94a3b8 !important; font-size: 1.1rem !important; }
    
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
    
    div[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
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

PALETA_KOLOROW = ["#ef4444", "#f97316", "#f59e0b", "#84cc16", "#22c55e", "#10b981", 
                  "#06b6d4", "#0ea5e9", "#3b82f6", "#6366f1", "#8b5cf6", "#d946ef", "#f43f5e"]

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
    except Exception as e:
        st.error(f"Błąd połączenia z Google Sheets: {e}")
        st.session_state.cargo_db = pd.DataFrame(columns=WYMAGANE_KOLUMNY)

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
                        proj_val = row['Projekt_1'] if z_col == 'Zawartosc_1' else row['Projekt_2']
                        summary.append({"Projekt": proj_val, "Sprzęt": name.strip(), "Ilość": int(qty.strip())})
    if summary: return pd.DataFrame(summary).groupby(["Projekt", "Sprzęt"])["Ilość"].sum().reset_index()
    return pd.DataFrame(columns=["Projekt", "Sprzęt", "Ilość"])

# ==========================================
# 4. SILNIK 3D
# ==========================================
def draw_3d(df_auto):
    fig = go.Figure()
    W, L, H = 2.45, 13.6, 2.7
    ROW_L = L / 15
    fig.add_trace(go.Mesh3d(x=[0,W,W,0], y=[0,0,L,L], z=[0,0,0,0], i=[0,0], j=[1,2], k=[2,3], color='#334155', opacity=1.0, hoverinfo='skip'))
    fig.add_trace(go.Scatter3d(x=[0,W,W,0,0,0,W,W,0,0], y=[0,0,L,L,0,0,0,L,L,0], z=[0,0,0,0,0,H,H,H,H,H], mode='lines', line=dict(color='#7dd3fc', width=4), hoverinfo='skip'))

    for _, row in df_auto.iterrows():
        y_s, y_e = (row['Rząd'] - 1) * ROW_L, row['Rząd'] * ROW_L - 0.05
        def add_box(xr, yr, zr, color, txt, lbl):
            fig.add_trace(go.Mesh3d(x=[xr[0],xr[0],xr[1],xr[1],xr[0],xr[0],xr[1],xr[1]], y=[yr[0],yr[1],yr[1],yr[0],yr[0],yr[1],yr[1],yr[0]], z=[zr[0],zr[0],zr[0],zr[0],zr[1],zr[1],zr[1],zr[1]], i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6], color=color, flatshading=True, hoverinfo='text', text=txt))
            fig.add_trace(go.Scatter3d(x=[(xr[0]+xr[1])/2], y=[(yr[0]+yr[1])/2], z=[zr[1]+0.1], mode='text', text=[lbl], textfont=dict(color='white', size=11), hoverinfo='skip'))

        c1 = get_proj_color(row['Projekt_1'])
        n1 = str(row['Projekt_1']).split(" - ")[-1]
        
        if "Pełny" in row['Układ']:
            add_box([0.05, W-0.05], [y_s, y_e], [0, H*0.8], c1, f"{row['Projekt_1']}<br>{row['Zawartosc_1']}", n1)
        elif "Lewa / Prawa" in row['Układ']:
            add_box([0.05, W/2-0.05], [y_s, y_e], [0, H*0.8], c1, f"L: {n1}", n1)
            if row['Projekt_2'] != "Brak": add_box([W/2+0.05, W-0.05], [y_s, y_e], [0, H*0.8], get_proj_color(row['Projekt_2']), f"P: {row['Projekt_2']}", str(row['Projekt_2']).split(" - ")[-1])
        elif "Dół / Góra" in row['Układ']:
            add_box([0.05, W-0.05], [y_s, y_e], [0, H*0.4], c1, f"Dół: {n1}", n1)
            if row['Projekt_2'] != "Brak": add_box([0.05, W-0.05], [y_s, y_e], [H*0.4+0.05, H*0.8], get_proj_color(row['Projekt_2']), f"Góra: {row['Projekt_2']}", str(row['Projekt_2']).split(" - ")[-1])

    fig.update_layout(scene=dict(aspectmode='data', xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False), camera=dict(eye=dict(x=-2.5, y=-1.8, z=1.5))), margin=dict(l=0,r=0,t=0,b=0), height=700, showlegend=False, paper_bgcolor='rgba(0,0,0,0)')
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
        if st.button("Dodaj") and ev: 
            if ev not in st.session_state.events_list:
                st.session_state.events_list.append(ev)
                st.rerun()
        for ev in st.session_state.events_list:
            cols = st.columns([4, 1])
            cols[0].write(f"- {ev}")
            if cols[1].button("Usuń", key=f"del_ev_{ev}"):
                st.session_state.events_list.remove(ev)
                st.rerun()
                
    with t2:
        st.markdown("### Aktualna Flota")
        st.session_state.fleet_db = st.data_editor(st.session_state.fleet_db, num_rows="dynamic", use_container_width=True, hide_index=True)
        
    with t3:
        with st.form("dodaj_projekt", clear_on_submit=True):
            colA, colB = st.columns(2)
            p_event = colA.selectbox("Przypisz do Eventu:", st.session_state.events_list if st.session_state.events_list else ["Brak"])
            p_id = colB.text_input("ID Projektu (5 cyfr):")
            p_nazwa = st.text_input("Nazwa Projektu:")
            if st.form_submit_button("Zapisz Projekt w Bazie") and p_event != "Brak" and p_id:
                nowy_proj = pd.DataFrame([{"Event": p_event, "ID": p_id, "Nazwa": p_nazwa, "Kolor": random.choice(PALETA_KOLOROW)}])
                st.session_state.projects_db = pd.concat([st.session_state.projects_db, nowy_proj], ignore_index=True)
                st.rerun()
        st.markdown("### Aktualne Projekty")
        st.session_state.projects_db = st.data_editor(st.session_state.projects_db, num_rows="dynamic", use_container_width=True, hide_index=True)

elif st.session_state.app_mode == 'load':
    st.sidebar.button("🔙 POWRÓT", on_click=lambda: st.session_state.update(app_mode='menu'))
    
    if not st.session_state.events_list:
        st.warning("Skonfiguruj biuro (brak eventów).")
        st.stop()
        
    ev_sel = st.sidebar.selectbox("Event:", st.session_state.events_list)
    auta = st.session_state.fleet_db[st.session_state.fleet_db['Event'] == ev_sel]['Auto'].tolist() if not st.session_state.fleet_db.empty else []
    
    if auta:
        auto_sel = st.sidebar.selectbox("Auto:", auta)
        df_c = st.session_state.cargo_db[(st.session_state.cargo_db['Event'] == ev_sel) & (st.session_state.cargo_db['Naczepa'] == auto_sel)]
        
        st.sidebar.markdown("### ⚡ KREATOR RZĘDU")
        rz = st.sidebar.number_input("Rząd (od kabiny):", min_value=1, max_value=15, value=len(df_c)+1)
        uk = st.sidebar.selectbox("Układ:", UKLADY_LISTA)
        
        projs = ["Brak", "MIX - Drobnica"] + [f"{r['ID']} - {r['Nazwa']}" for _, r in st.session_state.projects_db[st.session_state.projects_db['Event']==ev_sel].iterrows()]
        
        st.sidebar.markdown("---")
        p1 = st.sidebar.selectbox("Projekt 1 (Główny / Lewy / Dół):", projs)
        z1_s = st.sidebar.multiselect("Sprzęt 1:", KATEGORIE_SPRZETU)
        z1_qty = {s: st.sidebar.number_input(f"Ilość {s}:", min_value=1, key=f"q1_{s}") for s in z1_s}
        
        p2, z2_qty = "Brak", {}
        if "Pełny" not in uk:
            st.sidebar.markdown("---")
            p2 = st.sidebar.selectbox("Projekt 2 (Dodatkowy / Prawy / Góra):", projs)
            z2_s = st.sidebar.multiselect("Sprzęt 2:", KATEGORIE_SPRZETU)
            z2_qty = {s: st.sidebar.number_input(f"Ilość {s}:", min_value=1, key=f"q2_{s}") for s in z2_s}
            
        st.sidebar.markdown("---")
        uw = st.sidebar.text_input("Uwagi (opcjonalnie):", placeholder="np. Wózek z boku")
        
        if st.sidebar.button("🔽 DODAJ DO NACZEPY", use_container_width=True):
            z1_t = ", ".join([f"{k}: {v}" for k,v in z1_qty.items()]) if z1_qty else "Nie określono"
            z2_t = ", ".join([f"{k}: {v}" for k,v in z2_qty.items()]) if z2_qty else "Nie określono"
            
            row = pd.DataFrame([{'Event':ev_sel,'Naczepa':auto_sel,'Rząd':rz,'Układ':uk,'Projekt_1':p1,'Zawartosc_1':z1_t,'Projekt_2':p2,'Zawartosc_2':z2_t,'Uwagi':uw}])
            st.session_state.cargo_db = pd.concat([st.session_state.cargo_db, row], ignore_index=True)
            sync_db()
            st.rerun()
            
        if not df_c.empty:
            if st.sidebar.button("↩️ COFNIJ OSTATNI RZĄD", use_container_width=True):
                st.session_state.cargo_db = st.session_state.cargo_db.drop(df_c.index[-1])
                sync_db()
                st.rerun()

        st.title(f"📦 ZAŁADUNEK: {auto_sel}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Przestrzeń LDM", f"{len(df_c['Rząd'].unique())} / 15")
        c2.metric("Ostatni rząd", f"Rząd {len(df_c['Rząd'].unique())}" if not df_c.empty else "Brak")
        if c3.button("🔄 POBIERZ Z CHMURY (Odśwież)"): 
            del st.session_state.cargo_db
            st.rerun()
        
        st.plotly_chart(draw_3d(df_c), use_container_width=True)
        
        with st.expander("🛠️ TRYB KOREKTY"):
            edited_df = st.data_editor(df_c.drop(columns=['Event', 'Naczepa']), num_rows="dynamic", use_container_width=True, hide_index=True)
            if st.button("💾 ZAPISZ KOREKTĘ", type="primary"):
                edited_df['Event'] = ev_sel
                edited_df['Naczepa'] = auto_sel
                st.session_state.cargo_db = st.session_state.cargo_db[~((st.session_state.cargo_db['Event'] == ev_sel) & (st.session_state.cargo_db['Naczepa'] == auto_sel))]
                st.session_state.cargo_db = pd.concat([st.session_state.cargo_db, edited_df], ignore_index=True)
                sync_db()
                st.success("Zapisano!")
                st.rerun()
    else: 
        st.title("📦 ZAŁADUNEK")
        st.warning("Brak aut przypisanych do tego eventu. Dodaj je w panelu Biuro.")

elif st.session_state.app_mode == 'unload':
    st.sidebar.button("🔙 POWRÓT", on_click=lambda: st.session_state.update(app_mode='menu'))
    
    if not st.session_state.events_list:
        st.warning("Brak eventów."); st.stop()
        
    ev_sel = st.sidebar.selectbox("Event:", st.session_state.events_list)
    auta = st.session_state.fleet_db[st.session_state.fleet_db['Event'] == ev_sel]['Auto'].tolist() if not st.session_state.fleet_db.empty else []
    
    if auta:
        auto_sel = st.sidebar.selectbox("Auto:", auta)
        if st.sidebar.button("🔄 ODSWIEŻ DANE"): 
            st.session_state.pop('cargo_db', None)
            st.rerun()
            
        df_c = st.session_state.cargo_db[(st.session_state.cargo_db['Event'] == ev_sel) & (st.session_state.cargo_db['Naczepa'] == auto_sel)]
        
        st.title(f"📥 ROZŁADUNEK: {auto_sel}")
        t1, t2, t3 = st.tabs(["Widok 3D", "Manifest LIFO", "Podsumowanie"])
        
        with t1: 
            st.plotly_chart(draw_3d(df_c), use_container_width=True)
            
        with t2: 
            if not df_c.empty:
                st.dataframe(df_c[['Rząd', 'Układ', 'Projekt_1', 'Zawartosc_1', 'Projekt_2', 'Zawartosc_2', 'Uwagi']].sort_values("Rząd", ascending=False), hide_index=True, use_container_width=True)
            else:
                st.info("Naczepa jest pusta.")
                
        with t3: 
            if not df_c.empty:
                st.dataframe(aggregate_equipment(df_c), use_container_width=True, hide_index=True)
            else:
                st.info("Naczepa jest pusta.")
    else: 
        st.title("📥 ROZŁADUNEK")
        st.warning("Brak aut dla tego eventu.")
