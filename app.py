import dash
import dash_bootstrap_components as dbc
import flask


app = flask.Flask(__name__)

app_dash = dash.Dash(__name__, server=app,
                     external_scripts=[
                           "https://code.jquery.com/jquery-3.2.1.min.js",
                           "https://codepen.io/bcd/pen/YaXojL.js",
                           "https://codepen.io/chriddyp/pen/bWLwgP120",
                           "https://use.fontawesome.com/releases/v5.7.1/css/all.css"
                                    ],
                      external_stylesheets=[dbc.themes.BOOTSTRAP,
                      'https://use.fontawesome.com/releases/v5.8.1/css/all.css'],
                      url_base_pathname='/',
                      meta_tags=[{"name":"viewport", "content":"width=device-width, initial-scale=1"}]
                      )

app.secret_key = b'H\xeb\xe6f\x04\xa0A\x1fc\xbc\x0e\x7f'
app.jinja_env.cache = {}
server = app_dash.server
app_dash.config.suppress_callback_exceptions = True
app_dash.css.config.serve_locally = True
app_dash.scripts.config.serve_locally = True
app_dash.title = 'Player Profile'