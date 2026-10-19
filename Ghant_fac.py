import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
from dash_ag_grid import AgGrid
from pandas.api.types import is_datetime64_any_dtype as is_datetime
import numpy as np
import traceback
import sys

#print("Dash AG Grid version:", AgGrid.__version__)
#print("AG Grid version:", AgGrid.grid_version)

def status_style(params):
    status = params.value

    if status in ("Not Started", "New"):
        return {"backgroundColor": "#f0f0f0"}  # grey
    if status in ("In Progress", "Deferred"):
        return {"backgroundColor": "#fff3cd"}  # amber
    if status == "Blocked":
        return {"backgroundColor": "#f8d7da"}  # red
    if status in ("Complete", "To Be Closed"):
        return {"backgroundColor": "#d4edda"}  # green

    return {}

def build_gantt_from_df(df):
    
    # Data prep
    df["Actual End Plot"] = df["Actual End"].fillna(
    pd.Timestamp.today().normalize()
    )


    fig = go.Figure()
    

    date_cols=[
        "Planned Start",
        "Planned End",
        "Actual Start",
        "Actual End"
    ]

    for col in date_cols:
        if is_datetime(df[col]):
            print("Already a date")
        else:
            df[col] = pd.to_datetime(
                df[col],
                format="%Y-%m-%d",
                errors="coerce"
            )

    df=df.copy()

    df["Actual End Plot"] = (
        df["Actual End"].fillna(pd.Timestamp.today().normalize())
    )
    
    #Slip

    try:
        df["Slip Days"] = (
            df["Actual End Plot"] - df["Planned End"]
        ).dt.days
    except:
        df["Slip Days"] = 0
        print("Slip failed")

    df["Colour"] = np.select(
        [
            df["Slip Days"] >5,
            df["Slip Days"] >0
        ],
        [
            "#e74c3c", #Late
            "#f39c12" #warning
        ],
        default="#00bc8c" #Normal
    )
    
    #Chart

    for _, row in df.iterrows():
        #Planned dates
        try:
            fig.add_trace(
                go.Scatter(
                     x=[
                        row["Planned Start"],
                        row["Planned End"]
                        ],
                        y=[
                            row["Description"],
                            row["Description"]
                        ],
                        mode = "lines",
                        line = dict(
                            color="rgba(180,180,180,0.6)",
                            width=6
                        ),
                        showlegend=False,
                        hovertemplate=(
                            f"<b>{row['Description']}</b><br>"
                            f"Planned Start: {row['Planned Start']}<br>"
                            f"Planned End: {row['Planned End']}"
                            "<extra></extra>"
                        )
                   
                )
            )
        except:
            print("error adding planned trace")
            print(row)

        if pd.isna(row["Actual Start"]):
            continue

        #Actual Bar
        try:
            fig.add_trace(
                go.Scatter(
                        x=[
                        row["Actual Start"],
                        row["Actual End Plot"]
                        ],
                        y=[
                            row["Description"],
                            row["Description"]
                        ],
                        mode = "lines",
                        line = dict(
                            color=row["Colour"],
                            width=18
                        ),
                        showlegend=False,
                        hovertemplate=(
                            f"<b>{row['Description']}</b><br>"
                            f"Actual Start: {row['Actual Start']}<br>"
                            f"Actual End: {row['Actual End']}<br>"
                            f"Slip: {row['Slip Days']}<br>"
                            f"Owner: {row['Responsible Party']}<br>"
                            f"Completion: {row['Completion']}%"
                            "<extra></extra>"
                        )

                )
            )
        except:
            print("error adding actual trace")
            print(row)  

    #print(pd.Timestamp.today())
    
    #Today
    try:
        fig.add_vline(
            x=pd.Timestamp.today(),
            line_color="red",
            line_dash="dash",
            annotation_text="Today"
        )
    except Exception:
        traceback.print_exc(file=sys.stdout)

    #(I am) Legend
    Legend_Items = [
        ("Planned", "rgba(180,180,180,0.6)",6),
        ("On Track", "#00bc8c",18 ),
        ("Slight Slip", "#f39c12",18 ),
        ("Late", "#e74c3c",18 )
    ]


    for name, colour, width in Legend_Items:
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="lines",
                line=dict(
                    color=colour,
                    width=width
                ),
                name=name
            )
        )

    fig.update_layout(
        template="plotly_dark",
        title = "Task Chart",
        xaxis_title="Date",
        yaxis_title="",
        hovermode="closest",
        height=max(500, len(df)*35),
        margin=dict(
            l=350,
            r=50,
            t=75,
            b=50,
        ),
        legend=dict(
            orientation="h",
            y=1.05
        )
    )

    fig.update_yaxes(
        autorange="reversed"
    )

    return fig



def compute_kpis(df):
    today = datetime.date.today()
    #print(df)

    date_cols = ["Planned Start", "Planned End", "Actual Start", "Actual End"]

    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")


    #print(df)
    # Parse dates
    df["Actual End Plot"] = (
        df["Actual End"].fillna(pd.Timestamp.today().normalize())
    )

    df["Actual End Plot"] = df["Actual End"].fillna(
        pd.Timestamp.today().normalize()
        )
    #print("df actual plot")
    #print(df["Actual End"])

    try:
        df["Slip Days"] = (
            df["Actual End Plot"]  - df["Planned End"]
        ).dt.days
    except:
        df["Slip Days"] = 0
        print("Slip fail")
    
    Total = len(df["Task Number"])
    on_track = (df["Slip Days"] == 0).sum()
    slipping = ((df["Slip Days"] >  0) & (df["Slip Days"]<5)).sum()
    late = (df["Slip Days"] >5 ).sum()

    completed = len(df[df["Status"] == "Complete" ])

    #print(df["Slip Days"])

    
    

    return Total, on_track, slipping, late


def build_grid(df, page):
    #print("build grid")
    #print(df)

    id_string=page + "_task-grid"
    #print(id_string)

    # df["Planned Start"] = pd.to_datetime(df["Planned Start"])
    # df["Planned Start"] = df["Planned Start"].dt.strftime("%Y-%m-%d")
    # df["Planned End"] = pd.to_datetime(df["Planned End"])
    # df["Planned End"] = df["Planned End"].dt.strftime("%Y-%m-%d")
    # df["Actual Start"] = pd.to_datetime(df["Actual Start"])
    # df["Actual Start"] = df["Actual Start"].dt.strftime("%Y-%m-%d")
    # df["Actual End"] = pd.to_datetime(df["Actual End"])
    # df["Actual End"] = df["Actual End"].dt.strftime("%Y-%m-%d")




    column_defs = [
        {
         "headerName": "Task Number", 
         "field": "Task Number", 
         "editable": True
        },
        {
        "headerName": "Task", 
        "field": "Description", 
        "editable": True
         },
        {
            "field": "Planned Start",
            "editable": True,
            "cellDataType": "dateString"

        },
        {
        "headerName": "Planned End", 
        "field": "Planned End",
        "cellDataType": "dateString", 
        "editable": True,},
        {
        "headerName": "Duration", 
        "field": "Duration",
        "type": "number", 
        "editable": True,
        },        
        {
        "headerName": "Actual Start", 
        "field": "Actual Start", 
        "editable": True,
        "cellDataType": "dateString"            
        },
        {
        "headerName": "Actual End", 
        "field": "Actual End", 
        "editable": True,
        "cellDataType": "dateString"

        },
        {"headerName": "Responsible Party", "field": "Responsible Party", "editable": True, },
        {"headerName": "Status", "field": "Status", "editable": True,"cellEditor": "agSelectCellEditor",
            "cellEditorParams": {
                "values": ["Not Started","New","To Be closed", "Open", "In Progress", "Blocked", "Closed"]
            }},
        {"headerName": "Notes", "field": "Notes", "editable": True},
        {
        "headerName": "Dependencies",
        "field": "Dependencies",
        "editable": True,
        },
        {
        "headerName": "Float",
        "field": "Float",
        },
        {
            "headerName": "Critical",
            "field": "Critical",
            "cellRenderer": "agTextCellRenderer",
        }

    ]
    #print(df["Planned Start"].head())
    #print(df["Planned Start"].dtype)
    return AgGrid(
        id=id_string,
        enableEnterpriseModules=True,
        rowData=df.to_dict("records"),
        columnDefs=column_defs,
        className="ag-theme-alpine",
        defaultColDef={"sortable": True, "filter": True, "resizable": True, "editable":True},
    dashGridOptions={
        "autoSizeStrategy": {"type": "fitGridWidth"},
        "updateRowData": True
    },
    )




def Rail_Table(df):



    df["Open Date"] = pd.to_datetime(df["Open Date"])
    df["Open Date"] = df["Open Date"].dt.strftime("%Y-%m-%d")
    df["Due Date"] = pd.to_datetime(df["Due Date"])
    df["Due Date"] = df["Due Date"].dt.strftime("%Y-%m-%d")


    column_defs = [
        {
            "headerName": "Task Number", 
         "field": "Task Number", 
         "editable": False
         },
        {
            "headerName": "Open Date",
            "field": "Open Date",
            "editable": True
            },
        {
            "headerName": "Description", 
            "field": "Description", 
            "editable": True
            },
        {
            "headerName": "Priority",
            "field": "Priority", 
            "editable": True,
            "cellEditor": "agSelectCellEditor",
            "cellEditorParams": {
                            "values": ["High", "Medium", "Low"]
                        },
            },
        {"headerName": "Category", 
         "field": "Category", 
         "editable": True,
         "cellEditor": "agSelectCellEditor",
         "cellEditorParams": {
                         "values": ["Tech", "Non-Tech"]
                     },
        },
        {
            "headerName": "Responsible Party",
            "field": "Responsible Party",
            "editable": True,
        },
        {"headerName": "Due Date",
          "field": "Due Date",
          "cellDataType": "dateString",
           "editable": True,
            "cellEditorParams": {
                "useLocalTime": True
                    }},
        {
            "headerName": "Completion", 
            "field": "Completion", 
            "editable": True
         },
        {
            "headerName": "Status",
            "field": "Status",
            "editable": True,
            "cellEditor": "agSelectCellEditor",
            "cellEditorParams": {
                "values": ["Open", "In Progress", "Closed", "To Be Closed", "New", "Deferred"]
            },
            "cellStyle": {
                "styleConditions": [
                    {
                        "condition": "params.value === 'Open'",
                        "style": {
                            "backgroundColor": "#d9ffb5",
                            "color":"#000000"
                            }
                    },
                    {
                        "condition": "params.value === 'In Progress'",
                        "style": {
                            "backgroundColor": "#ffe5b5",
                            "color":"#000000"
                            }
                    },
                    {
                        "condition": "params.value === 'New'",
                        "style": {
                            "backgroundColor": "#d9ffb5",
                            "color":"#000000"
                            }
                    },
                ]
            }


        },
        {"headerName": "Notes", 
         "field": "Notes"
        },
    ]


    return AgGrid(
        id="Rail-grid",
        enableEnterpriseModules=True,
        rowData=df.to_dict("records"),
        columnDefs=column_defs,
        className="ag-theme-alpine",
        defaultColDef={"sortable": True, "filter": True, "resizable": True},
        dashGridOptions={
            "autoSizeStrategy": {"type": "fitGridWidth"},
            "rowSelection":{
                "mode": "singleRow"
            },
        }
    )
