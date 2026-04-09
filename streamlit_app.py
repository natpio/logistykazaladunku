import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. KONFIGURACJA STRONY (Wygląd PRO)
st.set_page_config(
    page_title="SQM Logistics | Trailer Planner",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Wymuszenie nowoczesnego czcionki i ukrycie znaków wodnych Streamlit
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stMetric {background-color: #f0f2f6; padding: 10px; border-radius: 8px;}
    </style>
""", unsafe_allow_html=True)

# 2. STAN APLIKACJI (Symulacja Bazy Danych)
if 'trailer_data' not in st.session_state:
    st.session_state.trailer_data = pd.DataFrame(columns=['Rząd', 'Projekt', 'Hala', 'Uwagi', 'Ostrożnie'])

# Symulacja słownika projektów
projekty_slownik = {
    "21374 - Hannover Messe": "Hala 2",
    "24001 - Samsung": "Hala 3A",
    "24552 - Budimex": "Hala 5",
    "MIX - Drobnica": "Różne"
}

# 3. INTERFEJS - NAGŁÓWEK I KPI
st.title("🚛 SQM System Załadunkowy")
st.markdown("---")

# Wskaźniki na samej górze (Efekt WOW dla zarządu)
col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
zajete_rzedy = len(st.session_state.trailer_data)
wolne_rzedy = 15 - zajete_rzedy # Zakładamy 15 rzędów na standardowej naczepie

col_kpi1.metric("Zajęte Rzędy", f"{zajete_rzedy} / 15", f"{round((zajete_rzedy/15)*100)}% zapełnienia")
col_kpi2.metric("Projekty na naczepie", len(st.session_state.trailer_data['Projekt'].unique()))
col_kpi3.metric("Status Naczepy", "GOTOWA DO DROGI" if zajete_rzedy >= 13 else "W TRAKCIE ZAŁADUNKU")

st.markdown("---")

# 4. GŁÓWNY UKŁAD STRONY (Podział na Panel sterowania i Wizualizację)
col_form, col_wiz = st.columns([1, 2])

with col_form:
    st.subheader("⚡ Szybki Załadunek")
    with st.form("add_row_form", clear_on_submit=True):
        wybrany_projekt = st.selectbox("Wybierz Projekt (Skanuj lub wpisz)", list(projekty_slownik.keys()))
        uwagi = st.text_input("Zawartość / Uwagi (Opcjonalnie)", placeholder="np. Wózek widłowy z prawej")
        ostroznie = st.checkbox("⚠️ Uwaga (Szkło / Elementy luźne)")
        
        submitted = st.form_submit_button("➕ ZATWIERDŹ RZĄD (Spnij Pasy)", use_container_width=True)
        
        if submitted:
            nowy_rzad = len(st.session_state.trailer_data) + 1
            nowe_dane = pd.DataFrame([{
                'Rząd': nowy_rzad,
                'Projekt': wybrany_projekt.split(" - ")[0],
                'Hala': projekty_slownik[wybrany_projekt],
                'Uwagi': uwagi,
                'Ostrożnie': ostroznie
            }])
            st.session_state.trailer_data = pd.concat([st.session_state.trailer_data, nowe_dane], ignore_index=True)
            st.rerun()

    if st.button("🗑️ Resetuj Naczepę (Nowy Załadunek)"):
        st.session_state.trailer_data = pd.DataFrame(columns=['Rząd', 'Projekt', 'Hala', 'Uwagi', 'Ostrożnie'])
        st.rerun()

with col_wiz:
    st.subheader("📡 Cyfrowy Bliźniak Naczepy")
    
    df = st.session_state.trailer_data
    
    if df.empty:
        st.info("Naczepa jest pusta. Rozpocznij załadunek dodając pierwszy rząd od strony kabiny.")
    else:
        # Automatyczne przypisywanie kolorów PRO
        kolory = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        projekty = df['Projekt'].unique()
        mapa_kolorow = {proj: kolory[i % len(kolory)] for i, proj in enumerate(projekty)}

        # Rysowanie naczepy za pomocą Plotly
        fig = go.Figure()

        for idx, row in df.iterrows():
            kolor = mapa_kolorow[row['Projekt']]
            ikona = "⚠️ " if row['Ostrożnie'] else ""
            opis = f"Rząd {row['Rząd']} | {ikona}Proj: {row['Projekt']} (Hala {row['Hala']})<br>{row['Uwagi']}"
            
            fig.add_trace(go.Bar(
                x=[1], # Stała szerokość naczepy
                y=[1], # Stała grubość rzędu
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
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, autorange='reversed'), # Odwracamy, by rząd 1 był na górze
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)

# 5. LISTA ROZŁADUNKOWA NA DOLE STRONY
st.markdown("---")
st.subheader("📋 Kolejność Rozładunku (Od drzwi do kabiny)")
if not df.empty:
    # Odwracamy DataFrame, bo rozładowujemy od ostatniego rzędu
    df_rozladunek = df.iloc[::-1].reset_index(drop=True)
    st.dataframe(
        df_rozladunek, 
        use_container_width=True,
        column_config={
            "Ostrożnie": st.column_config.CheckboxColumn("Wymaga uwagi", default=False)
        }
    )
