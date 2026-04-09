import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ==========================================
# 1. KONFIGURACJA STRONY I STYLIZACJA PRO
# ==========================================
st.set_page_config(
    page_title="SQM | System Załadunkowy", 
    page_icon="🚛", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp { 
        background-color: #0f172a; 
        color: #f8fafc; 
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; 
    }
    
    h1, h2, h3 { 
        color: #38bdf8 !important; 
        font-weight: 600; 
        text-transform: uppercase; 
        letter-spacing: 1px;
    }
    
    /* KPI */
    div[data-testid="metric-container"] {
        background-color: #1e293b !important; 
        border-left: 5px solid #38bdf8 !important;
        border-radius: 8px !important; 
        padding: 15px !important; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important;
    }
    div[data-testid="metric-container"] label { color: #94a3b8 !important; font-size: 1.1rem !important; }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #ffffff !important; font-weight: bold !important; }
    
    /* Przyciski */
    div.stButton > button:first-child {
        background-color: #0284c7; color: white; border: none; border-radius: 6px; font-weight: bold; transition: all 0.2s;
    }
    div.stButton > button:first-child:hover { background-color: #38bdf8; color: #0f172a; }
    
    /* --- NAPRAWA PANELU BOCZNEGO --- */
    section[data-testid="stSidebar"] { background-color: #1e293b !important; }
    section[data-testid="stSidebar"] label { color: #f8fafc !important; font-weight: 600 !important; }
    section[data-testid="stSidebar"] .stMarkdown p { color: #cbd5e1 !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BAZA DANYCH I SŁOWNIKI
# ==========================================
# GŁÓWNA ZMIANA: Dodajemy z powrotem Event i Naczepę do bazy
if 'cargo_db' not in st.session_state:
    st.session_state.cargo_db = pd.DataFrame(columns=[
        'Event', 'Naczepa', 'Rząd', 'Układ', 'Projekt_1', 'Projekt_2', 'Uwagi'
    ])

eventy_lista = ["Hannover Messe 2026", "ISE Barcelona 2026", "IFA Berlin"]
flota_lista = ["PO 1234A (Mega)", "WA 9876C (Standard)", "KR 5555X (Standard)"]
projekty_lista = ["Brak", "21374 - Hannover", "24001 - Samsung", "24552 - Budimex", "MIX - Drobnica"]
uklady_lista = ["🟩 Pełny rząd (1 Projekt)", "🔲 Podzielony: Lewa / Prawa", "🟰 Piętrowany: Dół / Góra"]

kolory_skrzyn = {
    '21374 - Hannover': '#0ea5e9',
    '24001 - Samsung': '#ef4444', 
    '24552 - Budimex': '#22c55e',  
    'MIX - Drobnica': '#f59e0b'    
}

# ==========================================
# 3. INTERFEJS UŻYTKOWNIKA - SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #38bdf8 !important;'>📍 KONTEKST</h2>", unsafe_allow_html=True)
    wybrany_event = st.selectbox("Wybierz Event:", eventy_lista)
    wybrana_naczepa = st.selectbox("Wybierz Auto:", flota_lista)
    
    st.markdown("---")
    st.markdown("<h2 style='text-align: center; color: #38bdf8 !important;'>⚡ ZAŁADUNEK</h2>", unsafe_allow_html=True)
    
    # Filtrujemy dane TYLKO dla tego konkretnego auta (żeby numerować rzędy poprawnie)
    df_current_auto = st.session_state.cargo_db[
        (st.session_state.cargo_db['Event'] == wybrany_event) & 
        (st.session_state.cargo_db['Naczepa'] == wybrana_naczepa)
    ]
    
    with st.form("add_row_form", clear_on_submit=True):
        rzad = st.number_input("Kolejny Rząd (od kabiny):", min_value=1, max_value=15, value=len(df_current_auto)+1)
        uklad = st.selectbox("Szablon Układu:", uklady_lista)
        
        st.markdown("---")
        p1 = st.selectbox("Projekt Główny (Lewy / Dół):", projekty_lista, index=1)
        p2 = st.selectbox("Projekt Dodatkowy (Prawy / Góra):", projekty_lista, index=0)
        uwagi = st.text_input("Uwagi (opcjonalnie):", placeholder="np. Wózek z boku")
        
        if st.form_submit_button("🔽 UMIEŚĆ W NACZEPIE", use_container_width=True):
            nowe_dane = pd.DataFrame([{
                'Event': wybrany_event,
                'Naczepa': wybrana_naczepa,
                'Rząd': rzad, 
                'Układ': uklad, 
                'Projekt_1': p1, 
                'Projekt_2': p2 if "Pełny" not in uklad else "Brak", 
                'Uwagi': uwagi
            }])
            st.session_state.cargo_db = pd.concat([st.session_state.cargo_db, nowe_dane], ignore_index=True)
            st.rerun()

    if st.button("🗑️ Wyczyść TO auto", use_container_width=True):
        # Usuwamy tylko ładunek dla aktualnie wybranego auta
        mask = ~((st.session_state.cargo_db['Event'] == wybrany_event) & (st.session_state.cargo_db['Naczepa'] == wybrana_naczepa))
        st.session_state.cargo_db = st.session_state.cargo_db[mask]
        st.rerun()

# ==========================================
# 4. GŁÓWNY PANEL (KPI i Nagłówek)
# ==========================================
# Aktualizujemy df_current_auto po ewentualnym dodaniu danych
df_current_auto = st.session_state.cargo_db[
    (st.session_state.cargo_db['Event'] == wybrany_event) & 
    (st.session_state.cargo_db['Naczepa'] == wybrana_naczepa)
]

st.title(f"🚛 {wybrany_event} | AUTO: {wybrana_naczepa}")

c1, c2, c3 = st.columns(3)
zajete = len(df_current_auto['Rząd'].unique())
c1.metric("Zajęte Rzędy (LDM)", f"{zajete} / 15", f"{round((zajete/15)*100)}% Wypełnienia")
c2.metric("Liczba Operacji", len(df_current_auto), "Bloki przestrzenne")
c3.metric("Status Auta", "GOTOWE DO DROGI" if zajete >= 14 else "W TRAKCIE ZAŁADUNKU", "Wydanie")
st.markdown("---")

# ==========================================
# 5. SILNIK RENDEROWANIA 3D 
# ==========================================
fig3d = go.Figure()

W, L, H = 2.45, 13.6, 2.7
ROW_L = L / 15

fig3d.add_trace(go.Mesh3d(x=[0, W, W, 0], y=[0, 0, L, L], z=[0, 0, 0, 0], i=[0, 0], j=[1, 2], k=[2, 3], color='#334155', opacity=1.0, hoverinfo='skip'))
fig3d.add_trace(go.Scatter3d(x=[0, W, W, 0, 0, 0, W, W, 0, 0], y=[0, 0, L, L, 0, 0, 0, L, L, 0], z=[0, 0, 0, 0, 0, H, H, H, H, H], mode='lines', line=dict(color='#7dd3fc', width=4), hoverinfo='skip'))

def draw_block(fig, x_range, y_range, z_range, color, text):
    x = [x_range[0], x_range[0], x_range[1], x_range[1], x_range[0], x_range[0], x_range[1], x_range[1]]
    y = [y_range[0], y_range[1], y_range[1], y_range[0], y_range[0], y_range[1], y_range[1], y_range[0]]
    z = [z_range[0], z_range[0], z_range[0], z_range[0], z_range[1], z_range[1], z_range[1], z_range[1]]
    i, j, k = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
    
    fig.add_trace(go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color=color, opacity=1.0, hoverinfo='text', text=text,
        flatshading=True, lighting=dict(ambient=0.8, diffuse=0.9, roughness=0.5, specular=0.2)
    ))

for idx, row in df_current_auto.iterrows():
    y_start = (row['Rząd'] - 1) * ROW_L
    y_end = row['Rząd'] * ROW_L - 0.05 
    
    p1, p2 = row['Projekt_1'], row['Projekt_2']
    c1 = kolory_skrzyn.get(p1, '#64748b') 
    c2 = kolory_skrzyn.get(p2, '#64748b')
    
    opis_base = f"<b>RZĄD {row['Rząd']}</b><br>Układ: {row['Układ']}<br>Uwagi: {row['Uwagi']}"

    if "Pełny" in row['Układ']:
        draw_block(fig3d, [0.05, W-0.05], [y_start, y_end], [0, H*0.8], c1, f"{opis_base}<br>Projekt: {p1}")
    elif "Lewa / Prawa" in row['Układ']:
        draw_block(fig3d, [0.05, W/2-0.05], [y_start, y_end], [0, H*0.8], c1, f"{opis_base}<br>Strona Lewa: {p1}")
        if p2 != "Brak":
            draw_block(fig3d, [W/2+0.05, W-0.05], [y_start, y_end], [0, H*0.8], c2, f"{opis_base}<br>Strona Prawa: {p2}")
    elif "Dół / Góra" in row['Układ']:
        draw_block(fig3d, [0.05, W-0.05], [y_start, y_end], [0, H*0.4], c1, f"{opis_base}<br>Poziom Dół: {p1}")
        if p2 != "Brak":
            draw_block(fig3d, [0.05, W-0.05], [y_start, y_end], [H*0.4+0.05, H*0.8], c2, f"{opis_base}<br>Poziom Góra: {p2}")

fig3d.update_layout(
    scene=dict(
        aspectmode='data', 
        xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
        camera=dict(eye=dict(x=-2.2, y=-1.8, z=1.0)) 
    ),
    margin=dict(l=0, r=0, t=0, b=0), height=750, showlegend=False, paper_bgcolor='rgba(0,0,0,0)' 
)
st.plotly_chart(fig3d, use_container_width=True)

# ==========================================
# 6. TABELA ROZŁADUNKOWA (CZYSTA!)
# ==========================================
st.markdown("### 📋 MANIFEST ROZŁADUNKOWY (LIFO)")
if not df_current_auto.empty:
    # Wybieramy TYLKO istotne kolumny dla ekipy rozładunkowej
    kolumny_do_tabeli = ['Rząd', 'Układ', 'Projekt_1', 'Projekt_2', 'Uwagi']
    df_rozladunek = df_current_auto[kolumny_do_tabeli].sort_values(by='Rząd', ascending=False).reset_index(drop=True)
    
    st.dataframe(
        df_rozladunek, 
        use_container_width=True, 
        hide_index=True
    )
