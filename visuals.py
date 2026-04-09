# visuals.py
import streamlit as st
import plotly.graph_objects as go

def load_ui():
    st.markdown("""
        <style>
        .stApp { background-color: #0f172a; color: white; }
        h1, h2, h3 { color: #38bdf8 !important; text-transform: uppercase; }
        div[data-testid="metric-container"] { background-color: #1e293b !important; border-left: 5px solid #38bdf8 !important; border-radius: 8px; }
        div.stButton > button:first-child { background-color: #0284c7; color: white; border-radius: 6px; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

def get_proj_color(proj_string):
    if proj_string in ["Brak", "MIX - Drobnica"]: return "#64748b"
    p_id = proj_string.split(" - ")[0]
    match = st.session_state.projects_db[st.session_state.projects_db['ID'] == str(p_id)]
    return match.iloc[0]['Kolor'] if not match.empty else "#64748b"

def draw_3d(df_auto):
    fig = go.Figure()
    W, L, H = 2.45, 13.6, 2.7
    ROW_L = L / 15

    # Podłoga i szkielet
    fig.add_trace(go.Mesh3d(x=[0, W, W, 0], y=[0, 0, L, L], z=[0, 0, 0, 0], i=[0,0], j=[1,2], k=[2,3], color='#334155', opacity=1.0))
    fig.add_trace(go.Scatter3d(x=[0,W,W,0,0,0,W,W,0,0], y=[0,0,L,L,0,0,0,L,L,0], z=[0,0,0,0,0,H,H,H,H,H], mode='lines', line=dict(color='#7dd3fc', width=4)))

    for _, row in df_auto.iterrows():
        y_s, y_e = (row['Rząd'] - 1) * ROW_L, row['Rząd'] * ROW_L - 0.05
        
        def add_box(xr, yr, zr, color, txt, lbl):
            fig.add_trace(go.Mesh3d(
                x=[xr[0], xr[0], xr[1], xr[1], xr[0], xr[0], xr[1], xr[1]],
                y=[yr[0], yr[1], yr[1], yr[0], yr[0], yr[1], yr[1], yr[0]],
                z=[zr[0], zr[0], zr[0], zr[0], zr[1], zr[1], zr[1], zr[1]],
                i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
                color=color, flatshading=True, hoverinfo='text', text=txt
            ))
            fig.add_trace(go.Scatter3d(x=[(xr[0]+xr[1])/2], y=[(yr[0]+yr[1])/2], z=[zr[1]+0.1], mode='text', text=[lbl], textfont=dict(color='white', size=10)))

        c1 = get_proj_color(row['Projekt_1'])
        n1 = row['Projekt_1'].split(" - ")[-1] if " - " in row['Projekt_1'] else row['Projekt_1']

        if "Pełny" in row['Układ']:
            add_box([0.05, W-0.05], [y_s, y_e], [0, H*0.8], c1, f"{row['Projekt_1']}<br>{row['Zawartosc_1']}", n1)
        elif "Lewa / Prawa" in row['Układ']:
            add_box([0.05, W/2-0.05], [y_s, y_e], [0, H*0.8], c1, f"{row['Projekt_1']}<br>{row['Zawartosc_1']}", n1)
            if row['Projekt_2'] != "Brak":
                add_box([W/2+0.05, W-0.05], [y_s, y_e], [0, H*0.8], get_proj_color(row['Projekt_2']), f"{row['Projekt_2']}<br>{row['Zawartosc_2']}", row['Projekt_2'].split(" - ")[-1])

    fig.update_layout(scene=dict(aspectmode='data', xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False), camera=dict(eye=dict(x=-2.5, y=-1.8, z=1.5))), margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)')
    return fig
