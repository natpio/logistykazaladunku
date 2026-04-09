# visuals.py
import streamlit as st
import plotly.graph_objects as go

def load_css():
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        .stApp { background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI', sans-serif; }
        h1, h2, h3 { color: #38bdf8 !important; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
        div[data-testid="metric-container"] { background-color: #1e293b !important; border-left: 5px solid #38bdf8 !important; border-radius: 8px !important; padding: 15px !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important; }
        div[data-testid="metric-container"] label { color: #94a3b8 !important; font-size: 1.1rem !important; }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #ffffff !important; font-weight: bold !important; }
        div.stButton > button:first-child { background-color: #0284c7; color: white; border: none; border-radius: 6px; font-weight: bold; transition: all 0.2s; height: 50px; }
        div.stButton > button:first-child:hover { background-color: #38bdf8; color: #0f172a; }
        section[data-testid="stSidebar"] { background-color: #1e293b !important; }
        section[data-testid="stSidebar"] label { color: #f8fafc !important; font-weight: 600 !important; }
        span[data-baseweb="tag"] { background-color: #0284c7 !important; color: white !important; border-radius: 4px; }
        </style>
    """, unsafe_allow_html=True)

def get_project_color(project_string):
    if project_string in ["Brak", "MIX - Drobnica"]: return "#64748b"
    proj_id = project_string.split(" - ")[0]
    match = st.session_state.projects_db[st.session_state.projects_db['ID'] == str(proj_id)]
    if not match.empty: return match.iloc[0]['Kolor']
    return "#64748b"

def render_3d_trailer(df_current_auto):
    fig3d = go.Figure()
    W, L, H = 2.45, 13.6, 2.7
    ROW_L = L / 15

    fig3d.add_trace(go.Mesh3d(x=[0, W, W, 0], y=[0, 0, L, L], z=[0, 0, 0, 0], i=[0, 0], j=[1, 2], k=[2, 3], color='#334155', opacity=1.0, hoverinfo='skip'))
    fig3d.add_trace(go.Scatter3d(x=[0, W, W, 0, 0, 0, W, W, 0, 0], y=[0, 0, L, L, 0, 0, 0, L, L, 0], z=[0, 0, 0, 0, 0, H, H, H, H, H], mode='lines', line=dict(color='#7dd3fc', width=4), hoverinfo='skip'))

    def draw_block(fig, x_range, y_range, z_range, color, hover_text, label_text):
        x = [x_range[0], x_range[0], x_range[1], x_range[1], x_range[0], x_range[0], x_range[1], x_range[1]]
        y = [y_range[0], y_range[1], y_range[1], y_range[0], y_range[0], y_range[1], y_range[1], y_range[0]]
        z = [z_range[0], z_range[0], z_range[0], z_range[0], z_range[1], z_range[1], z_range[1], z_range[1]]
        i, j, k = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
        fig.add_trace(go.Mesh3d(x=x, y=y, z=z, i=i, j=j, k=k, color=color, opacity=1.0, hoverinfo='text', text=hover_text, flatshading=True, lighting=dict(ambient=0.8, diffuse=0.9, roughness=0.5, specular=0.2)))
        x_center, y_center, z_center = (x_range[0] + x_range[1]) / 2, (y_range[0] + y_range[1]) / 2, z_range[1] + 0.1
        fig.add_trace(go.Scatter3d(x=[x_center], y=[y_center], z=[z_center], mode='text', text=[label_text], textfont=dict(color='white', size=11, family="Arial"), textposition='middle center', hoverinfo='skip', showlegend=False))

    for idx, row in df_current_auto.iterrows():
        y_start, y_end = (row['Rząd'] - 1) * ROW_L, row['Rząd'] * ROW_L - 0.05 
        p1, p2 = str(row['Projekt_1']), str(row['Projekt_2'])
        z1, z2 = str(row['Zawartosc_1']), str(row['Zawartosc_2'])
        c1, c2 = get_project_color(p1), get_project_color(p2)
        
        nazwa_p1 = p1.split(" - ")[-1] if " - " in p1 else p1
        nazwa_p2 = p2.split(" - ")[-1] if " - " in p2 else p2

        h_base = f"<b>RZĄD {row['Rząd']}</b><br>Układ: {row['Układ']}<br>Uwagi: {row['Uwagi']}"
        lab_1 = f"<b>{nazwa_p1}</b><br>📦" if z1 != "Nie określono" else f"<b>{nazwa_p1}</b>"
        lab_2 = f"<b>{nazwa_p2}</b><br>📦" if z2 != "Nie określono" else f"<b>{nazwa_p2}</b>"

        if "Pełny" in row['Układ']: draw_block(fig3d, [0.05, W-0.05], [y_start, y_end], [0, H*0.8], c1, f"{h_base}<br>Proj: {p1}<br>{z1}", lab_1)
        elif "Lewa / Prawa" in row['Układ']:
            draw_block(fig3d, [0.05, W/2-0.05], [y_start, y_end], [0, H*0.8], c1, f"{h_base}<br>[L] Proj: {p1}<br>{z1}", lab_1)
            if p2 != "Brak": draw_block(fig3d, [W/2+0.05, W-0.05], [y_start, y_end], [0, H*0.8], c2, f"{h_base}<br>[P] Proj: {p2}<br>{z2}", lab_2)
        elif "Dół / Góra" in row['Układ']:
            draw_block(fig3d, [0.05, W-0.05], [y_start, y_end], [0, H*0.4], c1, f"{h_base}<br>[DÓŁ] Proj: {p1}<br>{z1}", lab_1)
            if p2 != "Brak": draw_block(fig3d, [0.05, W-0.05], [y_start, y_end], [H*0.4+0.05, H*0.8], c2, f"{h_base}<br>[GÓRA] Proj: {p2}<br>{z2}", lab_2)

    fig3d.update_layout(scene=dict(aspectmode='data', xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False), camera=dict(eye=dict(x=-2.5, y=-1.8, z=1.5))), margin=dict(l=0, r=0, t=0, b=0), height=700, showlegend=False, paper_bgcolor='rgba(0,0,0,0)')
    return fig3d
