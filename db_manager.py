# db_manager.py
import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from config import WYMAGANE_KOLUMNY

def init_db():
    """Inicjalizacja połączenia i słowników biurowych"""
    if 'app_mode' not in st.session_state:
        st.session_state.app_mode = 'menu'

    conn = st.connection("gsheets", type=GSheetsConnection)

    # Pobieranie ładunku
    if 'cargo_db' not in st.session_state:
        try:
            df = conn.read(worksheet="ZALADUNEK", ttl=0).dropna(how='all')
            # Auto-naprawa kolumn
            for col in WYMAGANE_KOLUMNY:
                if col not in df.columns:
                    df[col] = "Nie określono"
            st.session_state.cargo_db = df
        except:
            st.session_state.cargo_db = pd.DataFrame(columns=WYMAGANE_KOLUMNY)

    # Inicjalizacja słowników biurowych w pamięci
    if 'events_list' not in st.session_state:
        st.session_state.events_list = ["Hannover Messe 2026", "ISE Barcelona 2026"]
    if 'fleet_db' not in st.session_state:
        st.session_state.fleet_db = pd.DataFrame([
            {"Event": "Hannover Messe 2026", "Auto": "PO 1234A (Mega)"},
            {"Event": "ISE Barcelona 2026", "Auto": "WA 9876C (Standard)"}
        ])
    if 'projects_db' not in st.session_state:
        st.session_state.projects_db = pd.DataFrame([
            {"Event": "Hannover Messe 2026", "ID": "21374", "Nazwa": "Hannover Główny", "Kolor": "#0ea5e9"}
        ])

def sync_db():
    """Zapis do Google Sheets"""
    conn = st.connection("gsheets", type=GSheetsConnection)
    conn.update(worksheet="ZALADUNEK", data=st.session_state.cargo_db)

def aggregate_equipment(df_auto):
    """Sumowanie sprzętu z 'Nazwa: Ilość' na liczby"""
    summary = []
    for _, row in df_auto.iterrows():
        for z_col in ['Zawartosc_1', 'Zawartosc_2']:
            val = str(row[z_col])
            if ":" in val:
                for item in val.split(", "):
                    if ": " in item:
                        name, qty = item.split(": ")
                        summary.append({"Sprzęt": name, "Ilość": int(qty)})
    if summary:
        return pd.DataFrame(summary).groupby("Sprzęt")["Ilość"].sum().reset_index()
    return pd.DataFrame(columns=["Sprzęt", "Ilość"])
