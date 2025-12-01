import pandas as pd
from dash import Dash, dcc, html, dash_table, Input, Output
import plotly.graph_objects as go
import os

# ======================================================
# 1. Cargar datos
# ======================================================
# Segmentos
df = pd.read_csv(r"Joinpoint-Results/Total.Export.APC.txt")
df["Significativo"] = df["PPC Significant"].map({1: "Sí", 0: "No"})

# Datos del modelo (REM y predicción)
df_fit = pd.read_csv(r"Joinpoint-Results/Total.Export.Data.txt")

# Municipios disponibles
municipios = sorted(df["municipio"].unique())

# ======================================================
# 2. Crear APP
# ======================================================
app = Dash(__name__)

app.layout = html.Div([

    html.H2("Resultados del Joinpoint del REM.", style={"text-align": "center"}),

    html.Label("Selecciona un municipio:", style={"font-weight": "bold"}),
    dcc.Dropdown(
        id="selector_municipio",
        options=[{"label": m, "value": m} for m in municipios],
        value=municipios[0],
        clearable=False
    ),
    html.Br(),

    html.Div([

        # =================== COLUMNA IZQUIERDA (65%) ===================
        html.Div([
            dcc.Graph(id="grafico_joinpoint")
        ], style={"width": "65%", "display": "inline-block", "vertical-align": "top"}),

        # =================== COLUMNA DERECHA (35%) ===================
        html.Div([

            html.H4("Resumen de Segmentos", style={"text-align": "center"}),
            dash_table.DataTable(
                id="tabla_ppc",
                columns=[
                    {"name": "Segmento", "id": "Segment"},
                    {"name": "PPC", "id": "PPC", "type": "numeric", "format": {"specifier": ".2f"}},
                    {"name": "Significativo", "id": "Significativo"}
                ],
                style_table={"width": "100%"},
                style_cell={"textAlign": "center"},
                style_header={"fontWeight": "bold", "backgroundColor": "#e6e6e6"},
            ),

            html.Br(),

            html.Div(id="cuadro_joinpoints",
                     style={
                         "background-color": "#007acc",
                         "color": "white",
                         "padding": "15px",
                         "border-radius": "8px",
                         "font-size": "20px",
                         "text-align": "center",
                         "font-weight": "bold"
                     }),

            html.Br(),

            dcc.Graph(id="grafico_ppc_seg")

        ], style={"width": "32%", "display": "inline-block",
                  "padding-left": "20px", "vertical-align": "top"}),

    ])

])

# ======================================================
# 3. CALLBACKS
# ======================================================
@app.callback(
    Output("grafico_joinpoint", "figure"),
    Output("tabla_ppc", "data"),
    Output("cuadro_joinpoints", "children"),
    Output("grafico_ppc_seg", "figure"),
    Input("selector_municipio", "value")
)
def actualizar_dashboard(municipio):

    municipio = municipio.upper()

    # ---------- Segmentos ----------
    df_m = df[df["municipio"] == municipio].copy()

    # ---------- Datos REM y modelo ----------
    df_f = df_fit[df_fit["municipio"] == municipio].copy()
    df_f = df_f.sort_values("periodo_global")

    # ======================================================
    # 1) GRAFICO PRINCIPAL JOINPOINT (Plotly)
    # ======================================================

    fig_join = go.Figure()

    # ---- puntos observados ----
    fig_join.add_trace(go.Scatter(
        x=df_f["periodo_global"],
        y=df_f["REM"],
        mode="markers",
        marker=dict(color="darkred", size=7),
        name="Observado"
    ))

    # ---- segmentos JOINPOINT ----
    colors = ["blue", "green", "red", "purple", "orange", "brown"]

    for i, row in df_m.iterrows():
        ini = row["Segment Start"]
        fin = row["Segment End"]

        tramo = df_f[(df_f["periodo_global"] >= ini) & (df_f["periodo_global"] <= fin)]

        fig_join.add_trace(go.Scatter(
            x=tramo["periodo_global"],
            y=tramo["Model"],
            mode="lines",
            line=dict(width=3, color=colors[int(row["Segment"]) % len(colors)]),
            name=f"Segmento {row['Segment']}"
        ))

    fig_join.update_layout(
        title=f"Modelo Joinpoint – {municipio}",
        xaxis_title="Periodo",
        yaxis_title="REM",
        plot_bgcolor="white",
        height=700
    )

    # ======================================================
    # 2) TABLA SEGMENTOS
    # ======================================================
    tabla = df_m[["Segment", "PPC", "Significativo"]].to_dict("records")

    # ======================================================
    # 3) CUADRO N° JOINPOINTS
    # ======================================================
    num_joinpoints = int(df_m["Model"].iloc[0])
    texto_joinpoints = f"N° Joinpoints: {num_joinpoints}"

    # ======================================================
    # 4) GRÁFICO PPC
    # ======================================================
    fig_ppc = go.Figure()

    fig_ppc.add_trace(go.Scatter(
        x=df_m["Segment"],
        y=df_m["PPC"],
        mode="markers+lines",
        marker=dict(
            size=12,
            color=df_m["PPC Significant"].map({1: "blue", 0: "orange"}),
            line=dict(width=1, color="black")
        ),
        line=dict(dash="dash", color="gray"),
        name="PPC"
    ))

    fig_ppc.add_hline(y=0, line_color="black")

    fig_ppc.update_layout(
        title=f"PPC por segmento – {municipio}",
        xaxis_title="Segmento",
        yaxis_title="PPC",
        plot_bgcolor="white",
        height=350
    )

    return fig_join, tabla, texto_joinpoints, fig_ppc


# ======================================================
# Ejecutar
# ======================================================
if __name__ == "__main__":
    app.run(debug=True)


