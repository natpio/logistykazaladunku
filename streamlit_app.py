import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. KONFIGURACJA STRONY
st.set_page_config(page_title="SQM Logistics | Fleet View", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stMetric {background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #1f77b4;}
    </style>
""", unsafe_allow_html=True)

# 2. BAZA DANYCH (Symulacja globalnej bazy)
if 'global_db' not in st.session_state:
    st.session_state.global_db = pd.DataFrame(columns=['Event', 'Naczepa', 'Rząd', 'Projekt', 'Hala', 'Uwagi', 'Ostrożnie'])

# Słowniki (W przyszłości zaciągane z innej zakładki w Google Sheets)
eventy = ["Hannover Messe 2026", "ISE Barcelona 2026", "IFA Berlin 2026"]
flota = ["PO 1234A (Mega)", "WA 9876C (Standard)", "KR 5555X (Standard)"]
projekty_slownik = {
    "21374 - Hannover Messe": "Hala 2",
    "24001 - Samsung": "Hala 3A",
    "24552 - Budimex": "Hala 5",
    "MIX - Drobnica": "Różne"
}

# 3. SIDEBAR - WYBÓR KONTEKSTU (Kluczowa zmiana!)
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Truck_icon.svg/1024px-Truck_icon.svg.png", width=80)
    st.header("📍 Kontekst Pracy")
    
    wybrany_event = st.selectbox("1. Wybierz Event", eventy)
    wybrana_naczepa = st.selectbox("2. Wybierz Naczepę", flota)
    
    st.markdown("---")
    st.write("👨‍💻 Zalogowany jako: Magazyn PL")

# 4. FILTROWANIE DANYCH TYLKO DLA WYBRANEGO AUTA
# Tworzymy widok tylko dla wybranej naczepy na wybranym evencie
df_widok = st.session_state.global_db[
    (st.session_state.global_db['Event'] == wybrany_event) & 
    (st.session_state.global_db['Naczepa'] == wybrana_naczepa)
]

# 5. NAGŁÓWEK I KPI (Zaktualizowane pod konkretne auto)
st.title(f"🌍 {wybrany_event} | Auto: {wybrana_naczepa.split(' ')[0]}")
st.markdown("---")

zajete_rzedy = len(df_widok)
wolne_rzedy = 15 - zajete_rzedy 

col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
col_kpi1.metric("Zajęte Rzędy (To auto)", f"{zajete_rzedy} / 15", f"{round((zajete_rzedy/15)*100)}% zapełnienia")
col_kpi2.metric("Projekty w środku", len(df_widok['Projekt'].unique()))
if zajete_rzedy == 0:
    col_kpi3.metric("Status Naczepy", "PUSTA / PODSTAWIONA")
elif zajete_rzedy >= 13:
    col_kpi3.metric("Status Naczepy", "GOTOWA DO DROGI")
else:
    col_kpi3.metric("Status Naczepy", "W TRAKCIE ZAŁADUNKU")

st.markdown("---")

# 6. GŁÓWNY UKŁAD STRONY
col_form, col_wiz = st.columns([1, 2])

with col_form:
    st.subheader("⚡ Panel Załadunku")
    with st.form("add_row_form", clear_on_submit=True):
        wybrany_projekt = st.selectbox("Wybierz Projekt", list(projekty_slownik.keys()))
        uwagi = st.text_input("Zawartość / Uwagi", placeholder="np. Wózek widłowy z prawej")
        ostroznie = st.checkbox("⚠️ Uwaga (Szkło / Elementy luźne)")
        
        submitted = st.form_submit_button("➕ DODAJ RZĄD", use_container_width=True)
        
        if submitted:
            nowy_rzad = len(df_widok) + 1
            nowe_dane = pd.DataFrame([{
                'Event': wybrany_event,             # <-- Zapisujemy wybrany event!
                'Naczepa': wybrana_naczepa,         # <-- Zapisujemy konkretne auto!
                'Rząd': nowy_rzad,
                'Projekt': wybrany_projekt.split(" - ")[0],
                'Hala': projekty_slownik[wybrany_projekt],
                'Uwagi': uwagi,
                'Ostrożnie': ostroznie
            }])
            # Dopisujemy do GLOBALNEJ bazy danych
            st.session_state.global_db = pd.concat([st.session_state.global_db, nowe_dane], ignore_index=True)
            st.rerun()

    if st.button("🗑️ Wyczyść TO auto"):
        # Usuwamy z globalnej bazy tylko wpisy dla tego konkretnego auta i eventu
        mask = ~((st.session_state.global_db['Event'] == wybrany_event) & (st.session_state.global_db['Naczepa'] == wybrana_naczepa))
        st.session_state.global_db = st.session_state.global_db[mask]
        st.rerun()

with col_wiz:
    st.subheader("📡 Mapa Naczepy")
    
    if df_widok.empty:
        st.info("To auto jest jeszcze puste. Rozpocznij załadunek.")
    else:
        kolory = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        # Kolory muszą być spójne dla WSZYSTKICH naczep, więc liczymy je z global_db
        projekty = st.session_state.global_db['Projekt'].unique()
        mapa_kolorow = {proj: kolory[i % len(kolory)] for i, proj in enumerate(projekty)}

        fig = go.Figure()

        for idx, row in df_widok.iterrows():
            kolor = mapa_kolorow[row['Projekt']]
            ikona = "⚠️ " if row['Ostrożnie'] else ""
            opis = f"Rząd {row['Rząd']} | {ikona}Proj: {row['Projekt']} (Hala {row['Hala']})<br>{row['Uwagi']}"
            
            fig.add_trace(go.Bar(
                x=[1], 
                y=[1], 
                name=f"{row['Projekt']}",
                orientation='v',
                marker=dict(color=kolor, line=dict(color='white', width=2)),
                text=opis,
                textposition='inside',
                insidetextanchor='middle',
                hoverinfo='text'
            ))

        fig.update_layout(
            title="Widok z góry (Góra = Kabina, Dół = Drzwi)",
            barmode='stack',
            showlegend=False,
            height=600,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, autorange='reversed'), 
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)

# 7. LISTA ROZŁADUNKOWA NA DOLE STRONY
st.markdown("---")
st.subheader(f"📋 Raport Rozładunkowy: {wybrana_naczepa}")
if not df_widok.empty:
    df_rozladunek = df_widok.iloc[::-1].reset_index(drop=True)
    # Ukrywamy kolumny Event i Naczepa w raporcie (bo są oczywiste z kontekstu)
    st.dataframe(
        df_rozladunek[['Rząd', 'Projekt', 'Hala', 'Uwagi', 'Ostrożnie']], 
        use_container_width=True,
        column_config={"Ostrożnie": st.column_config.CheckboxColumn("Wymaga uwagi", default=False)}
    )
