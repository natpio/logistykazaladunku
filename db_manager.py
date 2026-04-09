# db_manager.py
import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from config import WYMAGANE_KOLUMNY

def init_db():
    """Inicjalizuje stan aplikacji i pobiera dane z Google Sheets"""
    if 'app_mode' not in st.session_state:
        st.session_state.app_mode = 'menu' 

    conn = st.connection("gsheets", type=GSheetsConnection)

    if 'cargo_db' not in st.session_state:
        try:
            df_sheet = conn.read(worksheet="ZALADUNEK", ttl=0)
            df_sheet = df_sheet.dropna(how='all')
            if df_sheet.empty:
                st.session_state.cargo_db = pd.DataFrame(columns=WYMAGANE_KOLUMNY)
            else:
                for kol in WYMAGANE_KOLUMNY:
                    if kol not in df_sheet.columns:
                        df_sheet[kol] = "Nie określono"
                st.session_state.cargo_db = df_sheet
        except:
            st.session_state.cargo_db = pd.DataFrame(columns=WYMAGANE_KOLUMNY)

    # Inicjalizacja słowników biurowych (jeśli puste)
    if 'events_list' not in st.session_state:
        st.session_state.events_list = ["Hannover Messe 2026", "ISE Barcelona 2026"]
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
    """Wysyła aktualny stan cargo_db do Google Sheets"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet="ZALADUNEK", data=st.session_state.cargo_db)
    except Exception as e:
        st.error(f"Błąd synchronizacji: {e}")

def aggregate_equipment(df_auto):
    """Sumuje ilości sprzętu dla techników"""
    summary = []
    for _, row in df_auto.iterrows():
        for p_col, z_col in [('Projekt_1', 'Zawartosc_1'), ('Projekt_2', 'Zawartosc_2')]:
            proj, zaw = row[p_col], row[z_col]
            if proj != "Brak" and zaw != "Nie określono" and pd.notna(zaw):
                items = str(zaw).split(", ")
                for item in items:
                    if ": " in item:
                        parts = item.split(": ")
                        try:
                            summary.append({
                                "Projekt": proj, 
                                "Sprzęt": parts[0].strip(), 
                                "Ilość skrzyń": int(parts[1].strip())
                            })
                        except: pass
    if summary:
        df_sum = pd.DataFrame(summary)
        return df_sum.groupby(["Projekt", "Sprzęt"])["Ilość skrzyń"].sum().reset_index()
    return pd.DataFrame(columns=["Projekt", "Sprzęt", "Ilość skrzyń"])
