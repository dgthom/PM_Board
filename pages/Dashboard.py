import pandas as pd
import Ghant_fac
import Project_Fac
import dash
from dash import Dash, html, dcc,Input, Output, State, callback
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import os
from pathlib import Path
import json
import shutil
dash.register_page(__name__, path="/dashboard", name="Dashboard")

ROOT = Path(__file__).resolve().parent.parent
config_file = ROOT / "config.json"
default_file = ROOT / "config.default.json"

if not config_file.exists():
    shutil.copy(default_file, config_file)

with open(config_file, "r") as f:
    config = json.load(f)
    

project_store = Path(config["project_store"])
base_path = project_store

RAIL_df = pd.DataFrame(columns = [
            "Task Number",
            "Open Date",
            "Description",
            "Priority",
            "Category",
            "Responsible Party",
            "Due Date",
            "completion",
            "Status",
            "Notes"
        ])

schedule_df=pd.DataFrame(columns = [
                "Task Number",
                "Description",
                "Planned Start",
                "Planned End",
                "Duration",
                "Actual Start",
                "Actual End",
                "Responsible Party",
                "Completion",
                "Status",
                "Notes",
                "Dependencies"
            ])

ghantt_df=pd.DataFrame(columns = [
                "Task Number",
                "Description",
                "Planned Start",
                "Planned End",
                "Duration",
                "Actual Start",
                "Actual End",
                "Responsible Party",
                "Completion",
                "Status",
                "Notes",
                "Dependencies"
            ])



figure = Ghant_fac.build_gantt_from_df(schedule_df)

dashboard_metadata_panel = html.Div(
    id="dashboard-metadata-panel",
    children=[
        html.Div(["Client: ", html.Span(id="dash-meta-client")]),
        html.Div(["Lead Engineer: ", html.Span(id="dash-meta-lead-engineer")]),
        html.Div(["Project Manager: ", html.Span(id="dash-meta-pm")]),
        html.Div(["Client Lead: ", html.Span(id="dash-meta-client-lead")]),
        html.Div(["Project Number: ", html.Span(id="dash-meta-project-number")]),
        html.Div(["Revision: ", html.Span(id="dash-meta-revision")]),
        html.Div(["Start Date: ", html.Span(id="dash-meta-start-date")]),
        html.Div(["Last Updated: ", html.Span(id="dash-meta-last-updated")]),
    ]
)



card_style = {
    "paddding": "15px",
    "borderRadius" : "10px",
    "textAlign":"center",
    "boxShadow":"0px 2px 4px rgba(0,0,0,0,0.15)"
}


# Compute KPIs
Total_tasks_Ghantt, On_track_Ghantt, Slipping_ghantt, Late_Ghantt = Ghant_fac.compute_kpis(schedule_df.copy())

def kpi_card(title, value):
    return html.Div(
        className="kpi-card",
        children=[
            html.Div(title, className="kpi-title"),
            html.Div(str(value), className="kpi-value")
        ]
    )

kpi_row = html.Div(
    className="kpi-row",
    id="kpi-row",
    children=[
        html.Div(className="kpi-card", children=[
            html.Div([
                html.H4("Total Tasks"),
                html.H2(id="kpi-total")
            ], style=card_style),
        ]),
        html.Div(className="kpi-card", children=[
            html.Div([
                html.H4("On Track"),
                html.H2(id="kpi-ontrack")
            ], style=card_style),
        ]),
        html.Div(className="kpi-card", children=[
            html.Div([
                html.H4("Slipping"),
                html.H2(id="kpi-slipping")
            ], style=card_style),
        ]),
        html.Div(className="kpi-card", children=[
            html.Div([
                html.H4("Late"),
                html.H2(id="kpi-late")
            ], style=card_style),
        ]),
    ]
)



layout = html.Div([
    html.H1("Project Status Dashboard"),
    dashboard_metadata_panel,
        html.Div(
            dcc.Dropdown(
                id="Dashboard_project_selector",
                options=[{"label": p, "value": p} for p in Project_Fac.Project_Factory.list_projects(project_store)],
                placeholder="Select a project"
                ),style={"width": "300px"}),
    dcc.Graph(id="dashboard_gantt-chart", figure = Ghant_fac.build_gantt_from_df(ghantt_df)),
    html.Br(),
    kpi_row,
    html.Br(),
    html.Div(
        className="grid-container",
        children=[
            html.H2("Task Table", className="section-title"),
            Ghant_fac.build_grid(schedule_df, "Dashboard")
        ]
    ),
    html.Br(),
    dbc.Button(
        "Save Gantt Changes",
        id="save_ghantt_table",
        color="primary",
        n_clicks =0
    ),
    html.Div(id="Ghantt_save_Status"),
    html.Br(),
    html.Div(
        className="grid-container",
        children=[
            html.H2("Action Item Table", className="section-title"),
            Ghant_fac.Rail_Table(RAIL_df),
            html.Br(),
            html.Div(
                id="notes-panel",
                children=[
                    html.H3("Additional Notes"),
                    dcc.Textarea(
                        id="Notes_editor",
                        style={
                            "width": "100%",
                            "height": "300px",
                            "backgroundColor":"#303030",
                            "color": "White",
                            "border": "1px solid #444",
                            "BorderRadius": "8px",
                            "padding": "10px",
                            "fontSize": "14px",
                            "fontfamily": "Segoe UI, sans-serif"

                        }
                    ),
                    dbc.Button(
                        "Save Notes",
                        id="Save_RAIL_Notes_btn",
                        color="primary"
                    ),
                ],
                style={
                    "display":"none"
                }
            ),
            dbc.Button(
                "New Action",
                id="New_action_btn",
                color="primary",
                style={"marginRight": "10px"}

            ),
            dbc.Button(
                "Save Action List changes",
                id="Save_Rail_Btn",
                color="primary"
            ),
            html.Div(id="Rail_Save_Status")
        ],
    ),

])

@callback(
    [
        Output("dashboard_gantt-chart", "figure")
    ],
    [
        Input("Dashboard_task-grid", "cellValueChanged"),
        State("Dashboard_task-grid", "rowData"),
    ],
    prevent_initial_call=True
    
)
def update_dashboard(change,grid_data):
    if grid_data is None:
        raise PreventUpdate


    # Convert AG-Grid data back to DataFrame
    df = pd.DataFrame(grid_data)
    df["Planned Start"] = pd.to_datetime(df["Planned Start"], errors="coerce")
    df["Planned End"]   = pd.to_datetime(df["Planned End"], errors="coerce")
    df["Actual Start"]  = pd.to_datetime(df["Actual Start"], errors="coerce")
    df["Actual End"]    = pd.to_datetime(df["Actual End"], errors="coerce")

    # Rebuild Gantt
    gantt_fig = Ghant_fac.build_gantt_from_df(df)

    return [gantt_fig]


@callback(
    Output("Ghantt_save_Status","children"),
    Input("save_ghantt_table","n_clicks"),
    State("Dashboard_task-grid","rowData"),
    State("Dashboard_project_selector", "value"),
    prevent_initial_call=True
)
def save_Ghantt_table(n_clicks,row_data,project_name):
    #print("Ghantt")
    if not n_clicks:
        raise PreventUpdate

    project_path = os.path.join(base_path, project_name)
    schedule_path = os.path.join(project_path, "schedule.xlsx")

    df=pd.DataFrame(row_data)

    df.to_excel(
        schedule_path,
        index=False)

    return "Changes Saved Succesfully"

@callback(
    Output("Rail_Save_Status","children"),
    Input("Save_Rail_Btn","n_clicks"),
    State("Rail-grid","rowData"),
    State("Dashboard_project_selector", "value"),
    prevent_initial_call=True
)
def save_RAIL_table(n_clicks,row_data,project_name):

    if not n_clicks:
        raise PreventUpdate

    df=pd.DataFrame(row_data)
    project_path = os.path.join(base_path, project_name)
    Rail_Path = os.path.join(project_path, "rail.xlsx")


    df.to_excel(
        Rail_Path,
        index=False
        )

    return "Changes Saved Succesfully"

@callback(
    Output("Notes_editor","value"),
    Output("notes-panel","style"),
    Input("Rail-grid","selectedRows"),
    prevent_initial_call=True
)
def save_notes(selected_rows):

    if not selected_rows:
        return "", {"display":"none"}

    row = selected_rows[0]

    note=row.get("Notes","")

    if note is None:
        note=""

    return(
        note,
        {
            "display":"block",
            "marginTop": "10px"
        }
    )

@callback(
    Output("Rail-grid","rowData"),
    Input("New_action_btn","n_clicks"),
    State("Rail-grid","rowData"),
    State("Dashboard_project_selector", "value"),
    prevent_initial_call=True
)
def Add_action(n_clicks,row_data,project_name):
    
    project_path = os.path.join(base_path, project_name)
    Rail_Path = os.path.join(project_path, "rail.xlsx")
    
    if row_data == []:
        RAIL_df = pd.read_excel(Rail_Path)
        new_row={
            "Task Number": 1,
            "Open Date": pd.Timestamp.today().strftime("%Y-%m-%d"),
            "Description":"",
            "Priority":"",
            "Category":"",
            "Responsible Party":"",
            "Due Date":"",
            "Completion":"",
            "Status": "New",
            "Notes":""
        }
    else:
        RAIL_df=pd.DataFrame(row_data)
        next_id = RAIL_df["Task Number"].max() +1
        new_row={
            "Task Number": next_id,
            "Open Date": pd.Timestamp.today().strftime("%Y-%m-%d"),
            "Description":"",
            "Priority":"",
            "Category":"",
            "Responsible Party":"",
            "Due Date":"",
            "Completion":"",
            "Status": "New",
            "Notes":""
        }

    RAIL_df=pd.concat(
        [RAIL_df, pd.DataFrame([new_row])],
        ignore_index=True
    )

    return RAIL_df.to_dict("records")

@callback(
    Output("Rail_Save_Status", "children", allow_duplicate=True),
    Output("Rail-grid", "rowData", allow_duplicate=True),
    Input("Save_RAIL_Notes_btn", "n_clicks"),
    State("Notes_editor", "value"),
    State("Rail-grid", "selectedRows"),
    State("Rail-grid", "rowData"),
    prevent_initial_call=True
)
def Save_notes(n_clicks, notes, selected_rows, row_data):

    if not selected_rows:
        return "Please select a row first", Dash.no_update

    selected_row = selected_rows[0]
    record_id = selected_row["Task Number"]

    df = pd.DataFrame(row_data)

    df.loc[
        df["Task Number"] == record_id,
        "Notes"
    ] = notes

    return (
        "Notes Saved",
        df.to_dict("records")
    )

@callback(
    Output("dashboard_gantt-chart", "figure",allow_duplicate=True),
    Output("Dashboard_task-grid", "rowData"),
    Output("Rail-grid", "rowData", allow_duplicate=True),
    Output("dash-meta-client", "children"),
    Output("dash-meta-lead-engineer", "children"),
    Output("dash-meta-pm", "children"),
    Output("dash-meta-client-lead", "children"),
    Output("dash-meta-project-number", "children"),
    Output("dash-meta-revision", "children"),
    Output("dash-meta-start-date", "children"),
    Output("dash-meta-last-updated", "children"),
    Output("kpi-total", "children"),
    Output("kpi-ontrack", "children"),
    Output("kpi-slipping", "children"),
    Output("kpi-late", "children"),
    Input("Dashboard_project_selector", "value"),
    prevent_initial_call=True
)
def Update_Project(project_name):
    if not project_name:
            raise PreventUpdate
    
    schedule_df, metadata = Project_Fac.Project_Factory.load_project(project_store, project_name)
    Rail_df = Project_Fac.Project_Factory.load_project_Rail(project_store, project_name)
    metadata = Project_Fac.Project_Factory.Load_META_Data(project_store, project_name)
    #print("after retrival")
    #print(schedule_df)

    fig = Ghant_fac.build_gantt_from_df(schedule_df)

    schedule_df["Planned Start"] = pd.to_datetime(schedule_df["Planned Start"])
    schedule_df["Planned Start"] = schedule_df["Planned Start"].dt.strftime("%Y-%m-%d")
    schedule_df["Planned End"] = pd.to_datetime(schedule_df["Planned End"])
    schedule_df["Planned End"] = schedule_df["Planned End"].dt.strftime("%Y-%m-%d")
    schedule_df["Actual Start"] = pd.to_datetime(schedule_df["Actual Start"])
    schedule_df["Actual Start"] = schedule_df["Actual Start"].dt.strftime("%Y-%m-%d")
    schedule_df["Actual End"] = pd.to_datetime(schedule_df["Actual End"])
    schedule_df["Actual End"] = schedule_df["Actual End"].dt.strftime("%Y-%m-%d")

    # Compute KPIs
    #print("before KPI call")
    #print(schedule_df)
    KPI_total, KPI_ontrack, KPI_slipping, KPI_Late = Ghant_fac.compute_kpis(schedule_df.copy())
    #print(KPI_total)

    
    return [
        fig,
        schedule_df.to_dict("records"),
        Rail_df.to_dict("records"),
        metadata.get("Client", "N/A"),
        metadata.get("Lead Engineer", "N/A"),
        metadata.get("Project Manager", "N/A"),
        metadata.get("Client Lead", "N/A"),
        metadata.get("Project Number", "N/A"),
        metadata.get("Revision", "N/A"),
        metadata.get("Start Date", "N/A"),
        metadata.get("Last Updated", "N/A"),
        KPI_total,
        KPI_ontrack,
        KPI_slipping,
        KPI_Late

    ]





