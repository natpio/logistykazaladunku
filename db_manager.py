# db_manager.py
import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from config import WYMAGANE_KOLUMNY

def init_db():
    """Inicjalizuje połączenie z Google Sheets i stan aplikacji"""
    if 'app_mode' not in st.session_state:
        st.session_state.app_mode = 'menu' 

    conn = st.connection("gsheets", type=GSheetsConnection)

    # Ładunek z chmury
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
        except Exception as e:
            st.error(f"Błąd połączenia z Google Sheets. ({e})")
            st.session_state.cargo_db = pd.DataFrame(columns=WYMAGANE_KOLUMNY)

    # Baza Logistyki (Słowniki)
    if 'events_list' not in st.session_state:
        st.session_state.events_list = ["Hannover Messe 2026", "ISE Barcelona 2026"]
    if 'fleet_list' not in st.session_state:
        st.session_state.fleet_list = ["PO 1234A (Mega)", "WA 9876C (Standard)", "KR 5555X (Standard)"]
    if 'projects_db' not in st.session_state:
        st.session_state.projects_db = pd.DataFrame([
            {"Event": "Hannover Messe 2026", "ID": "21374", "Nazwa": "Hannover Główny", "Kolor": "#0ea5e9"},
            {"Event": "Hannover Messe 2026", "ID": "21375", "Nazwa": "Stoisko BMW", "Kolor": "#f59e0b"},
            {"Event": "ISE Barcelona 2026", "ID": "24001", "Nazwa": "Samsung", "Kolor": "#ef4444"}
        ])

def sync_to_google_sheets():
    """Wysyła aktualną bazę ładunku do chmury"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet="ZALADUNEK", data=st.session_state.cargo_db)
    except Exception as e:
        st.error(f"Nie udało się zapisać w Google Sheets: {e}")

def aggregate_equipment(df_auto):
    """Zlicza ilość skrzyń dla danego auta"""
    summary = []
    for _, row in df_auto.iterrows():
        for p_col, z_col in [('Projekt_1', 'Zawartosc_1'), ('Projekt_2', 'Zawartosc_2')]:
            proj, zaw = row[p_col], row[z_col]
            if proj != "Brak" and zaw != "Nie określono" and pd.notna(zaw):
                items = str(zaw).split(", ")
                for item in items:
                    parts = item.split(": ")
                    if len(parts) == 2:
                        try:
                            summary.append({"Projekt": proj, "Sprzęt": parts[0].strip(), "Ilość skrzyń": int(parts[1].strip())})
                        except ValueError:
                            pass
    if summary:
        df_sum = pd.DataFrame(summary)
        return df_sum.groupby(["Projekt", "Sprzęt"])["Ilość skrzyń"].sum().reset_index()
    return pd.DataFrame(columns=["Projekt", "Sprzęt", "Ilość skrzyń"])
