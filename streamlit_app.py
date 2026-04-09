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

# Zaawansowany CSS (Mroczny, profesjonalny motyw Industrial/Sci-Fi)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp { 
        background-color: #0b1120; 
        color: #e2e8f0; 
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; 
    }
    
    h1, h2, h3 { 
        color: #38bdf8; 
        font-weight: 600; 
        text-transform: uppercase; 
        letter-spacing: 1px;
    }
    
    /* Stylizacja wskaźników KPI */
    div[data-testid="metric-container"] {
        background: #1e293b; 
        border-left: 4px solid #38bdf8;
        border-radius: 8px; 
        padding: 15px; 
        border-top: 1px solid #334155;
        border-right: 1px solid #334155;
        border-bottom: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }
    div[data-testid="metric-container"] > div {
        color: #f8fafc;
    }
    
    /* Stylizacja przycisków */
    div.stButton > button:first-child {
        background-color: #0284c7; 
        color: white; 
        border: none;
        border-radius: 6px; 
        font-weight: bold; 
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:first-child:hover { 
        background-color: #0369a1; 
        transform: translateY(-2px);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BAZA DANYCH I SŁOWNIKI
# ==========================================
# Inicjalizacja "bazy danych" w pamięci aplikacji
if 'cargo_db' not in st.session_state:
    st.session_state.cargo_db = pd.DataFrame(columns=[
        'Rząd', 'Układ', 'Projekt_1', 'Projekt_2', 'Uwagi'
    ])

# Słowniki opcji
projekty_lista = ["Brak", "21374 - Hannover", "24001 - Samsung", "24552 - Budimex", "MIX - Drobnica"]
uklady_lista = ["🟩 Pełny rząd (1 Projekt)", "🔲 Podzielony: Lewa / Prawa", "🟰 Piętrowany: Dół / Góra"]

# Paleta kolorów dla renderowania 3D
kolory_skrzyn = {
    '21374 - Hannover': '#0284c7', # Niebieski
    '24001 - Samsung': '#dc2626',  # Czerwony
    '24552 - Budimex': '#16a34a',  # Zielony
    'MIX - Drobnica': '#ea580c'    # Pomarańczowy
}

# ==========================================
# 3. INTERFEJS UŻYTKOWNIKA - SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>⚡ PANEL ZAŁADUNKU</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Formularz dodawania rzędu
    with st.form("add_row_form", clear_on_submit=True):
        rzad = st.number_input("Kolejny Rząd (od kabiny):", min_value=1, max_value=15, value=len(st.session_state.cargo_db)+1)
        uklad = st.selectbox("Szablon Układu:", uklady_lista)
        
        st.markdown("---")
        p1 = st.selectbox("Projekt Główny (lub Lewy / Dół):", projekty_lista, index=1)
        p2 = st.selectbox("Projekt Dodatkowy (lub Prawy / Góra):", projekty_lista, index=0, help="Zostaw 'Brak', jeśli rząd jest pełny.")
        uwagi = st.text_input("Uwagi (opcjonalnie):", placeholder="np. Delikatne, Wózek z boku")
        
        if st.form_submit_button("🔽 UMIEŚĆ W NACZEPIE", use_container_width=True):
            nowe_dane = pd.DataFrame([{
                'Rząd': rzad, 
                'Układ': uklad, 
                'Projekt_1': p1, 
                'Projekt_2': p2 if "Pełny" not in uklad else "Brak", 
                'Uwagi': uwagi
            }])
            st.session_state.cargo_db = pd.concat([st.session_state.cargo_db, nowe_dane], ignore_index=True)
            st.rerun()

    st.markdown("---")
    if st.button("🗑️ Resetuj Naczepę (Nowy Załadunek)", use_container_width=True):
        st.session_state.cargo_db = st.session_state.cargo_db.iloc[0:0]
        st.rerun()

# ==========================================
# 4. GŁÓWNY PANEL (KPI i Nagłówek)
# ==========================================
st.title("🚛 CYFROWY BLIŹNIAK NACZEPY")
df = st.session_state.cargo_db

# Kafelki ze statystykami
c1, c2, c3 = st.columns(3)
zajete = len(df['Rząd'].unique())
c1.metric("Zajęte Rzędy (LDM)", f"{zajete} / 15", f"{round((zajete/15)*100)}% Wypełnienia")
c2.metric("Liczba Operacji (Bloków)", len(df))
c3.metric("Status Auta", "GOTOWE DO DROGI" if zajete >= 14 else "W TRAKCIE ZAŁADUNKU")
st.markdown("---")

# ==========================================
# 5. SILNIK RENDEROWANIA 3D (PLOTLY)
# ==========================================
fig3d = go.Figure()

# Wymiary fizyczne standardowej naczepy (w metrach)
W, L, H = 2.45, 13.6, 2.7
ROW_L = L / 15

# Rysowanie podłogi (Ciemna powierzchnia)
fig3d.add_trace(go.Mesh3d(
    x=[0, W, W, 0], y=[0, 0, L, L], z=[0, 0, 0, 0], 
    i=[0, 0], j=[1, 2], k=[2, 3], 
    color='#1e293b', opacity=1.0, hoverinfo='skip'
))

# Rysowanie krawędzi (Szkielet naczepy)
fig3d.add_trace(go.Scatter3d(
    x=[0, W, W, 0, 0, 0, W, W, 0, 0], 
    y=[0, 0, L, L, 0, 0, 0, L, L, 0], 
    z=[0, 0, 0, 0, 0, H, H, H, H, H], 
    mode='lines', line=dict(color='#38bdf8', width=3), hoverinfo='skip'
))

# Funkcja pomocnicza do budowania trójwymiarowych klocków (Flight Case'ów)
def draw_block(fig, x_range, y_range, z_range, color, text):
    x = [x_range[0], x_range[0], x_range[1], x_range[1], x_range[0], x_range[0], x_range[1], x_range[1]]
    y = [y_range[0], y_range[1], y_range[1], y_range[0], y_range[0], y_range[1], y_range[1], y_range[0]]
    z = [z_range[0], z_range[0], z_range[0], z_range[0], z_range[1], z_range[1], z_range[1], z_range[1]]
    i, j, k = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
    
    fig.add_trace(go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color=color, opacity=0.95, hoverinfo='text', text=text,
        flatshading=True, # Nadaje matowy, realistyczny wygląd skrzyń
        lighting=dict(ambient=0.6, diffuse=0.9, roughness=0.8, specular=0.1)
    ))

# Logika układania Makro-Bloków w przestrzeni 3D
for idx, row in df.iterrows():
    y_start = (row['Rząd'] - 1) * ROW_L
    y_end = row['Rząd'] * ROW_L - 0.05 # Lekki odstęp dla realizmu
    
    p1, p2 = row['Projekt_1'], row['Projekt_2']
    c1 = kolory_skrzyn.get(p1, '#475569') # Domyślny szary, jeśli projekt nie jest na liście
    c2 = kolory_skrzyn.get(p2, '#475569')
    
    opis_base = f"<b>RZĄD {row['Rząd']}</b><br>Układ: {row['Układ']}<br>Uwagi: {row['Uwagi']}"

    if "Pełny" in row['Układ']:
        # 1. Cały rząd zajęty przez jeden projekt
        draw_block(fig3d, [0.02, W-0.02], [y_start, y_end], [0, H*0.8], c1, f"{opis_base}<br>Projekt: {p1}")
        
    elif "Lewa / Prawa" in row['Układ']:
        # 2. Dwa projekty obok siebie
        draw_block(fig3d, [0.02, W/2-0.02], [y_start, y_end], [0, H*0.8], c1, f"{opis_base}<br>Strona Lewa: {p1}")
        if p2 != "Brak":
            draw_block(fig3d, [W/2+0.02, W-0.02], [y_start, y_end], [0, H*0.8], c2, f"{opis_base}<br>Strona Prawa: {p2}")
            
    elif "Dół / Góra" in row['Układ']:
        # 3. Jeden projekt piętrowany na drugim
        draw_block(fig3d, [0.02, W-0.02], [y_start, y_end], [0, H*0.4], c1, f"{opis_base}<br>Poziom Dół: {p1}")
        if p2 != "Brak":
            draw_block(fig3d, [0.02, W-0.02], [y_start, y_end], [H*0.4+0.05, H*0.8], c2, f"{opis_base}<br>Poziom Góra: {p2}")

# Ustawienia sceny 3D (Kamera, tło, ukrycie osi)
fig3d.update_layout(
    scene=dict(
        xaxis=dict(visible=False), 
        yaxis=dict(visible=False), 
        zaxis=dict(visible=False),
        camera=dict(eye=dict(x=-1.5, y=-1.8, z=0.8)) # Kamera patrzy od strony drzwi
    ),
    margin=dict(l=0, r=0, t=0, b=0), 
    height=600, 
    showlegend=False, 
    paper_bgcolor='rgba(0,0,0,0)' # Przezroczyste tło wykresu
)

# Wyświetlenie wykresu w Streamlit
st.plotly_chart(fig3d, use_container_width=True)

# ==========================================
# 6. TABELA ROZŁADUNKOWA (Od drzwi do kabiny)
# ==========================================
st.markdown("### 📋 MANIFEST ROZŁADUNKOWY (LIFO)")
if not df.empty:
    # Sortowanie odwrotne - najwyższy rząd (najbliżej drzwi) jest pierwszy
    df_rozladunek = df.sort_values(by='Rząd', ascending=False).reset_index(drop=True)
    st.dataframe(
        df_rozladunek, 
        use_container_width=True, 
        hide_index=True,
        height=300
    )
