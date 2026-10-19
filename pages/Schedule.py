import pandas as pd
import Ghant_fac
import scheduler_fac
import Project_Fac
import dash
from dash import Dash, html, dcc,Input, Output, State, callback
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import datetime
import base64
import io
import os
import json
import networkx as nx
from pathlib import Path
import shutil
import json

dash.register_page(__name__, path="/schedule", name="Schedule")

ROOT = Path(__file__).resolve().parent.parent
config_file = ROOT / "config.json"
default_file = ROOT / "config.default.json"

if not config_file.exists():
    shutil.copy(default_file, config_file)

with open(config_file, "r") as f:
    config = json.load(f)

project_store = Path(config["project_store"])


Schedule_df = pd.DataFrame(columns=["Task Number", "Description", "Planned Start", "Planned End","Duration", "Actual Start", "Actual End", "Responsible Party", "Completion", "Status", "Notes","Dependencies"])
ghantt_df = pd.DataFrame(columns=["Task Number", "Description", "Planned Start", "Planned End","Duration", "Actual Start", "Actual End", "Responsible Party", "Completion", "Status", "Notes","Dependencies"])

metadata_panel = html.Div(
    id="project-metadata-panel",
    style={"padding": "10px", "border": "1px solid #ccc", "margin-bottom": "15px"},
    children=[
        html.Div([
            html.Label("Client"),
            dcc.Input(id="meta-client", type="text", placeholder="Client", style={"width": "100%"})
        ]),
        html.Div([
            html.Label("Lead Engineer"),
            dcc.Input(id="meta-lead-engineer", type="text", placeholder="Lead Engineer", style={"width": "100%"})
        ]),
        html.Div([
            html.Label("Project Manager"),
            dcc.Input(id="meta-pm", type="text", placeholder="Project Manager", style={"width": "100%"})
        ]),
        html.Div([
            html.Label("Client Lead"),
            dcc.Input(id="meta-client-lead", type="text", placeholder="Client Lead", style={"width": "100%"})
        ]),
        html.Div([
            html.Label("Project Number"),
            dcc.Input(id="meta-project-number", type="text", placeholder="Project Number", style={"width": "100%"})
        ]),
        html.Div([
            html.Label("Revision"),
            dcc.Input(id="meta-revision", type="text", placeholder="Revision", style={"width": "100%"})
        ]),
        html.Div([
            html.Label("Start Date"),
            dcc.Input(id="meta-start-date", type="text", placeholder="YYYY-MM-DD", style={"width": "100%"})
        ]),
        html.Div([
            html.Label("Last Updated"),
            dcc.Input(id="meta-last-updated", type="text", placeholder="YYYY-MM-DD", style={"width": "100%"})
        ]),
    ]
)




layout = html.Div([
    html.Div(
        
    dcc.Dropdown(
        id="project-selector",
        options=[{"label": p, "value": p} for p in Project_Fac.Project_Factory.list_projects(project_store)],
        placeholder="Select a project"
        ),style={"width": "300px"}),
    metadata_panel,
    html.H2("Project Schedule"),
    dcc.Graph(id="Schedule_gantt-chart", figure = Ghant_fac.build_gantt_from_df(ghantt_df)),
    html.Div(
            className="grid-container",
            children=[
                html.H2("Task Table", className="section-title"),
                Ghant_fac.build_grid(Schedule_df, "Schedule")
            ]
        ),
    html.Div([
        html.H4("Critical Path"),
        html.Div(id="critical-path-text", style={"fontWeight": "bold", "marginBottom": "10px"}),
        html.Div(id="critical-path-duration")
        ]),
    html.Br(),
    dcc.Graph(
        id="dependency-graph",
        style={"display": "none"}  # hidden until CPM runs
    ),
    html.Br(),
    dbc.Container(
    [
        # --- Row 1: Task actions ---
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button("New Task", id="New_Task_BTN", color="primary", className="w-100"),
                    width="auto"
                ),
                dbc.Col(
                    dbc.Button("Refresh Chart", id="refreh_Chart", color="secondary", className="w-100"),
                    width="auto"
                ),
                dbc.Col(
                    dbc.Button("Compute Critical Path", id="Compute_Critical_Path", color="secondary", className="w-100"),
                    width="auto"
                ),
            ],
            className="mb-3"
        ),

        # --- Row 2: File actions ---
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button("Download Table", id="download_Table", color="primary", className="w-100"),
                    width="auto"
                ),
                dbc.Col(
                    dcc.Upload(
                        id="upload_schedule",
                        children=dbc.Button("Load Schedule", color="info", className="w-100"),
                        multiple=False,
                        style={"display": "inline-block"}
                    ),
                    width="auto"
                ),
                dcc.Download(id="download-schedule"),
            ],
            className="mb-3"
        ),

        # --- Row 3: Project actions ---
        dbc.Row(
            [
                dbc.Col(
                    dcc.Input(
                        id="new-project-name",
                        type="text",
                        placeholder="Project name",
                    ),
                    width=1
                ),
                dbc.Col(
                    dbc.Button("Create Project", id="create-project-btn", color="success", className="w-100"),
                    width="auto"
                ),
                dbc.Col(
                    dbc.Button("Save Project Files", id="Save-project-btn", color="warning", className="w-100"),
                    width="auto"
                ),
            ],
            className="mb-3"
        ),
    ],
    fluid=True
)

        


])



@callback(
    Output("Schedule_task-grid", "rowData"),
    Output("Schedule_gantt-chart", "figure", allow_duplicate=True),
    Input("Schedule_task-grid", "cellValueChanged"),
    State("Schedule_task-grid", "rowData"),
    Input("New_Task_BTN", "n_clicks"),
    prevent_initial_call=True
)
def update_grid(cell_event, rows, add_clicks):
    
    #print("rows:", rows)
    #print("type:", type(rows))


    ctx = dash.callback_context
    trigger = ctx.triggered[0]["prop_id"]
    #print("trigger:", trigger)
    # -----------------------------
    # 1. APPLY THE EDIT TO ROWDATA
    # -----------------------------
    # if trigger.startswith("Schedule_task-grid"):
    #     if cell_event:
    #         rowIndex = cell_event["rowIndex"]
    #         colId = cell_event["colId"]
    #         newValue = cell_event["newValue"]

    #         print(f"Applying edit: row {rowIndex}, col {colId}, value {newValue}")
    #         rows[rowIndex][colId] = newValue

    # -----------------------------
    # 2. ADD NEW TASK
    # -----------------------------
    if trigger.startswith("New_Task_BTN"):
        #print("button triggered")
        #print(rows)

        df = pd.DataFrame(rows)
        next_id = 1 if df.empty else df["Task Number"].max() + 1

        rows.append({
            "Task Number": next_id,
            "Description": "",
            "Planned Start": "",
            "Planned End": "",
            "Duration": "",
            "Actual Start": "",
            "Actual End": "",
            "Responsible Party": "",
            "Completion": "",
            "Status": "",
            "Notes": "",
            "Dependencies": ""
        })

    # -----------------------------
    # 3. RECOMPUTE SCHEDULE LOGIC
    # -----------------------------
    df = pd.DataFrame(rows)

    # Recalculate schedule only if all rows have Planned Start + Duration
    rows = scheduler_fac.SimpleTask.recompute_end_dates(rows)
    rows = scheduler_fac.SimpleTask.apply_full_dependency_schedule(rows)

    # # Apply dependency scheduling
    # if len(df) > 2 and all(
    #     r.get("Planned Start") not in (None, "", []) and
    #     r.get("Duration") not in (None, "", [])
    #     for r in rows
    # ):
    #     

    # -----------------------------
    # 4. UPDATE GANTT CHART
    # -----------------------------
    df = pd.DataFrame(rows)
    try:
        fig = Ghant_fac.build_gantt_from_df(df)
    except:
        fig = None

    return rows, fig





@callback(
    Output("download-schedule", "data"),
    Input("download_Table", "n_clicks"),
    State("Schedule_task-grid", "rowData"),
    prevent_initial_call=True
)
def download_schedule(n, rows):
    df = pd.DataFrame(rows)
    return dcc.send_data_frame(df.to_excel, "schedule.xlsx", index=False)

@callback(
    Output("Schedule_gantt-chart", "figure",allow_duplicate=True),
    Input("refreh_Chart", "n_clicks"),
    State("Schedule_task-grid", "rowData"),
    prevent_initial_call=True
)
def manual_update_chart(n, rows):
    df = pd.DataFrame(rows)
    fig = Ghant_fac.build_gantt_from_df(df)

    return fig

@callback(
    Output("Schedule_task-grid", "rowData",allow_duplicate=True),
    Output("Schedule_gantt-chart", "figure",allow_duplicate=True),
    Input("upload_schedule", "contents"),
    prevent_initial_call=True
)
def load_schedule(contents):
    if contents is None:
        raise PreventUpdate

    # Decode base64
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    # Read Excel into DataFrame
    df = pd.read_excel(io.BytesIO(decoded))

    # Convert DF → AG Grid rows
    rows = df.to_dict("records")

    # Rebuild Gantt chart
    fig = Ghant_fac.build_gantt_from_df(df)

    return rows, fig


@callback(
    Output("project-selector","value"),
    Output("project-selector", "options"),    
    Input("create-project-btn", "n_clicks"),
    State("Schedule_task-grid", "rowData"),
    State("new-project-name", "value"),
    prevent_initial_call=True
)
def save_New_project_data(n, schedule_rows, project_name):
    schedule_df = pd.DataFrame(schedule_rows)
    if schedule_df.empty:
            #print("Empty")
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

    last_updated_new = datetime.datetime.today().isoformat()
    metadata = {
        "Client": "",
        "Lead Engineer": "",
        "Project Manager": "",
        "Client Lead": "",
        "Project Number": "",
        "Revision": "",
        "Start Date": "",
        "Last Updated": last_updated_new
    }



    #print(project_name)
    Project_Fac.Project_Factory.create_project_folder(project_store, project_name)
    Project_Fac.Project_Factory.save_project(project_store, project_name, schedule_df, metadata)

    projects = Project_Fac.Project_Factory.list_projects(project_store)


    return project_name,projects

@callback(
    Input("Save-project-btn", "n_clicks"),
    State("meta-client", "value"),
    State("meta-lead-engineer", "value"),
    State("meta-pm", "value"),
    State("meta-client-lead", "value"),
    State("meta-project-number", "value"),
    State("meta-revision", "value"),
    State("meta-start-date", "value"),
    State("meta-last-updated", "value"),
    State("Schedule_task-grid", "rowData"),
    State("project-selector","value"),
    prevent_initial_call=True
)
def save_project_data(n_clicks,client, lead_eng, pm, client_lead, proj_num, revision, start_date, last_updated, schedule_rows, project_name):

    schedule_df = pd.DataFrame(schedule_rows)
    if schedule_df.empty:
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
    
    # Auto-set last updated to today
    last_updated_new = datetime.datetime.today().isoformat()

    # Build metadata dictionary
    metadata = {
        "Client": client,
        "Lead Engineer": lead_eng,
        "Project Manager": pm,
        "Client Lead": client_lead,
        "Project Number": proj_num,
        "Revision": revision,
        "Start Date": start_date,
        "Last Updated": last_updated_new
    }

    Project_Fac.Project_Factory.save_project(project_store, project_name, schedule_df, metadata)


@callback(
    Output("Schedule_task-grid", "rowData", allow_duplicate=True),
    Output("Schedule_gantt-chart", "figure", allow_duplicate=True),
    Output("meta-client", "value", allow_duplicate=True),
    Output("meta-lead-engineer", "value", allow_duplicate=True),
    Output("meta-pm", "value", allow_duplicate=True),
    Output("meta-client-lead", "value", allow_duplicate=True),
    Output("meta-project-number", "value", allow_duplicate=True),
    Output("meta-revision", "value", allow_duplicate=True),
    Output("meta-start-date", "value", allow_duplicate=True),
    Output("meta-last-updated", "value", allow_duplicate=True),
    Output("critical-path-text", "children"),
    Output("critical-path-duration", "children"),
    Output("dependency-graph", "figure"),
    Output("dependency-graph", "style"),
    Input("project-selector", "value"),
    prevent_initial_call=True
)
def load_selected_project(project_name):
    #print("loading project from store")
    if not project_name:
        raise PreventUpdate

    # Load schedule + metadata
    schedule_df, metadata = Project_Fac.Project_Factory.load_project(
        project_store, project_name
    )
    #print(schedule_df["Planned End"])
    #print("BEfore")
    #print(schedule_df.dtypes)

    date_cols = ["Planned Start", "Planned End", "Actual Start", "Actual End"]

    for col in date_cols:
        if col in schedule_df.columns:
            schedule_df[col] = (
                schedule_df[col]
                .astype(str)              # force everything to string
                .replace("nan", "")       # remove literal "nan"
                .replace("NaT", "")       # remove literal "NaT"
                .replace("None", "")      # remove literal "None"
                .fillna("")               # remove real NaN
            )


    schedule_df["Planned Start"] = pd.to_datetime(schedule_df["Planned Start"])
    schedule_df["Planned Start"] = schedule_df["Planned Start"].dt.strftime("%Y-%m-%d")
    schedule_df["Planned End"] = pd.to_datetime(schedule_df["Planned End"])
    schedule_df["Planned End"] = schedule_df["Planned End"].dt.strftime("%Y-%m-%d")
    schedule_df["Actual Start"] = pd.to_datetime(schedule_df["Actual Start"])
    schedule_df["Actual Start"] = schedule_df["Actual Start"].dt.strftime("%Y-%m-%d")
    schedule_df["Actual End"] = pd.to_datetime(schedule_df["Actual End"])
    schedule_df["Actual End"] = schedule_df["Actual End"].dt.strftime("%Y-%m-%d")
    
    #print(schedule_df["Planned End"])
    #print("After")
    #print(schedule_df.dtypes)


    fig = Ghant_fac.build_gantt_from_df(schedule_df.copy())

    # Extract metadata fields
    meta_client         = metadata.get("Client", "N/A")
    meta_lead_engineer  = metadata.get("Lead Engineer", "N/A")
    meta_pm             = metadata.get("Project Manager", "N/A")
    meta_client_lead    = metadata.get("Client Lead", "N/A")
    meta_project_number = metadata.get("Project Number", "N/A")
    meta_revision       = metadata.get("Revision", "N/A")
    meta_start_date     = metadata.get("Start Date", "N/A")
    meta_last_updated   = metadata.get("Last Updated", "N/A")

    #import json
    #print("JSON sent to AG Grid:")
    #print(json.dumps(schedule_df.to_dict("records"), indent=4))
    
    project_path = os.path.join(project_store, project_name)
    json_path = os.path.join(project_path, "critical_path.json")

    if os.path.exists(json_path):
        #print("file exists")
        with open(json_path, "r") as f:
            stored = json.load(f)
        stored_path = stored.get("critical_path", "")
        stored_duration = stored.get("critical_duration", "")
    else:
        #print("file doesn't exist")
        stored_path = ""
        stored_duration = ""
    try:
        graph_path = os.path.join(project_path, "dependency_graph.json")    
        with open(graph_path, "r") as f:
            data = json.load(f)

        G = nx.DiGraph()

        # Rebuild nodes
        for node in data["nodes"]:
            G.add_node(node["task"], duration=node["duration"])

        # Rebuild edges
        for edge in data["edges"]:
            G.add_edge(edge["from"], edge["to"])

        
        crit_fig = scheduler_fac.SimpleTask.build_dependency_graph_plot(G,stored_path)
    except:
        ("no data in chart")
        crit_fig=None

    # Return ALL outputs in order
    return (
        schedule_df.to_dict("records"),
        fig,
        meta_client,
        meta_lead_engineer,
        meta_pm,
        meta_client_lead,
        meta_project_number,
        meta_revision,
        meta_start_date,
        meta_last_updated,
        f"Critical Path: {stored_path}",
        f"Duration: {stored_duration} days",
        crit_fig,
        {"display": "block"}
    )

@callback(
    Output("Schedule_task-grid", "rowData", allow_duplicate=True),
    Output("critical-path-text", "children", allow_duplicate=True),
    Output("critical-path-duration", "children", allow_duplicate=True),
    Output("dependency-graph", "figure", allow_duplicate=True),
    Output("dependency-graph", "style", allow_duplicate=True),
    Input("Compute_Critical_Path", "n_clicks"),
    State("Schedule_task-grid", "rowData"),
    State("project-selector", "value"),
    prevent_initial_call=True
)
def compute_Critical_Path(n_clicks, rowData, project_name):
    schedule_df = pd.DataFrame(rowData)

    # Parse dependencies
    schedule_df["PredList"] = schedule_df["Dependencies"].apply(
        scheduler_fac.SimpleTask.extract_predecessors
    )

    # Normalize Task Number
    schedule_df["Task Number"] = schedule_df["Task Number"].astype(str).str.strip()

    # Normalize PredList
    schedule_df["PredList"] = schedule_df["PredList"].apply(
        lambda lst: [str(x).strip() for x in lst] if isinstance(lst, list) else []
    )

    # Compute CPM
    ES, EF, LS, LF, float_dict, critical_path, G = scheduler_fac.SimpleTask.compute_critical_path(schedule_df)

    # Add float + critical columns
    schedule_df["Float"] = schedule_df["Task Number"].map(float_dict)
    schedule_df["Critical"] = schedule_df["Task Number"].isin(critical_path)

    # Critical path duration = EF of last task
    critical_duration = EF[critical_path[-1]]

    # Format critical path string
    critical_path_str = " → ".join(critical_path)

    # Save critical path info to file
    save_data = {
        "critical_path": critical_path_str,
        "critical_duration": int(critical_duration)
    }
    project_path = os.path.join(project_store, project_name)
    json_path = os.path.join(project_path, "critical_path.json")
    with open(json_path, "w") as f:
        json.dump(save_data, f, indent=4)

    schedule_df["Task Number"] = schedule_df["Task Number"].astype(int)

    crit_fig = scheduler_fac.SimpleTask.build_dependency_graph_plot(G,critical_path)
    #crit_fig = scheduler_fac.SimpleTask.build_timescaled_cpm_plot(G, ES, EF, critical_path)
    #crit_fig.write_html(r"C:\Projects\dependency_graph.html")

    data = {
        "nodes": [
            {"task": n, "duration": G.nodes[n]["duration"]}
            for n in G.nodes()
        ],
        "edges": [
            {"from": u, "to": v}
            for u, v in G.edges()
        ]
    }
    
    graph_path = os.path.join(project_path, "dependency_graph.json")
    with open(graph_path, "w") as f:
        json.dump(data, f, indent=4)



    return (
        schedule_df.to_dict("records"),
        f"Critical Path: {critical_path_str}",
        f"Duration: {critical_duration} days",
        crit_fig,
        {"display": "block"}

    )
