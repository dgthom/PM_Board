import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/", name="Home")

layout = dbc.Container([
    html.H1("Project Management Tools", className="mt-4"),

    html.Hr(),

    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4("Project Review Dashboard"),
                    html.P("View KPIs, project status, risks, and summaries."),
                    dbc.Button("Go to Dashboard", href="/dashboard", color="primary")
                ])
            ], className="mb-4"),
            width=6
        ),

        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4("Schedule Builder"),
                    html.P("Build and edit project schedules with AG‑Grid + Gantt."),
                    dbc.Button("Go to Schedule", href="/schedule", color="primary")
                ])
            ], className="mb-4"),
            width=6
        ),
    ])
])
