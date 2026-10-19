# PM Board

A Dash-based project planning and RAIL management tool.

## Why I built it

Not having access to project planning and management tools I decided to build a lightweight project scheduling tool to allow me to better plan and execute. It quickly evolved into a tool that could help me contextualise conversations with external stakeholders to keep projects running to time and moving forward.

## Screenshots

### Schedule Dashboard

![ScheduleDashboard](docs/images/Schedule_DashBoard.png)

### Action Item List

![ActionItems](docs/images/ActionItems.png)

### Critical Path Visualisation

![CriticalPath](docs/images/Critical_Path_View.png)

## Features

- Project scheduling
- Critical path analysis
- Task dependencies
- RAIL management
- Interactive AG Grid interface
- Plotly visualisations
- Project persistence and reload


## Installation
Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Copy:

```text
config.default.json
```

to:

```text
config.json
```

Then edit the configuration as required.

## Running the Application

```bash
python app.py
```

## Project Structure

```text
PM_Board/
│
├── app.py
├── pages/
├── assets/
├── config.default.json
├── requirements.txt
└── README.md
```

## License

MIT License