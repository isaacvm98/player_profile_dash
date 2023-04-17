import pandas as pd
from dash import Output,Input, html, dcc, dash_table
import dash_bootstrap_components as dbc
from app import app_dash
import colorlover
from apps.vis.shotchart import create_shotchart
from nba_api.stats.endpoints import shotchartdetail
import urllib3, socket
from urllib3.connection import HTTPConnection
    
HTTPConnection.default_socket_options = ( 
            HTTPConnection.default_socket_options + [
            (socket.SOL_SOCKET, socket.SO_SNDBUF, 1000000), #1MB in byte
            (socket.SOL_SOCKET, socket.SO_RCVBUF, 1000000)
        ])
boptions= ["zoom2d", "pan2d", "select2d", "lasso2d", "zoomIn2d", "zoomOut2d", "autoScale2d",
           "resetScale2d", "hoverClosestCartesian", "hoverCompareCartesian",
           "zoom3d", "pan3d", "resetCameraDefault3d", "resetCameraLastSave3d", "hoverClosest3d",
           "orbitRotation", "tableRotation", "zoomInGeo", "zoomOutGeo", "resetGeo", "hoverClosestGeo",
           "toImage", "sendDataToCloud", "hoverClosestGl2d", "hoverClosestPie",
           "toggleHover", "resetViews", "toggleSpikelines", "resetViewMapbox"]
config_b = {"displaylogo":False,
            'modeBarButtonsToRemove':boptions, #'displayModeBar': True,
            }
HEADER_STYLE = {'whiteSpace': 'normal',
                    'height': 'auto',
                    'textAlign': 'center',
                    'color':'white',
                    'fontWeight': 'bold',
                    'backgroundColor': 'rgb(98, 100, 100, 1)',
                    'fontFamily':'Segoe UI'}

CELL_STYLE = {'fontFamily':'Segoe UI'}

years = ['2021-22','2022-23']
df_names = pd.read_csv('./assets/players_teams.csv')
df = pd.read_csv('./assets/NBA_Play_Types_16_23.csv')
df = df[(df['SEASON'].isin(years))]

def discrete_background_color_bins(df, n_bins=5, columns='all'):
    """
    Apply discrete background color bins to a DataFrame containing numerical data.

    Parameters:
    -----------
    df : pandas.DataFrame
        The DataFrame containing the numerical data to be binned.
    n_bins : int, optional (default=5)
        The number of bins to use.
    columns : str or list-like, optional (default='all')
        The columns to be binned. If 'all', all numerical columns except for 'id' are selected.

    Returns:
    --------
    styles : list of dicts
        A list of dictionaries, each containing the style specifications for a single cell in the DataFrame.
        The 'if' key specifies the cell(s) to apply the style to, and the 'backgroundColor' and 'color' keys
        specify the background color and text color, respectively.
    """
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    if columns == 'all':
        if 'id' in df:
            df_numeric_columns = df.select_dtypes('number').drop(['id'], axis=1)
        else:
            df_numeric_columns = df.select_dtypes('number')
    else:
        df_numeric_columns = df[columns]
    df_max = df_numeric_columns.max().max()
    df_min = df_numeric_columns.min().min()
    ranges = [
        ((df_max - df_min) * i) + df_min
        for i in bounds
    ]
    styles = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        backgroundColor = colorlover.scales[str(n_bins)]['seq']['Greens'][i - 1]
        color = 'white' if i > len(bounds) / 2. else 'inherit'

        for column in df_numeric_columns:
            styles.append({
                'if': {
                    'filter_query': (
                        '{{{column}}} >= {min_bound}' +
                        (' && {{{column}}} < {max_bound}' if (i < len(bounds) - 1) else '')
                    ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                    'column_id': column
                },
                'backgroundColor': backgroundColor,
                'color': color
            })

    return styles
def create_layout():
    player_names = list(df_names['PLAYER_NAME'].unique())
    tabs = html.Div([
        dbc.Tabs(
            [
                dbc.Tab(label="Player Tendencies", tab_id="tab-1"),
                dbc.Tab(label="Expected Points", tab_id="tab-2"),
            ],
            id="tabs",
            active_tab="tab-1",
        ),
        html.Br(),
        html.Div(id="content")])



    layout = html.Div([
                    dbc.Row([html.H5('Select a player'),
                             dcc.Dropdown(player_names,
                                   value='James Harden',
                                   id='player')],
                      justify='center'),
                    html.Hr(),
                    html.Div(id='header'),
                    html.Br(),
                    tabs
                      ])
    return layout

xpps_layout = dbc.Row([dbc.Col([html.H3('Shotchart',style={'text-align':'center'}),
                                            dcc.Graph(id='shotchart_fig',config=config_b)],sm=4),
                            dbc.Col([html.H3('Expected Points',style={'text-align':'center'}),
                                     html.Br(),
                                    html.Div(id='table_xpps')],sm=8),
                                    ])

@app_dash.callback(Output("content", "children"), Input("tabs", "active_tab"))
def switch_tab(at):
    if at == "tab-1":
        return dbc.Col(id='tendencies-tables',sm=10)
    elif at == "tab-2":
        return xpps_layout

@app_dash.callback(Output('tendencies-tables','children'),
                   Input('player','value'))
def render_tendency_table(player_name):
    try:
        percentage = dash_table.FormatTemplate.percentage(1)
        
        df_player = df[(df['PLAYER_NAME']==player_name)]

        df_player = df_player.groupby(['PLAY_TYPE','SEASON'],as_index=False)[['FREQ','FREQ_PCTL','PPP','PPP_PCTL']].mean()

        # Pivot the dataframe
        df_pivoted = pd.pivot_table(df_player, index='PLAY_TYPE', columns='SEASON', values=['FREQ','FREQ_PCTL','PPP','PPP_PCTL'])

        # Flatten the multi-level column index
        df_pivoted.columns = [' '.join(col).strip() for col in df_pivoted.columns.values]

        # Reset the index
        df_pivoted = df_pivoted.reset_index()

        df_pivoted['Frequency Change'] = (df_pivoted[f'FREQ {years[1]}'] - df_pivoted[f'FREQ {years[0]}']) / df_pivoted[f'FREQ {years[0]}']
        df_pivoted['PPPoss Change'] = (df_pivoted[f'PPP {years[1]}'] - df_pivoted[f'PPP {years[0]}']) / df_pivoted[f'PPP {years[0]}']
        df_pivoted['Frequency Percentile Change'] = (df_pivoted[f'FREQ_PCTL {years[1]}'] - df_pivoted[f'FREQ_PCTL {years[0]}']) / df_pivoted[f'FREQ_PCTL {years[0]}']
        df_pivoted['PPPoss Percentile Change'] = (df_pivoted[f'PPP_PCTL {years[1]}'] - df_pivoted[f'PPP_PCTL {years[0]}']) / df_pivoted[f'PPP_PCTL {years[0]}']
        df_pivoted_1 = df_pivoted[['PLAY_TYPE',f'FREQ {years[0]}', f'FREQ {years[1]}','Frequency Change',
                                f'FREQ_PCTL {years[0]}',f'FREQ_PCTL {years[1]}','Frequency Percentile Change',
                                ]]
        df_pivoted_2 = df_pivoted[['PLAY_TYPE',
                                f'PPP {years[0]}',f'PPP {years[1]}', 'PPPoss Change',
                                f'PPP_PCTL {years[0]}', f'PPP_PCTL {years[1]}','PPPoss Percentile Change',f'FREQ {years[1]}']]
        rename_dict = {'PLAY_TYPE': 'Play Type',
                        f'FREQ {years[0]}': f'Frequency {years[0]}', 
                    f'FREQ {years[1]}':f'Frequency {years[1]}', 
                        f'PPP {years[0]}': f'PPPoss {years[0]}',
                        f'PPP {years[1]}':f'PPPoss {years[1]}',
                        f'FREQ_PCTL {years[0]}': f'Frequency Percentile {years[0]}', 
                    f'FREQ_PCTL {years[1]}':f'Frequency Percentile {years[1]}', 
                        f'PPP_PCTL {years[0]}': f'PPPoss Percentile {years[0]}',
                        f'PPP_PCTL {years[1]}':f'PPPoss Percentile {years[1]}'}
        color_cols = [i for i in rename_dict.values()]
        added_cols = ['Frequency Change','PPPoss Change','Frequency Percentile Change','PPPoss Percentile Change']
        color_cols = color_cols + added_cols 
        df_pivoted_1.rename(columns=rename_dict,inplace=True)
        df_pivoted_1 = df_pivoted_1[df_pivoted_1[f'Frequency {years[1]}']>.05]
        styles_all = []
        for col in df_pivoted_1.columns.to_list():
            if col in color_cols[1:]:
                styles = discrete_background_color_bins(df_pivoted_1, columns=[col])
                styles_all = styles_all+styles
        columns_pct = ['Frequency 2021-22', 'Frequency 2022-23','Frequency Percentile Change',
                        'Frequency Change', 'PPPoss Percentile Change', 
                        'PPPoss Change']
        columns = []
        for col in df_pivoted_1.columns.to_list():
            if col in columns_pct:
                rv = {"name": col, "id": col,'type':'numeric', 'format':percentage}
            elif col == 'Play Type':
                rv = {"name": col, "id": col} 
            else:
                rv = {"name": col, "id": col,'type':'numeric', 'format':dash_table.Format.Format(precision=2, scheme=dash_table.Format.Scheme.decimal_integer)}
            columns.append(rv)
        df_pivoted_2.rename(columns=rename_dict,inplace=True)
        df_pivoted_2 = df_pivoted_2[df_pivoted_2[f'Frequency {years[1]}']>.05]
        df_pivoted_2.drop(f'Frequency {years[1]}',axis = 1, inplace=True)
        styles_all_2 = []
        for col in df_pivoted_2.columns.to_list():
            if col in color_cols[1:]:
                styles = discrete_background_color_bins(df_pivoted_2, columns=[col])
                styles_all_2 = styles_all_2+styles
        columns_pct = ['Frequency 2021-22', 'Frequency 2022-23','Frequency Percentile Change',
                        'Frequency Change', 'PPPoss Percentile Change', 
                        'PPPoss Change']
        columns_2 = []
        for col in df_pivoted_2.columns.to_list():
            if col in columns_pct:
                rv = {"name": col, "id": col,'type':'numeric', 'format':percentage}
            elif col == 'Play Type':
                rv = {"name": col, "id": col} 
            else:
                rv = {"name": col, "id": col,'type':'numeric', 'format':dash_table.Format.Format(precision=2, scheme=dash_table.Format.Scheme.fixed)}
            columns_2.append(rv)
        table = dash_table.DataTable(
                data=df_pivoted_1.to_dict('records'),
                columns= columns,
                style_data_conditional=styles_all,
                style_cell_conditional=[
                        {
                            'if': {'column_id': 'Play Type'},
                            'textAlign': 'left'
                        }
                    ],
                style_header=HEADER_STYLE,
                style_data=CELL_STYLE)
            
        table_2 = dash_table.DataTable(
                data=df_pivoted_2.to_dict('records'),
                columns= columns_2,
                style_data_conditional=styles_all_2,
                                style_cell_conditional=[
                        {
                            'if': {'column_id': 'Play Type'},
                            'textAlign': 'left'
                        }
                    ],
                style_header= HEADER_STYLE,
                style_data=CELL_STYLE
            )
        tables = html.Div([
            dbc.Row([
            html.H3('Frequency'),
            table
            ]),
            html.Br(),
            dbc.Row([
            html.H3('Points per Posession'),
            table_2
            ])
        ])
    except:
        tables = html.Div([
            html.H3('No data available for selected player'),
        ])

    return tables


@app_dash.callback( Output('shotchart_fig','figure'),
                   Input('player','value'),
                  )

def render_shotchart(player_name):
    df_player = df_names[df_names['PLAYER_NAME']==player_name]
    player_id = df_player['PLAYER_ID'].iloc[0]
    teams_id = df_player['TEAM_ID'].unique()
    data = pd.DataFrame()
    for i in range(len(teams_id)):
        shot_detail = shotchartdetail.ShotChartDetail(team_id=i,player_id=player_id ,context_measure_simple = 'FGA')
        data = pd.concat([data,shot_detail.get_data_frames()[0]],ignore_index=True)

    shotchart = create_shotchart(data)
    return shotchart

@app_dash.callback( Output('table_xpps','children'),
                   Input('player','value'),
                  )
def render_table_xpps(player_name):
    df_shots = pd.read_csv('./assets/xpts_2023.csv')
    df_shots = df_shots[df_shots['Player']==player_name]
    df_shots.drop(['Player','player_id'],axis=1,inplace=True)
    df_shots = df_shots[['pts_u10', 'xpts_u10', 'Diff_u10', 'pts_o10', 'xpts_o10','Diff_o10', 'pts_3p', 'xpts_3p','Diff_3p','Pts', 'xPts', 'Diff']]
    rename_cols = ['Pts under 10 ft', 'xPts under 10 ft','Diff under 10 ft' ,
                   'Pts over 10 ft', 'xPts over 10 ft', 'Diff over 10ft' ,
                   'Points from 3', 'xPoints from 3','Diff from 3',
                    'Total Points', 'xTotal Points', 'Total Diff']
    dict_rename = dict(zip(df_shots.columns.to_list(),rename_cols))
    df_shots.rename(columns = dict_rename,inplace=True)
    columns = [{"name": col, "id": col,'type':'numeric',
                 'format':dash_table.Format.Format(precision=2, scheme=dash_table.Format.Scheme.decimal_integer)} for col in df_shots.columns]
    table = dash_table.DataTable(
                data=df_shots.to_dict('records'),
                columns= columns,
                style_header= HEADER_STYLE,
                style_data=CELL_STYLE
            )
    return table
@app_dash.callback( Output('header','children'),
                   Input('player','value'),
                  )
def return_header(player_name):
    style_img = {'box-sizing':'border-box',
        'border': '0 solid',
        'border-style': 'solid',
        'vertical-align':' middle',
        'max-width': '100%',
        'height': 'auto',
        'display': 'block',
        'width': '20%',
        'margin-left': 'auto',
        'margin-right': 'auto',
        'margin-top': '6rem'}
    df_player = df[(df['PLAYER_NAME']==player_name)]
    player_id = df_player['PLAYER_ID'].iloc[0]
    header = dbc.Row([html.H3(f'Player Profile for {player_name}'),
                     html.Img(src=f'https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png',style=style_img)])
    return header
