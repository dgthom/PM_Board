import dash
from dash import Dash, html
import dash_bootstrap_components as dbc

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.DARKLY],
    assets_folder="assets",
    pages_folder="pages",
    suppress_callback_exceptions=True
)

app.layout = html.Div([
    dash.page_container
])

if __name__ == '__main__':
    app.run(debug=True)