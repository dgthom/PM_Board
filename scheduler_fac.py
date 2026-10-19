from datetime import datetime, timedelta
import networkx as nx
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Dependency Types (FS, SS, FF) and Lags/Leads
#
# Your scheduling engine supports three standard dependency types:
#
#   FS  (Finish‑to‑Start)
#       The successor task starts only after the predecessor finishes.
#       Example: "1:FS" → Task starts when Task 1 ends.
#
#   SS  (Start‑to‑Start)
#       The successor task starts when the predecessor starts.
#       Example: "4:SS" → Task starts when Task 4 starts.
#
#   FF  (Finish‑to‑Finish)
#       The successor task finishes when the predecessor finishes.
#       Example: "7:FF" → Task finishes when Task 7 finishes.
#
# Lags and Leads:
#   A positive lag (+N) delays the successor.
#   A negative lag (‑N) creates overlap (lead).
#
#   Examples:
#       "1:FS+3" → Start 3 working days after Task 1 finishes.
#       "2:SS-2" → Start 2 working days before Task 2 starts.
#       "7:FF+5" → Finish 5 working days after Task 7 finishes.
#
# Multiple dependencies can be combined using commas:
#       "1:FS+3, 4:SS, 7:FF-2"
#
# The scheduler resolves all dependencies and lags by:
#   1. Recomputing each task’s end date from its start + duration.
#   2. Applying dependency rules to determine candidate start dates.
#   3. Selecting the latest candidate start (max constraint).
#   4. Repeating until the schedule stabilizes (full propagation).
#
# This produces behaviour similar to MS Project / Primavera:
# downstream tasks automatically shift when predecessors change.
# ---------------------------------------------------------------------------




class SimpleTask:
    def compute_end_date(start_date: datetime, working_days: float) -> datetime:
        """
        Compute an end date by adding working days (Mon–Fri) to a start date.
        Weekends are skipped. Holidays can be added later if needed.
        """
        date = start_date
        days_added = 0

        while days_added < working_days:
            date += timedelta(days=1)
            if date.weekday() < 5:  # Monday=0 ... Friday=4
                days_added += 1

        return date

    def parse_dependency(dep_str):
        """
        Convert '1:FS+3' into:
        {
            "task": "1",
            "type": "FS",
            "lag": 3
        }
        """
        try:
            task_part, rule_part = dep_str.split(":")
            task = task_part.strip()

            # Default type is FS
            dep_type = "FS"
            lag = 0

            # Extract type and lag
            if "+" in rule_part:
                dep_type, lag_str = rule_part.split("+")
                lag = float(lag_str)
            elif "-" in rule_part:
                dep_type, lag_str = rule_part.split("-")
                lag = -float(lag_str)
            else:
                dep_type = rule_part.strip()

            return {"task": task, "type": dep_type.strip(), "lag": lag}

        except Exception:
            return None

    def apply_full_dependency_schedule(rows):
        """
        Run dependency logic repeatedly until the schedule stabilizes.
        Supports FS, SS, FF with lags/leads.
        """
        changed = True
        task_lookup = {str(row.get("Task Number")): row for row in rows}

        while changed:
            changed = False

            for row in rows:
                deps_raw = row.get("Dependencies", "")
                if not deps_raw:
                    continue

                dep_items = [d.strip() for d in deps_raw.split(",") if d.strip()]
                parsed_deps = [SimpleTask.parse_dependency(d) for d in dep_items]

                candidate_starts = []

                for dep in parsed_deps:
                    if not dep:
                        continue

                    pred = task_lookup.get(dep["task"])
                    if not pred:
                        continue

                    dep_type = dep["type"]
                    lag = dep["lag"]
                    lag_td = timedelta(days=lag)

                    # FS
                    if dep_type == "FS" and pred.get("Planned End"):
                        pred_end = datetime.strptime(pred["Planned End"], "%Y-%m-%d")
                        candidate_starts.append(pred_end + lag_td)

                    # SS
                    if dep_type == "SS" and pred.get("Planned Start"):
                        pred_start = datetime.strptime(pred["Planned Start"], "%Y-%m-%d")
                        candidate_starts.append(pred_start + lag_td)

                    # FF
                    if dep_type == "FF" and pred.get("Planned End"):
                        pred_end = datetime.strptime(pred["Planned End"], "%Y-%m-%d")
                        try:
                            duration = float(row.get("Duration", 0))
                            succ_end = pred_end + lag_td
                            succ_start = SimpleTask.compute_end_date(succ_end, -duration)
                            candidate_starts.append(succ_start)
                        except:
                            pass

                if candidate_starts:
                    new_start = max(candidate_starts)
                    old_start = row.get("Planned Start")

                    if old_start != new_start.strftime("%Y-%m-%d"):
                        row["Planned Start"] = new_start.strftime("%Y-%m-%d")

                        duration = float(row.get("Duration", 0))
                        end_dt = SimpleTask.compute_end_date(new_start, duration)
                        row["Planned End"] = end_dt.strftime("%Y-%m-%d")

                        changed = True

        return rows

    def recompute_end_dates(rows):
            """Recompute Planned End for all tasks based on Planned Start + Duration."""
            for row in rows:
                start = row.get("Planned Start")
                duration_raw = row.get("Duration")

                try:
                    duration = float(duration_raw)
                except (TypeError, ValueError):
                    continue

                if start:
                    try:
                        start_dt = datetime.strptime(start, "%Y-%m-%d")
                        end_dt = SimpleTask.compute_end_date(start_dt, duration)
                        row["Planned End"] = end_dt.strftime("%Y-%m-%d")
                    except Exception:
                        pass

            return rows

    def extract_predecessors(dep_str):
        # Handle None, NaN, floats, lists, etc.
        if dep_str is None:
            return []

        if isinstance(dep_str, float):  # NaN is float
            return []

        if isinstance(dep_str, list):   # already parsed
            return dep_str

        if not isinstance(dep_str, str):
            return []

        dep_str = dep_str.strip()
        if dep_str == "":
            return []

        parts = dep_str.split(",")
        preds = []

        for p in parts:
            p = p.strip()
            task_id = p.split(":")[0]   # extract the number before FS/SS/FF
            preds.append(task_id)

        return preds


    def build_graph(df):
        G = nx.DiGraph()
        for _, row in df.iterrows():
            G.add_node(row["Task Number"], duration=row["Duration"])
            if isinstance(row["PredList"], list):
                for dep in row["PredList"]:
                    G.add_edge(dep, row["Task Number"])
        return G

    def forward_pass(df, G):
        ES, EF = {}, {}

        topo = list(nx.topological_sort(G))

        for task in topo:
            preds = list(G.predecessors(task))

            # --- DEBUG BLOCK ---
            #print("\n=== Forward Pass Debug ===")
            #print("Current task:", repr(task))
            #print("Predecessors:", preds)

            # Check DF lookup
            df_rows = df.loc[df["Task Number"] == task]
            #print("DF lookup rows:", len(df_rows))

            if len(df_rows) == 0:
                print("ERROR: Task not found in DataFrame!")
                print("Valid DF Task Numbers:", df["Task Number"].unique())
                raise ValueError(f"Task {task} not found in DataFrame")

            duration = df_rows["Duration"].iloc[0]
            #print("Duration:", duration)
            # --- END DEBUG BLOCK ---

            # Normal CPM logic
            if preds:
                ES[task] = max(EF[p] for p in preds)
            else:
                ES[task] = 0

            try:
                duration = int(duration)
            except (ValueError, TypeError):
                duration = 0
                print(f"Warning: Invalid duration for {task}: {duration}")


            EF[task] = ES[task] + duration

        return ES, EF

    

    def backward_pass(df, G, EF):
        LS, LF = {}, {}

        topo_rev = list(reversed(list(nx.topological_sort(G))))
        project_finish = max(EF.values())

        for task in topo_rev:
            succs = list(G.successors(task))
            if succs:
                LF[task] = min(LS[s] for s in succs)
            else:
                LF[task] = project_finish

            duration = df.loc[df["Task Number"] == task, "Duration"].iloc[0]
            LS[task] = LF[task] - duration

        return LS, LF
    
    def compute_float(ES, LS):
        return {task: LS[task] - ES[task] for task in ES}

    def extract_critical_path(float_dict):
        return [task for task, fl in float_dict.items() if fl == 0]

    def compute_critical_path(df):
        G = SimpleTask.build_graph(df)
        ES, EF = SimpleTask.forward_pass(df, G)
        LS, LF = SimpleTask.backward_pass(df, G, EF)
        float_dict = SimpleTask.compute_float(ES, LS)
        critical_path = SimpleTask.extract_critical_path(float_dict)

        return ES, EF, LS, LF, float_dict, critical_path, G

    def build_dependency_graph_plot(G, critical_path):
        # 1. Topological order → left-to-right layout
        order = list(nx.topological_sort(G))

        # 2. Assign x positions based on order index
        pos = {}
        for i, node in enumerate(order):
            pos[node] = [i, 0]  # baseline y = 0

        # 3. Vertical layering based on dependency depth
        for node in order:
            depth = len(list(G.predecessors(node)))
            pos[node][1] = -depth

        # 4. Build edges (lines)
        edge_x = []
        edge_y = []
        for u, v in G.edges():
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

        # Edge colour: planned grey (same as Gantt planned bars)
        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(width=2, color="rgba(180,180,180,0.6)"),
            hoverinfo="none"
        )

        # 5. Build nodes
        node_x = []
        node_y = []
        node_text = []
        node_color = []

        for node, data in G.nodes(data=True):
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

            # Hover text
            node_text.append(
                f"<b>Task {node}</b><br>"
                f"Duration: {data['duration']}"
            )

            # Critical path = Late colour (red)
            if node in critical_path:
                node_color.append("#e74c3c")  # Late
            else:
                node_color.append("#00bc8c")  # On Track (green)

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=[str(n) for n in G.nodes()],
            textposition="bottom center",
            hovertext=node_text,
            hoverinfo="text",
            marker=dict(
                size=22,
                color=node_color,
                line=dict(width=2, color="black")  # matches Gantt bar outline
            )
        )

        # 6. Final figure
        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            template="plotly_dark",  # MATCH GANTT CHART
            showlegend=False,
            margin=dict(l=40, r=40, t=40, b=40),
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False),
            plot_bgcolor="rgba(0,0,0,1)",  # transparent dark background
            paper_bgcolor="rgba(0,0,0,1)"
        )




        return fig

    def build_timescaled_cpm_plot(G, ES, EF, critical_path):
        node_x = []
        node_y = []
        node_widths = []
        node_text = []
        node_color = []

        # Vertical spacing based on dependency depth
        depth_map = {}
        for node in G.nodes():
            depth_map[node] = len(list(G.predecessors(node)))

        # Build node traces
        for node in G.nodes():
            x = ES[node]  # Earliest Start = x-position
            y = -depth_map[node]  # deeper dependencies lower

            node_x.append(x)
            node_y.append(y)

            duration = EF[node] - ES[node]
            node_widths.append(duration)

            node_text.append(
                f"<b>Task {node}</b><br>"
                f"ES: {ES[node]}<br>"
                f"EF: {EF[node]}<br>"
                f"Duration: {duration}"
            )

            if node in critical_path:
                node_color.append("#e74c3c")  # Late (red)
            else:
                node_color.append("#00bc8c")  # On Track (green)

        # Build edges
        edge_x = []
        edge_y = []
        for u, v in G.edges():
            x0 = EF[u]  # end of predecessor
            y0 = -depth_map[u]
            x1 = ES[v]  # start of successor
            y1 = -depth_map[v]

            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(width=2, color="rgba(180,180,180,0.6)"),
            hoverinfo="none"
        )

        # Node rectangles (time-scaled)
        rect_traces = []
        for i, node in enumerate(G.nodes()):
            rect_traces.append(
                go.Scatter(
                    x=[node_x[i], node_x[i] + node_widths[i]],
                    y=[node_y[i], node_y[i]],
                    mode="lines",
                    line=dict(color=node_color[i], width=18),
                    hovertext=node_text[i],
                    hoverinfo="text",
                    showlegend=False
                )
            )

        # Build final figure
        fig = go.Figure([edge_trace] + rect_traces)
        fig.update_layout(
            template="plotly_dark",
            title="Time‑Scaled CPM Diagram",
            xaxis_title="Time (Earliest Start)",
            yaxis_title="Dependency Depth",
            hovermode="closest",
            paper_bgcolor="rgba(0,0,0,1)",
            plot_bgcolor="rgba(0,0,0,1)",
            margin=dict(l=40, r=40, t=40, b=40)
        )

        fig.update_yaxes(visible=False)

        return fig

