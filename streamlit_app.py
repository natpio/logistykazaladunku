import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. KONFIGURACJA STRONY
st.set_page_config(page_title="SQM Logistics | 3D Fleet View", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stMetric {background-color: #1e1e1e; color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #1f77b4;}
    div[data-testid="metric-container"] > div {color: white;}
    </style>
""", unsafe_allow_html=True)

# 2. BAZA DANYCH
if 'global_db' not in st.session_state:
    st.session_state.global_db = pd.DataFrame(columns=['Event', 'Naczepa', 'Rząd', 'Projekt', 'Hala', 'Uwagi', 'Ostrożnie'])

eventy = ["Hannover Messe 2026", "ISE Barcelona 2026"]
flota = ["PO 1234A (Mega)", "WA 9876C (Standard)"]
projekty_slownik = {
    "21374 - Hannover Messe": "Hala 2",
    "24001 - Samsung": "Hala 3A",
    "24552 - Budimex": "Hala 5",
    "MIX - Drobnica": "Różne"
}

# 3. SIDEBAR
with st.sidebar:
    st.header("📍 Kontekst Pracy")
    wybrany_event = st.selectbox("1. Wybierz Event", eventy)
    wybrana_naczepa = st.selectbox("2. Wybierz Naczepę", flota)
    st.markdown("---")
    
    st.subheader("⚡ Dodaj ładunek")
    with st.form("add_row_form", clear_on_submit=True):
        wybrany_projekt = st.selectbox("Wybierz Projekt", list(projekty_slownik.keys()))
        uwagi = st.text_input("Uwagi (np. Wózek)")
        ostroznie = st.checkbox("⚠️ Uwaga (Szkło)")
        
        if st.form_submit_button("➕ ZAPNIJ PASY (DODAJ RZĄD)", use_container_width=True):
            nowy_rzad = len(st.session_state.global_db[(st.session_state.global_db['Naczepa'] == wybrana_naczepa)]) + 1
            nowe_dane = pd.DataFrame([{
                'Event': wybrany_event, 'Naczepa': wybrana_naczepa, 'Rząd': nowy_rzad,
                'Projekt': wybrany_projekt.split(" - ")[0], 'Hala': projekty_slownik[wybrany_projekt],
                'Uwagi': uwagi, 'Ostrożnie': ostroznie
            }])
            st.session_state.global_db = pd.concat([st.session_state.global_db, nowe_dane], ignore_index=True)
            st.rerun()
            
    if st.button("🗑️ Wyczyść to auto", use_container_width=True):
        mask = ~((st.session_state.global_db['Event'] == wybrany_event) & (st.session_state.global_db['Naczepa'] == wybrana_naczepa))
        st.session_state.global_db = st.session_state.global_db[mask]
        st.rerun()

# 4. DANE DLA AKTUALNEGO AUTA
df_widok = st.session_state.global_db[(st.session_state.global_db['Event'] == wybrany_event) & (st.session_state.global_db['Naczepa'] == wybrana_naczepa)]

# 5. NAGŁÓWEK I KPI
st.title(f"🚚 {wybrany_event} | Auto: {wybrana_naczepa}")
zajete_rzedy = len(df_widok)
c1, c2, c3 = st.columns(3)
c1.metric("Zajęte Rzędy", f"{zajete_rzedy} / 15")
c2.metric("Liczba Projektów", len(df_widok['Projekt'].unique()))
c3.metric("Status", "GOTOWA" if zajete_rzedy >= 13 else "W TRAKCIE ZAŁADUNKU")
st.markdown("---")

# ZAKŁADKI WIDOKÓW
tab_3d, tab_2d, tab_tabela = st.tabs(["🧊 Model 3D (Interaktywny)", "📏 Widok 2D (Płaski)", "📋 Raport Magazynowy"])

# WSPÓLNE KOLORY
kolory = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
projekty_all = st.session_state.global_db['Projekt'].unique()
mapa_kolorow = {proj: kolory[i % len(kolory)] for i, proj in enumerate(projekty_all)}

# --- ZAKŁADKA 1: WIDOK 3D ---
with tab_3d:
    fig3d = go.Figure()
    
    # Rysowanie "podłogi" i siatki naczepy (13.6m długości, 2.45m szerokości, 2.7m wysokości)
    fig3d.add_trace(go.Scatter3d(
        x=[0, 2.45, 2.45, 0, 0, 0, 2.45, 2.45, 0, 0],
        y=[0, 0, 13.6, 13.6, 0, 0, 0, 13.6, 13.6, 0],
        z=[0, 0, 0, 0, 0, 2.7, 2.7, 2.7, 2.7, 2.7],
        mode='lines', line=dict(color='gray', width=2), name="Kontur Naczepy", hoverinfo='skip'
    ))

    # Rysowanie bloków 3D
    dlugosc_rzedu = 13.6 / 15 # ~0.9m na rząd
    
    for idx, row in df_widok.iterrows():
        y_start = (row['Rząd'] - 1) * dlugosc_rzedu
        y_end = row['Rząd'] * dlugosc_rzedu
        kolor = mapa_kolorow[row['Projekt']]
        
        # Wierzchołki prostopadłościanu
        x = [0, 0, 2.45, 2.45, 0, 0, 2.45, 2.45]
        y = [y_start, y_end, y_end, y_start, y_start, y_end, y_end, y_start]
        z = [0, 0, 0, 0, 2.7, 2.7, 2.7, 2.7]
        # Definicja trójkątów budujących ściany
        i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]
        j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]
        k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
        
        opis = f"Rząd {row['Rząd']}<br>Projekt: {row['Projekt']}<br>Hala: {row['Hala']}<br>Uwagi: {row['Uwagi']}"
        
        fig3d.add_trace(go.Mesh3d(
            x=x, y=y, z=z, i=i, j=j, k=k,
            color=kolor, opacity=0.9, name=row['Projekt'],
            hoverinfo='text', text=opis
        ))

    fig3d.update_layout(
        scene=dict(
            xaxis=dict(title='Szerokość [m]', range=[-1, 3.5]),
            yaxis=dict(title='Długość Naczepy (Kabina -> Drzwi) [m]', range=[-1, 15]),
            zaxis=dict(title='Wysokość [m]', range=[0, 3.5]),
            camera=dict(eye=dict(x=-1.5, y=-1.5, z=1.2)) # Domyślny kąt kamery
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=600,
        showlegend=False
    )
    st.plotly_chart(fig3d, use_container_width=True)

# --- ZAKŁADKA 2: WIDOK 2D ---
with tab_2d:
    if not df_widok.empty:
        fig2d = go.Figure()
        for idx, row in df_widok.iterrows():
            opis = f"Rząd {row['Rząd']} | {'⚠️ ' if row['Ostrożnie'] else ''}Proj: {row['Projekt']} (Hala {row['Hala']})<br>{row['Uwagi']}"
            fig2d.add_trace(go.Bar(
                x=[1], y=[1], orientation='v',
                marker=dict(color=mapa_kolorow[row['Projekt']], line=dict(color='white', width=2)),
                text=opis, textposition='inside', insidetextanchor='middle', hoverinfo='text'
            ))
        fig2d.update_layout(
            title="Widok Płaski (Lżejszy dla telefonów)", barmode='stack', showlegend=False, height=500,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, autorange='reversed'),
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig2d, use_container_width=True)
    else:
        st.info("Naczepa jest pusta.")

# --- ZAKŁADKA 3: TABELA ROZŁADUNKOWA ---
with tab_tabela:
    if not df_widok.empty:
        st.write("Kolejność rozładunku (Od drzwi do kabiny):")
        df_rozladunek = df_widok.iloc[::-1].reset_index(drop=True)
        st.dataframe(df_rozladunek[['Rząd', 'Projekt', 'Hala', 'Uwagi', 'Ostrożnie']], use_container_width=True)
