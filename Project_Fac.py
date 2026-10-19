import os
import json
from datetime import datetime, timedelta
import pandas as pd



class Project_Factory:
    def create_project_folder(base_path, project_name):
        """
        Create a new project folder with default files.
        """
        project_path = os.path.join(base_path, project_name)

        # Create folder
        os.makedirs(project_path, exist_ok=True)

        # Create empty schedule + RAIL placeholders
        open(os.path.join(project_path, "schedule.xlsx"), "wb").close()
        open(os.path.join(project_path, "rail.xlsx"), "wb").close()
        #create Empty RAIL
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

        RAIL_df.to_excel(os.path.join(project_path, "rail.xlsx"), index=False)
        schedule_df.to_excel(os.path.join(project_path, "schedule.xlsx"), index=False)


        # Metadata file
        metadata = {
            "project_name": project_name,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "status": "Active"
        }

        with open(os.path.join(project_path, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4)

        return project_path

    def list_projects(base_path):
        """
        Return a list of project folder names.
        """
        return [
            name for name in os.listdir(base_path)
            if os.path.isdir(os.path.join(base_path, name))
        ]

    def load_project(base_path, project_name):

        project_path = os.path.join(base_path, project_name)
        
        schedule_path = os.path.join(project_path, "schedule.xlsx")
        
        meta_path = os.path.join(project_path, "metadata.json")

        schedule_df = pd.read_excel(schedule_path)

        with open(meta_path, "r") as f:
            metadata = json.load(f)

        return schedule_df, metadata

    def save_project(base_path, project_name, schedule_df, metadata):

        project_path = os.path.join(base_path, project_name)

        meta_path = os.path.join(project_path, "metadata.json")
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=4)

        schedule_df.to_excel(os.path.join(project_path, "schedule.xlsx"), index=False)


    def load_project_Rail(base_path, project_name):

        project_path = os.path.join(base_path, project_name)


        schedule_path = os.path.join(project_path, "rail.xlsx")
        #print("Schedule path rail call:", schedule_path)
        Rail_df = pd.read_excel(schedule_path)

        return Rail_df

    def Load_META_Data(base_path, project_name):

        project_path = os.path.join(base_path, project_name)
        meta_path = os.path.join(project_path, "metadata.json")

        if not os.path.exists(meta_path):
            return ["N/A"] * 8

        with open(meta_path, "r") as f:
            metadata = json.load(f)

        return metadata
