import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. KONFIGURACJA STRONY (Styl Industrialny)
st.set_page_config(page_title="SQM | Digital Twin", page_icon="🏗️", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    .stApp { background-color: #f4f6f9; color: #2c3e50; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    h1, h2, h3 { color: #1a252f; font-weight: 600; text-transform: uppercase; }
    div[data-testid="metric-container"] {
        background: #ffffff; border-left: 5px solid #3498db;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-radius: 4px; padding: 15px;
    }
    div.stButton > button:first-child {
        background-color: #2c3e50; color: white; border-radius: 4px; font-weight: bold; transition: 0.2s;
    }
    div.stButton > button:first-child:hover { background-color: #34495e; }
    </style>
""", unsafe_allow_html=True)

# 2. BAZA DANYCH (Z obsługą pozycji X i Z)
if 'cargo_db' not in st.session_state:
    st.session_state.cargo_db = pd.DataFrame(columns=[
        'Event', 'Naczepa', 'Rząd', 'Pozycja_X', 'Piętro_Z', 'Projekt', 'Uwagi'
    ])

eventy = ["Targi Hannover 2026", "Targi ISE 2026"]
flota = ["Naczepa 01 (Standard)", "Naczepa 02 (Mega)"]
projekty_slownik = {"21374 - Hannover": "Hala 2", "24001 - Samsung": "Hala 3A", "MIX - Akcesoria": "Baza"}
pozycje_x = ["Cała szerokość", "Lewa strona", "Prawa strona", "Środek"]
poziomy_z = ["0 - Podłoga", "1 - Na skrzyni (Piętro 1)", "2 - Wysoko (Piętro 2)"]

# Kolory przypominające czarne i szare flight case'y z kolorowymi etykietami/rogami
kolory_skrzyn = {'21374 - Hannover': '#2c3e50', '24001 - Samsung': '#c0392b', 'MIX - Akcesoria': '#f39c12'}

# 3. SIDEBAR - DODAWANIE ŁADUNKU
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Truck_icon.svg/1024px-Truck_icon.svg.png", width=60)
    st.header("🏗️ Panel Załadunku")
    wybrany_event = st.selectbox("Event", eventy)
    wybrana_naczepa = st.selectbox("Naczepa", flota)
    st.markdown("---")
    
    with st.form("add_cargo"):
        st.subheader("📦 Parametry Skrzyni")
        projekt = st.selectbox("Projekt", list(projekty_slownik.keys()))
        rzad = st.number_input("Numer Rzędu (1-15)", min_value=1, max_value=15, value=1)
        
        # Nowe parametry!
        col_x, col_z = st.columns(2)
        poz_x = col_x.selectbox("Szerokość", pozycje_x)
        poz_z = col_z.selectbox("Piętrowanie", poziomy_z)
        
        uwagi = st.text_input("Uwagi (np. Wózek)")
        
        if st.form_submit_button("🔽 UMIEŚĆ W NACZEPIE", use_container_width=True):
            nowe_dane = pd.DataFrame([{
                'Event': wybrany_event, 'Naczepa': wybrana_naczepa, 'Rząd': rzad,
                'Pozycja_X': poz_x, 'Piętro_Z': int(poz_z[0]), 'Projekt': projekt, 'Uwagi': uwagi
            }])
            st.session_state.cargo_db = pd.concat([st.session_state.cargo_db, nowe_dane], ignore_index=True)
            st.rerun()
            
    if st.button("🗑️ Opróżnij naczepę", use_container_width=True):
        mask = ~((st.session_state.cargo_db['Event'] == wybrany_event) & (st.session_state.cargo_db['Naczepa'] == wybrana_naczepa))
        st.session_state.cargo_db = st.session_state.cargo_db[mask]
        st.rerun()

# Filtrowanie dla widoku
df = st.session_state.cargo_db[(st.session_state.cargo_db['Event'] == wybrany_event) & (st.session_state.cargo_db['Naczepa'] == wybrana_naczepa)]

# 4. GŁÓWNY INTERFEJS
st.title(f"Naczepa: {wybrana_naczepa}")
st.markdown(f"**Trasa:** {wybrany_event} | **Podgląd:** Cyfrowy Bliźniak 3D")

c1, c2, c3 = st.columns(3)
c1.metric("Zajęte Rzędy (Długość)", f"{len(df['Rząd'].unique())} / 15")
c2.metric("Liczba Jednostek Ładunkowych", len(df))
c3.metric("Projekty w aucie", len(df['Projekt'].unique()))
st.markdown("---")

# 5. REALISTYCZNY RENDER 3D
fig3d = go.Figure()

# Wymiary fizyczne naczepy
TRUCK_W = 2.45
TRUCK_L = 13.6
TRUCK_H = 2.7
ROW_L = TRUCK_L / 15

# Rysowanie realistycznej podłogi (tekstura sklejki antypoślizgowej - brąz/szarość)
fig3d.add_trace(go.Mesh3d(
    x=[0, TRUCK_W, TRUCK_W, 0], y=[0, 0, TRUCK_L, TRUCK_L], z=[0, 0, 0, 0],
    i=[0, 0], j=[1, 2], k=[2, 3],
    color='#5c4d42', opacity=1.0, hoverinfo='skip', name="Podłoga"
))

# Krawędzie naczepy (Aluminiowe profile)
fig3d.add_trace(go.Scatter3d(
    x=[0, TRUCK_W, TRUCK_W, 0, 0, 0, TRUCK_W, TRUCK_W, 0, 0],
    y=[0, 0, TRUCK_L, TRUCK_L, 0, 0, 0, TRUCK_L, TRUCK_L, 0],
    z=[0, 0, 0, 0, 0, TRUCK_H, TRUCK_H, TRUCK_H, TRUCK_H, TRUCK_H],
    mode='lines', line=dict(color='#bdc3c7', width=6), hoverinfo='skip'
))

# Logika układania klocków (Obliczanie koordynatów)
for idx, row in df.iterrows():
    # OŚ Y (Długość)
    y_start = (row['Rząd'] - 1) * ROW_L
    y_end = row['Rząd'] * ROW_L - 0.05 # Odstęp 5cm między rzędami dla realizmu
    
    # OŚ X (Szerokość)
    if row['Pozycja_X'] == "Lewa strona":
        x_start, x_end = 0.02, (TRUCK_W / 2) - 0.02
    elif row['Pozycja_X'] == "Prawa strona":
        x_start, x_end = (TRUCK_W / 2) + 0.02, TRUCK_W - 0.02
    elif row['Pozycja_X'] == "Środek":
        x_start, x_end = (TRUCK_W / 4), (TRUCK_W * 0.75)
    else: # Cała szerokość
        x_start, x_end = 0.02, TRUCK_W - 0.02

    # OŚ Z (Wysokość/Piętrowanie - zakładamy skrzynie ok. 80cm wysokości)
    z_start = row['Piętro_Z'] * 0.85
    z_end = z_start + 0.8
    
    # Kolor skrzyni
    kolor = kolory_skrzyn.get(row['Projekt'], '#34495e')
    
    # Punkty 3D dla pojedynczej skrzyni
    x = [x_start, x_start, x_end, x_end, x_start, x_start, x_end, x_end]
    y = [y_start, y_end, y_end, y_start, y_start, y_end, y_end, y_start]
    z = [z_start, z_start, z_start, z_start, z_end, z_end, z_end, z_end]
    i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]
    j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]
    k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
    
    opis = f"<b>Rząd {row['Rząd']}</b><br>Pozycja: {row['Pozycja_X']}<br>Piętro: {row['Piętro_Z']}<br>Projekt: {row['Projekt']}"
    
    # Rysowanie bryły (Flight Case) z realistycznym oświetleniem matowym
    fig3d.add_trace(go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color=kolor, opacity=1.0, hoverinfo='text', text=opis,
        lighting=dict(ambient=0.7, diffuse=0.8, roughness=0.9, specular=0.1), # Matowe wykończenie
        flatshading=True # Wyostrza krawędzie, nadając wygląd skrzyń
    ))

fig3d.update_layout(
    scene=dict(
        xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
        camera=dict(eye=dict(x=-1.5, y=-1.8, z=1.0)) # Kamera ustawiona na róg drzwi naczepy
    ),
    margin=dict(l=0, r=0, t=0, b=0), height=700, showlegend=False, paper_bgcolor='#ffffff'
)
st.plotly_chart(fig3d, use_container_width=True)

# 6. TABELA ZAŁADUNKU (SZCZEGÓŁOWA)
st.subheader("Tabela Załadunku (Szczegóły)")
if not df.empty:
    st.dataframe(df.sort_values(by=['Rząd', 'Piętro_Z'], ascending=[False, False]), use_container_width=True)
