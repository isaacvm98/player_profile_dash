from dash import dcc,html, Output,Input
from app import app_dash, app
import apps


children_pages = apps.children_pages
app_dash.layout = html.Div([dcc.Location(id='url', refresh=True),
                            html.Div(id='page-content', style={"padding": "15px 20px 15px 20px"}),
                            ], style={"background-color": "white", 'height': '120%'}
                           )


@app.after_request
def apply_caching(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response

@app_dash.callback(Output('page-content', 'children'),
                   [Input('url', 'pathname')])
def display_page(pathname):
    l = html.Div([
        children_pages[pathname].create_layout(),
    ]
    )

    return l

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False, use_reloader=True, threaded=True)
    