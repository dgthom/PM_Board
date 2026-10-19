# PM Board

A Dash-based project planning and RAIL management tool.

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