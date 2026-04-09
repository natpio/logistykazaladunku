import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. KONFIGURACJA STRONY (Mroczny, profesjonalny motyw)
st.set_page_config(page_title="SQM | Załadunek PRO", page_icon="🏗️", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    .stApp { background-color: #0e1117; color: #c9d1d9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    h1, h2, h3 { color: #58a6ff; font-weight: 600; text-transform: uppercase; }
    div[data-testid="metric-container"] {
        background: #161b22; border-left: 4px solid #58a6ff;
        border-radius: 6px; padding: 15px; border: 1px solid #30363d;
    }
    </style>
""", unsafe_allow_html=True)

# 2. BAZA DANYCH
if 'cargo_db' not in st.session_state:
    st.session_state.cargo_db = pd.DataFrame(columns=[
        'Rząd', 'Układ', 'Projekt_1', 'Projekt_2', 'Uwagi'
    ])

projekty_lista = ["Brak", "21374 - Hannover", "24001 - Samsung", "24552 - Budimex", "MIX - Drobnica"]
uklady_lista = ["🟩 Pełny rząd (1 Projekt)", "🔲 Podzielony: Lewa / Prawa", "🟰 Piętrowany: Dół / Góra"]

# Stałe palety kolorów dla projektów (Industrialne, stonowane kolory)
kolory_skrzyn = {
    '21374 - Hannover': '#1f77b4', # Niebieski
    '24001 - Samsung': '#d62728',  # Czerwony
    '24552 - Budimex': '#2ca02c',  # Zielony
    'MIX - Drobnica': '#ff7f0e'    # Pomarańczowy
}

# 3. INTERFEJS UŻYTKOWNIKA - SIDEBAR
with st.sidebar:
    st.header("⚡ SZYBKI ZAŁADUNEK")
    st.info("Wybierz szablon rzędu i przypisz projekty. Zero zbędnego klikania.")
    
    # Formularz dodawania rzędu
    with st.form("add_row_form", clear_on_submit=True):
        rzad = st.number_input("Kolejny Rząd (od kabiny):", min_value=1, max_value=15, value=len(st.session_state.cargo_db)+1)
        uklad = st.selectbox("Szablon Układu:", uklady_lista)
        
        st.markdown("---")
        p1 = st.selectbox("Projekt Główny (lub Lewy / Dół):", projekty_lista, index=1)
        p2 = st.selectbox("Projekt Dodatkowy (lub Prawy / Góra):", projekty_lista, index=0, help="Zostaw 'Brak', jeśli rząd jest pełny.")
        uwagi = st.text_input("Uwagi (opcjonalnie):", placeholder="np. Uważać przy otwieraniu")
        
        if st.form_submit_button("🔽 DODAJ RZĄD", use_container_width=True):
            nowe_dane = pd.DataFrame([{
                'Rząd': rzad, 'Układ': uklad, 
                'Projekt_1': p1, 'Projekt_2': p2 if "Pełny" not in uklad else "Brak", 
                'Uwagi': uwagi
            }])
            st.session_state.cargo_db = pd.concat([st.session_state.cargo_db, nowe_dane], ignore_index=True)
            st.rerun()

    if st.button("🗑️ Resetuj Naczepę", use_container_width=True):
        st.session_state.cargo_db = st.session_state.cargo_db.iloc[0:0] # Czyści zachowując kolumny
        st.rerun()

# 4. GŁÓWNY PANEL (KPI i Tytuł)
st.title("🚛 Cyfrowy Bliźniak Naczepy")
df = st.session_state.cargo_db

c1, c2, c3 = st.columns(3)
c1.metric("Zajęte Rzędy", f"{len(df['Rząd'].unique())} / 15")
c2.metric("Tryb Wprowadzania", "Makro-Bloki")
c3.metric("Status", "GOTOWE" if len(df) >= 14 else "W TRAKCIE")
st.markdown("---")

# 5. RENDEROWANIE 3D (Zoptymalizowane)
fig3d = go.Figure()

# Wymiary naczepy
W, L, H = 2.45, 13.6, 2.7
ROW_L = L / 15

# Podłoga i Plandeka
fig3d.add_trace(go.Mesh3d(x=[0, W, W, 0], y=[0, 0, L, L], z=[0, 0, 0, 0], i=[0, 0], j=[1, 2], k=[2, 3], color='#2d3436', opacity=1.0, hoverinfo='skip'))
fig3d.add_trace(go.Scatter3d(x=[0, W, W, 0, 0, 0, W, W, 0, 0], y=[0, 0, L, L, 0, 0, 0, L, L, 0], z=[0, 0, 0, 0, 0, H, H, H, H, H], mode='lines', line=dict(color='#58a6ff', width=3), hoverinfo='skip'))

# Funkcja pomocnicza do rysowania bloków 3D
def draw_block(fig, x_range, y_range, z_range, color, text):
    x = [x_range[0], x_range[0], x_range[1], x_range[1], x_range[0], x_range[0], x_range[1], x_range[1]]
    y = [y_range[0], y_range[1], y_range[1], y_range[0], y_range[0], y_range[1], y_range[1], y_range[0]]
    z = [z_range[0], z_range[0], z_range[0], z_range[0], z_range[1], z_range[1], z_range[1], z_range[1]]
    i, j, k = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
    
    fig.add_trace(go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color=color, opacity=0.9, hoverinfo='text', text=text,
        flatshading=True, lighting=dict(ambient=0.7, diffuse=0.8, roughness=0.5, specular=0.2)
    ))

# Logika Generowania Makro-Bloków
for idx, row in df.iterrows():
    y_start = (row['Rząd'] - 1) * ROW_L
    y_end = row['Rząd'] * ROW_L - 0.05 # Lekki odstęp dla realizmu
    
    p1, p2 = row['Projekt_1'], row['Projekt_2']
    c1, c2 = kolory_skrzyn.get(p1, '#555555'), kolory_skrzyn.get(p2, '#555555')
    
    opis_base = f"<b>Rząd {row['Rząd']}</b><br>Układ: {row['Układ']}<br>Uwagi: {row['Uwagi']}"

    if "Pełny" in row['Układ']:
        # Cały rząd (1 blok)
        draw_block(fig3d, [0.02, W-0.02], [y_start, y_end], [0, H*0.8], c1, f"{opis_base}<br>Projekt: {p1}")
        
    elif "Lewa / Prawa" in row['Układ']:
        # Podział pionowy (2 bloki obok siebie)
        draw_block(fig3d, [0.02, W/2-0.02], [y_start, y_end], [0, H*0.8], c1, f"{opis_base}<br>Lewa strona: {p1}")
        if p2 != "Brak":
            draw_block(fig3d, [W/2+0.02, W-0.02], [y_start, y_end], [0, H*0.8], c2, f"{opis_base}<br>Prawa strona: {p2}")
            
    elif "Dół / Góra" in row['Układ']:
        # Podział poziomy (2 bloki jeden na drugim)
        draw_block(fig3d, [0.02, W-0.02], [y_start, y_end], [0, H*0.4], c1, f"{opis_base}<br>Dół: {p1}")
        if p2 != "Brak":
            draw_block(fig3d, [0.02, W-0.02], [y_start, y_end], [H*0.4+0.05, H*0.8], c2, f"{opis_base}<br>Góra: {p2}")

fig3d.update_layout(
    scene=dict(
        xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
        camera=dict(eye=dict(x=-1.5, y=-1.8, z=0.8))
    ),
    margin=dict(l=0, r=0, t=0, b=0), height=650, showlegend=False, paper_bgcolor='#0e1117'
)
st.plotly_chart(fig3d, use_container_width=True)

# 6. TABELA RAPORTOWA
st.markdown("### 📋 Manifest Rozładunkowy")
if not df.empty:
    st.dataframe(df.sort_values(by='Rząd', ascending=False), use_container_width=True, hide_index=True)
