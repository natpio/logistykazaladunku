import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. KONFIGURACJA STRONY (Wymuszony układ szeroki)
st.set_page_config(page_title="SQM | System Załadunkowy", page_icon="🛸", layout="wide", initial_sidebar_state="expanded")

# 2. POTĘŻNY CSS - STYLIZACJA ENTERPRISE
st.markdown("""
    <style>
    /* Ukrycie domyślnych elementów Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Globalne tło i czcionki */
    .stApp {
        background-color: #0b1121;
        background-image: radial-gradient(circle at 50% 0%, #1e293b 0%, #0b1121 70%);
        color: #e2e8f0;
    }
    
    h1, h2, h3 {
        font-family: 'Trebuchet MS', sans-serif;
        color: #00f3ff !important;
        text-shadow: 0 0 10px rgba(0, 243, 255, 0.3);
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }

    /* Glassmorphism dla KPI (Wskaźników) */
    div[data-testid="metric-container"] {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(0, 243, 255, 0.2);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        transition: transform 0.3s ease, border 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        border: 1px solid rgba(0, 243, 255, 0.8);
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.2);
    }
    div[data-testid="metric-container"] > div {
        color: #fff;
    }

    /* Super guziki */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        letter-spacing: 1px;
        padding: 10px 24px;
        transition: all 0.3s ease 0s;
        box-shadow: 0px 5px 15px rgba(0, 210, 255, 0.4);
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0px 10px 20px rgba(0, 210, 255, 0.6);
    }
    
    /* Stylizacja zakładek */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #94a3b8;
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        color: #00f3ff !important;
        border-bottom: 2px solid #00f3ff !important;
        background: rgba(0, 243, 255, 0.05);
    }
    </style>
""", unsafe_allow_html=True)

# 3. BAZA DANYCH (Słowniki i symulacja pamięci)
if 'global_db' not in st.session_state:
    st.session_state.global_db = pd.DataFrame(columns=['Event', 'Naczepa', 'Rząd', 'Projekt', 'Hala', 'Uwagi', 'Ostrożnie'])

eventy = ["Hannover Messe 2026", "ISE Barcelona 2026"]
flota = ["PO 1234A (Mega)", "WA 9876C (Standard)", "KR 5555X (Standard)"]
projekty_slownik = {
    "21374 - Hannover Messe": "Hala 2",
    "24001 - Samsung": "Hala 3A",
    "24552 - Budimex": "Hala 5",
    "MIX - Drobnica": "Różne"
}

# Ekskluzywna paleta barw (Neon/Cyberpunk)
kolory_premium = ['#00f3ff', '#ff003c', '#00ff66', '#ffea00', '#bd00ff', '#ff7b00']

# 4. SIDEBAR - PANEL DOWODZENIA
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: white;'>📡 SQM CTRL</h2>", unsafe_allow_html=True)
    st.markdown("---")
    wybrany_event = st.selectbox("📍 Docelowe Targi", eventy)
    wybrana_naczepa = st.selectbox("🚛 Przypisane Auto", flota)
    st.markdown("---")
    
    with st.form("add_row_form", clear_on_submit=True):
        st.markdown("### ⚡ Szybki Załadunek")
        wybrany_projekt = st.selectbox("Projekt (ID - Nazwa)", list(projekty_slownik.keys()))
        uwagi = st.text_input("Uwagi (Szczegóły)", placeholder="np. Wózek z lewej")
        ostroznie = st.checkbox("⚠️ Sprzęt Delikatny / Luźny")
        
        if st.form_submit_button("➕ SPNIJ PASY (DODAJ RZĄD)", use_container_width=True):
            nowy_rzad = len(st.session_state.global_db[(st.session_state.global_db['Naczepa'] == wybrana_naczepa)]) + 1
            nowe_dane = pd.DataFrame([{
                'Event': wybrany_event, 'Naczepa': wybrana_naczepa, 'Rząd': nowy_rzad,
                'Projekt': wybrany_projekt.split(" - ")[0], 'Hala': projekty_slownik[wybrany_projekt],
                'Uwagi': uwagi, 'Ostrożnie': ostroznie
            }])
            st.session_state.global_db = pd.concat([st.session_state.global_db, nowe_dane], ignore_index=True)
            st.rerun()
            
    if st.button("🚨 AWARYJNY RESET AUTA", use_container_width=True):
        mask = ~((st.session_state.global_db['Event'] == wybrany_event) & (st.session_state.global_db['Naczepa'] == wybrana_naczepa))
        st.session_state.global_db = st.session_state.global_db[mask]
        st.rerun()

# 5. DANE DLA AKTUALNEGO AUTA
df_widok = st.session_state.global_db[(st.session_state.global_db['Event'] == wybrany_event) & (st.session_state.global_db['Naczepa'] == wybrana_naczepa)]
projekty_all = st.session_state.global_db['Projekt'].unique()
mapa_kolorow = {proj: kolory_premium[i % len(kolory_premium)] for i, proj in enumerate(projekty_all)}

# 6. GŁÓWNY INTERFEJS (NAGŁÓWEK I KPI)
st.title(f"LIVE: {wybrany_event} 🚀")
st.markdown(f"**Jednostka: {wybrana_naczepa}** | Synchronizacja: OK")

zajete_rzedy = len(df_widok)
c1, c2, c3 = st.columns(3)
c1.metric("Przestrzeń Naczepy", f"{zajete_rzedy} / 15", f"{round((zajete_rzedy/15)*100)}% LDM")
c2.metric("Unikalne Projekty", len(df_widok['Projekt'].unique()), "Weryfikacja Hali")
c3.metric("Status Operacyjny", "GOTOWA DO DROGI" if zajete_rzedy >= 13 else "W TRAKCIE ZAŁADUNKU", "Real-time")
st.markdown("<br>", unsafe_allow_html=True)

# 7. ZAKŁADKI WIZUALIZACJI
tab_3d, tab_2d, tab_tabela = st.tabs(["🧊 HOLOGRAM 3D", "📐 SCHEMAT PŁASKI", "📋 MANIFEST ROZŁADUNKOWY"])

# --- ZAKŁADKA 1: HOLOGRAFICZNY WIDOK 3D ---
with tab_3d:
    fig3d = go.Figure()
    
    # 1. Podświetlana "Podłoga" naczepy
    fig3d.add_trace(go.Mesh3d(
        x=[0, 2.45, 2.45, 0], y=[0, 0, 13.6, 13.6], z=[0, 0, 0, 0],
        i=[0, 0], j=[1, 2], k=[2, 3],
        color='rgba(0, 243, 255, 0.1)', opacity=0.5, hoverinfo='skip'
    ))

    # 2. Siatka/Szkielet Naczepy (Neon)
    fig3d.add_trace(go.Scatter3d(
        x=[0, 2.45, 2.45, 0, 0, 0, 2.45, 2.45, 0, 0],
        y=[0, 0, 13.6, 13.6, 0, 0, 0, 13.6, 13.6, 0],
        z=[0, 0, 0, 0, 0, 2.7, 2.7, 2.7, 2.7, 2.7],
        mode='lines', line=dict(color='#00f3ff', width=4), name="Szkielet LDM", hoverinfo='skip'
    ))

    # 3. Bloki Ładunku (Rendering z oświetleniem)
    dlugosc_rzedu = 13.6 / 15
    for idx, row in df_widok.iterrows():
        y_start = (row['Rząd'] - 1) * dlugosc_rzedu
        y_end = row['Rząd'] * dlugosc_rzedu
        kolor = mapa_kolorow[row['Projekt']]
        
        x = [0.05, 0.05, 2.40, 2.40, 0.05, 0.05, 2.40, 2.40] # Lekki odstęp od ścian
        y = [y_start, y_end, y_end, y_start, y_start, y_end, y_end, y_start]
        z = [0, 0, 0, 0, 2.65, 2.65, 2.65, 2.65]
        i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]
        j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]
        k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
        
        opis = f"<b>RZĄD {row['Rząd']}</b><br>Projekt: {row['Projekt']}<br>Hala: {row['Hala']}<br>Status: {'⚠️ UWAGA' if row['Ostrożnie'] else 'OK'}<br>Info: {row['Uwagi']}"
        
        fig3d.add_trace(go.Mesh3d(
            x=x, y=y, z=z, i=i, j=j, k=k,
            color=kolor, opacity=0.85, name=row['Projekt'],
            hoverinfo='text', text=opis,
            # Zaawansowane oświetlenie nadające "metaliczno-szklany" wygląd
            lighting=dict(ambient=0.6, diffuse=0.9, roughness=0.2, specular=1.5, fresnel=0.5),
            lightposition=dict(x=5, y=5, z=5)
        ))

    # Konfiguracja przestrzeni (Ukrycie osi, pełny ciemny tryb)
    fig3d.update_layout(
        scene=dict(
            xaxis=dict(visible=False, showbackground=False),
            yaxis=dict(visible=False, showbackground=False),
            zaxis=dict(visible=False, showbackground=False),
            camera=dict(eye=dict(x=-1.8, y=-1.8, z=1.2), projection=dict(type='perspective'))
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=700,
        showlegend=False
    )
    st.plotly_chart(fig3d, use_container_width=True)

# --- ZAKŁADKA 2: WIDOK 2D (SCHEMAT RADAROWY) ---
with tab_2d:
    if not df_widok.empty:
        fig2d = go.Figure()
        for idx, row in df_widok.iterrows():
            kolor = mapa_kolorow[row['Projekt']]
            opis = f"<b>Sektor {row['Rząd']}</b> | Proj: {row['Projekt']} (Hala {row['Hala']})<br>{row['Uwagi']}"
            fig2d.add_trace(go.Bar(
                x=[1], y=[1], orientation='v',
                marker=dict(color=kolor, line=dict(color='#0b1121', width=3)),
                text=opis, textposition='inside', insidetextanchor='middle', hoverinfo='text',
                textfont=dict(size=14, color='white', family='Arial Black')
            ))
        fig2d.update_layout(
            barmode='stack', showlegend=False, height=600,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False, autorange='reversed'),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=20, b=0)
        )
        st.plotly_chart(fig2d, use_container_width=True)
    else:
        st.info("Brak ładunku do wyświetlenia.")

# --- ZAKŁADKA 3: MANIFEST ROZŁADUNKOWY ---
with tab_tabela:
    if not df_widok.empty:
        st.markdown("### 📥 KOLEJNOŚĆ WYŁADUNKU (Od drzwi)")
        df_rozladunek = df_widok.iloc[::-1].reset_index(drop=True)
        # Formatowanie tabeli
        st.dataframe(
            df_rozladunek[['Rząd', 'Projekt', 'Hala', 'Uwagi', 'Ostrożnie']], 
            use_container_width=True,
            height=400
        )
