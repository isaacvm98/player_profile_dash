import pandas as pd
import numpy as np
from dash import Output,Input, html, dcc, dash_table, State
import dash_bootstrap_components as dbc
from app import app_dash
import colorlover
from apps.vis.shotchart import create_shotchart
import psycopg2
import os
from dotenv import load_dotenv
import requests
import plotly.graph_objects as go
load_dotenv()

DB = os.environ['database']
USER_NAME = os.environ['user']
PASSWORD = os.environ['password']
PORT = os.environ['port']
HOST = os.environ['host']


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

CELL_STYLE = {'fontFamily':'Segoe UI',
              'border': 'bottom'}

df_names = pd.read_csv('./assets/players_teams.csv')
df = pd.read_csv('./assets/playtypes_new.csv')
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
                dbc.Tab(label="Matchups", tab_id="tab-3"),
                dbc.Tab(label="Assist Network", tab_id="tab-4")
            ],
            id="tabs",
            active_tab="tab-1",
        ),
        html.Br(),
        html.Div(id="content")])


    footer = dbc.Row([
                dbc.Col(html.Small('Created by Isaac Vergara', style={'font-size': '14px', 'font-weight': 'bold'}),sm=3),
                dbc.Col(html.A(html.I(className="fab fa-github fa-2x"), href="https://github.com/isaacvm98", target="_blank"),sm=3),
                dbc.Col(html.A(html.I(className="fab fa-twitter fa-2x"), href="https://twitter.com/ivm9816", target="_blank"),sm=3),
                dbc.Col(html.A(html.I(className="fab fa-linkedin fa-2x"), href="https://linkedin.com/in/isaac-vergara-mercenario-4a9822185",
                                target="_blank"),sm=3)
                        ])

    layout = html.Div([
                    dbc.Row([html.H5('Select a player'),
                             dcc.Dropdown(player_names,
                                   value='LeBron James',
                                   id='player')],
                      justify='center'),
                    html.Hr(),
                    html.Div(id='header'),
                    html.Br(),
                    tabs,
                    html.Hr(),
                    footer
                      ],style={'font-family': 'Arial'})
    return layout

import dash_bootstrap_components as dbc

# Define the popover content
popover_content = [dbc.PopoverHeader("Expected Points per Shot Model"),    dbc.PopoverBody('''The Expected Points Per Shot (XPPS) values shown 
                                                                                            in the table are calculated using a XGBoost model 
                                                                                            that takes into account the location of the shot,
                                                                                            time remaining in the shot clock, touch time before the shot,
                                                                                            the number of dribbles taken and
                                                                                            the closest defender ''')]

# Define the layout of your app
xpps_layout = dbc.Row([
    dbc.Col([
        html.H3('Shotchart',style={'text-align':'center'}),
        dcc.Loading(dcc.Graph(id='shotchart_fig',config=config_b)),
    ],sm=4),
    dbc.Col([
        dbc.Row([
            dbc.Col([
                html.H3('Expected Points', style={"textDecoration": "underline", "cursor": "pointer"}, id="expected-points-model"),
                dbc.Popover(
                    popover_content, 
                    id="popover-target",
                    is_open=False,
                    target="expected-points-model",
                    placement="bottom-start",
                ),
            ], 
            width={"size": 6, "offset": 6},
        ),
        html.Br(),
        dbc.Col(id='table_xpps', 
                 style={'border': '1px solid lightgray'}
        )
    ])],sm=8)
    ])
matchup_layout = html.Div([
    dbc.Row([
        html.H3('Matchups by team',style={'text-align':'center'}),
        dcc.Dropdown(id='team_dropdown',value=1610612738)
    ]),
    html.Br(),
    dbc.Row(id='table_matchups',
                 style={'border': '1px solid lightgray', 'border-radius': '5px', 'padding': '10px'}   
    )
    ])

assists_layout = html.Div([
    dbc.Row([
        html.H3('Assists Network',style={'text-align':'center'}),
    ]),
    html.Br(),
    dcc.Graph(id='assist_fig',config=config_b)
    ])


# Define the callback to toggle the popover
@app_dash.callback(
    Output("popover-target", "is_open"),
    [Input("expected-points-model", "n_clicks")],
    [State("popover-target", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open

@app_dash.callback(Output("content", "children"), Input("tabs", "active_tab"))
def switch_tab(at):
    if at == "tab-1":
        return html.Div(id='tendencies-tables')
    elif at == "tab-2":
        return xpps_layout
    elif at == 'tab-3':
        return matchup_layout
    elif at == 'tab-4':
        return assists_layout

@app_dash.callback(Output('tendencies-tables','children'),
                   Input('player','value'))
def render_tendency_table(player_name):
    try:
        
        percentage = dash_table.FormatTemplate.percentage(1)
        
        df_player = df[(df['PLAYER_NAME']==player_name)]
        df_player['SEASON_ID'] = df_player['SEASON_ID'].astype(str)

        # Pivot the dataframe
        df_pivoted = pd.pivot_table(df_player, index='PLAY_TYPE', columns='SEASON_ID', values=['PPP','PERCENTILE','POSS_PCT'])

        # Flatten the multi-level column index
        df_pivoted.columns = [' '.join(col).strip() for col in df_pivoted.columns.values]

        # Reset the index
        df_pivoted = df_pivoted.reset_index()

        years = ['2022','2023']
        df_pivoted['Frequency Change'] = (df_pivoted[f'POSS_PCT {years[1]}'] - df_pivoted[f'POSS_PCT {years[0]}']) / df_pivoted[f'POSS_PCT {years[0]}']
        df_pivoted['PPPoss Change'] = (df_pivoted[f'PPP {years[1]}'] - df_pivoted[f'PPP {years[0]}']) / df_pivoted[f'PPP {years[0]}']
        df_pivoted['PPPoss Percentile Change'] = (df_pivoted[f'PERCENTILE {years[1]}'] - df_pivoted[f'PERCENTILE {years[0]}']) / df_pivoted[f'PERCENTILE {years[0]}']
        df_pivoted_1 = df_pivoted[['PLAY_TYPE',f'POSS_PCT {years[0]}', f'POSS_PCT {years[1]}','Frequency Change',
                        f'PPP {years[0]}',f'PPP {years[1]}', 'PPPoss Change',
                        f'PERCENTILE {years[0]}', f'PERCENTILE {years[1]}','PPPoss Percentile Change']]
        rename_dict = {'PLAY_TYPE': 'Play Type',
                                f'POSS_PCT {years[0]}': f'Frequency {years[0]}', 
                            f'POSS_PCT {years[1]}':f'Frequency {years[1]}', 
                                f'PPP {years[0]}': f'PPPoss {years[0]}',
                                f'PPP {years[1]}':f'PPPoss {years[1]}',
                                f'PERCENTILE {years[0]}': f'PPPoss Percentile {years[0]}',
                                f'PERCENTILE {years[1]}':f'PPPoss Percentile {years[1]}'}
        color_cols = [i for i in rename_dict.values()]
        added_cols = ['Frequency Change','PPPoss Change','PPPoss Percentile Change']
        color_cols = color_cols + added_cols 
        df_pivoted_1 = df_pivoted_1.rename(columns=rename_dict)
        df_pivoted_1 = df_pivoted_1[df_pivoted_1[f'Frequency {years[1]}']>.05]
        styles_all = []
        for col in df_pivoted_1.columns.to_list():
            if col in color_cols[1:]:
                styles = discrete_background_color_bins(df_pivoted_1, columns=[col])
                styles_all = styles_all+styles
        columns_pct = ['Frequency 2022', 'Frequency 2023',
                        'Frequency Change', 'PPPoss Percentile Change', 
                        'PPPoss Change']
        columns = []
        for col in df_pivoted_1.columns.to_list():
            if col in columns_pct:
                rv = {"name": col, "id": col,'type':'numeric', 'format':percentage}
            elif col == 'Play Type':
                rv = {"name": col, "id": col} 
            else:
                rv = {"name": col, "id": col,'type':'numeric'}
            columns.append(rv)
        table = dash_table.DataTable(
                data=df_pivoted_1.to_dict('records'),
                columns= columns,
                #style_data_conditional=styles_all,
                style_cell_conditional=[
                        {
                            'if': {'column_id': 'Play Type'},
                            'textAlign': 'center'
                        }
                    ],
                style_header=HEADER_STYLE,
                style_data=CELL_STYLE)
            
        tables = html.Div([
            dbc.Row([
            html.H3('Frequency'),
            table
            ],justify='center'),
            html.Footer(['Source:',   
                          html.A('NBA Synergy Playtype Data', href='https://www.nba.com/stats/players/transition'),   
                         ])
        ],style={'text-align':'center'})
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
    # conn1 = psycopg2.connect(
    #   database= DB,
    #   user= USER_NAME, 
    #   password= PASSWORD, 
    #   port = PORT,
    #   host = HOST 
    # )
    # cursor = conn1.cursor() 
    # sql1=f'''select * from shots_2023 WHERE player_id = {player_id}'''
    # cursor.execute(sql1)
    # columns = cursor.description
    # conn1.commit()
    # columns = [columns[i][0] for i in range(len(columns))]
    # data = pd.DataFrame(cursor.fetchall(),columns=columns)
    # conn1.close()
    url = "https://api.pbpstats.com/get-shots/nba"
    params = {
        "Season": "2023-24",
        "SeasonType": "Regular Season",
        "EntityType": "Player",
        "EntityId": f"{player_id}",
    }
    response = requests.get(url, params=params)
    response_json = response.json()
    data = pd.DataFrame(response_json["results"])
    data['event_type'] = np.where(data['made']==True,'Made Shot','Missed Shot')
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
@app_dash.callback(Output('header','children'),
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
    style_table = {'box-sizing':'border-box',
        'border': '0 solid',
        'border-style': 'solid',
        'vertical-align':' middle',
        'height': 'auto',
        'display': 'in-line',
        'width': '20%',
        'margin-left': 'auto',
        'margin-right': 'auto',
        'margin-top': '6rem'}
    df_player = df[(df['PLAYER_NAME']==player_name)]
    player_id = df_player['PLAYER_ID'].iloc[0]
    conn1 = psycopg2.connect(
      database= DB,
      user= USER_NAME, 
      password= PASSWORD, 
      port = PORT,
      host = HOST 
    )
    cursor = conn1.cursor() 
    sql1=f'''select salary,player_age,rapm,winsadded,added_value,offposs
             from stats WHERE player_id = {player_id}'''
    cursor.execute(sql1)
    columns = cursor.description
    conn1.commit()
    columns = [columns[i][0] for i in range(len(columns))]
    data = pd.DataFrame(cursor.fetchall(),columns=columns)
    if len(data)>1:
        data = data.iloc[0]
    conn1.close()
    # # Extract the player's information from the DataFrame
    salary = data['salary'].iloc[0]
    player_age = data['player_age'].iloc[0]
    rapm = data['rapm'].iloc[0]
    winsadded = data['winsadded'].iloc[0]
    added_value = data['added_value'].iloc[0]
    possesions = data['offposs'].iloc[0]

    # Create the header component
    image = html.Img(src=f'https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png', style=style_img)
    offensive_profile = pd.read_csv('./assets/offensive_roles.csv')
    offensive_profile = offensive_profile[offensive_profile['PLAYER_ID']==player_id]
    offensive_profile = offensive_profile['new_clusters'].iloc[0]
    # Create a table to display the player's information
    info_table = html.Table([
        html.Tr([html.Th('Salary'), html.Td("${:,}".format(salary))]),
        html.Tr([html.Th('Age'), html.Td(player_age)]),
        html.Tr([html.Th('RAPM',
                         style={"textDecoration": "underline", "cursor": "pointer"},
                         id="rapm"), html.Td(rapm)]),
        html.Tr([html.Th('Wins Added',
                         style={"textDecoration": "underline", "cursor": "pointer"},
                         id="wins-added"), html.Td(round(winsadded,2))]),
        html.Tr([html.Th('Added Value',
                         style={"textDecoration": "underline", "cursor": "pointer"},
                         id="added-value"), html.Td("${:,}".format(added_value))]),
        html.Tr([html.Th('Possessions'), html.Td(possesions)]),
        html.Tr([html.Th('Offensive Role',
                         style={"textDecoration": "underline", "cursor": "pointer"},
                         id="offensive-role-model"), html.Td(offensive_profile)])
    ],style=style_table)
    if player_name.endswith('s'):
        profile = f"{player_name}' Profile"
    else:
        profile = f"{player_name}'s Profile"

    clustering_explanation = [dbc.PopoverHeader("Offensive Role Clustering model"),    dbc.PopoverBody('''The K-means clustering model groups basketball players based on 
                                                                                            their frequency in nine different playtypes. It identifies similarities 
                                                                                            among players and assigns them to clusters with similar playstyle patterns.
                                                                                            This helps coaches and analysts understand player strengths, roles, 
                                                                                            and tendencies. Clusters reveal distinct groups of players, 
                                                                                            such as iso specialists or rolling bigs, 
                                                                                            enabling better player evaluation and team composition.''')]
    rapm_explanation = [dbc.PopoverHeader("RAPM"),    dbc.PopoverBody('''RAPM is typically calculated by taking the last three seasons of all play by play 
                                                                      data, weighting the latest season the most, and solving for a linear system of equations 
                                                                      where every row of that system are the 5 offensive and defensive players on the floor 
                                                                      between every substitution of every game and the resulting plus minus (also called a stint). 
                                                                      We hope to find the plus minus contribution of every player by solving the linear system.
                                                                      Source: https://medium.com/@johnchenmbb/95a7730ef59b''')]
    wins_added_explanation = [dbc.PopoverHeader("Wins Added Calculation"),    dbc.PopoverBody('''Wins added was calculated using ((RAPM/100 + 3/100)*Possesions)/32.5.
                                                                                              Adding +3/100 because thats the baseline that follow the NBA's salary structure.
                                                                                              Dividing by 32.5 because 30-35 points of scoring margin adds one win to a team's 
                                                                                              expected record, using the Pythagorean Wins Formula.''')]
    added_value_explanation = [dbc.PopoverHeader("Added Value Calculation"),    dbc.PopoverBody('''Added Value is calculated using the following formula:
                                                                                                Added Value = (Wins Added * League Value per Win) - Salary.
                                                                                                League Value per Win is around $3.8 millon/win.
                                                                                                The goal is the find the most cost efficient players, 
                                                                                                that normally occurs during a player's rookie contracts.
                                                                                                Inspired in Seth Partnow's book The Midrange Theory''')]
    # Combine the header and the info table
    header = html.Div([dbc.Row(html.H3(profile,style={'text-align':'center','font-weight':'bold'}),justify='center'),
                       dbc.Row([image,info_table,
                                dbc.Popover(
                                    clustering_explanation, 
                                    target="offensive-role-model",
                                    placement="bottom-start",
                                    id="popover-target-2"
                                ),
                                dbc.Popover(
                                    rapm_explanation, 
                                    target="rapm",
                                    placement="bottom-start",
                                    id="popover-rapm"
                                ),
                                dbc.Popover(
                                    wins_added_explanation, 
                                    target="wins-added",
                                    placement="bottom-start",
                                    id="popover-target-wins"
                                ),
                                dbc.Popover(
                                    added_value_explanation, 
                                    target="added-value",
                                    placement="bottom-start",
                                    id="popover-target-value"
                                )])
                       ])
    return header
#Define the callback to toggle the popover
@app_dash.callback(
    Output("popover-target-2", "is_open"),
    [Input("offensive-role-model", "n_clicks")],
    [State("popover-target-2", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open
@app_dash.callback(
    Output("popover-rapm", "is_open"),
    [Input("rapm", "n_clicks")],
    [State("popover-rapm", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open
@app_dash.callback(
    Output("popover-target-wins", "is_open"),
    [Input("wins-added", "n_clicks")],
    [State("popover-target-wins", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open
@app_dash.callback(
    Output("popover-target-value", "is_open"),
    [Input("added-value", "n_clicks")],
    [State("popover-target-value", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open
@app_dash.callback(Output('team_dropdown','options'),
                   Input('player','value'))

def team_ops(player_name):
    df_player = df_names[df_names['PLAYER_NAME']==player_name]
    player_id = df_player['PLAYER_ID'].iloc[0]
    conn = psycopg2.connect(
      database= DB,
      user= USER_NAME, 
      password= PASSWORD, 
      port = PORT,
      host = HOST 
    )
    curs = conn.cursor() 
    sql1=f'''SELECT DISTINCT def_team_id 
            FROM matchups 
            WHERE off_player_id = {player_id}'''
    curs.execute(sql1)
    columns = curs.description
    conn.commit()
    columns = [columns[i][0] for i in range(len(columns))]
    data = pd.DataFrame(curs.fetchall(),columns=columns)
    conn.close()
    data = data.merge(df_names[['TEAM_ABB','TEAM_ID']],left_on='def_team_id',right_on='TEAM_ID',how='left')
    data.drop_duplicates(inplace=True)
    teams_dropdown = [{'value':v,'label':k} for v,k in zip(data['TEAM_ID'],data['TEAM_ABB'])]
    return teams_dropdown
    
@app_dash.callback(Output('table_matchups','children'),
                    Input('player','value'),
                   Input('team_dropdown','value')
                  )

def render_shotchart(player_name,team_id):
    df_player = df_names[df_names['PLAYER_NAME']==player_name]
    player_id = df_player['PLAYER_ID'].iloc[0]
    conn = psycopg2.connect(
      database= DB,
      user= USER_NAME, 
      password= PASSWORD, 
      port = PORT,
      host = HOST 
    )
    curs = conn.cursor() 
    sql1=f'''SELECT def_player_id, partial_poss,matchup_points, points_per_poss 
            FROM matchups 
            WHERE off_player_id = {player_id} AND def_team_id = {int(team_id)}'''
    curs.execute(sql1)
    columns = curs.description
    conn.commit()
    columns = [columns[i][0] for i in range(len(columns))]
    data = pd.DataFrame(curs.fetchall(),columns=columns)
    conn.close()
    rename_dict = {'def_player_id':'Player', 'partial_poss':'Possesions','matchup_points':'Points', 'points_per_poss':'Points Per Possession'}
    data.rename(columns=rename_dict,inplace=True)
    data['Player'] = data['Player'].map(dict(zip(df_names['PLAYER_ID'],df_names['PLAYER_NAME'])))
    data.sort_values('Points Per Possession',ascending=False,inplace=True)
    data['Points Per Possession'] = data['Points Per Possession'].round(2)
    table = dash_table.DataTable(
                data=data.to_dict('records'),
                columns= [{"name": i, "id": i} for i in data.columns],
                style_header= HEADER_STYLE,
                style_data=CELL_STYLE,
                style_cell_conditional=[
                        {
                            'if': {'column_id': 'Player'},
                            'textAlign': 'left'
                        }
                    ],
            )
    return table

@app_dash.callback(Output('assist_fig','figure'),
                   Input('player','value'))

def get_assist_fig(player_name):
    df_player = df_names[df_names['PLAYER_NAME']==player_name]
    player_id = df_player['PLAYER_ID'].iloc[0]
    if len(df_player)>1:
        team_id = df_player['TEAM_ID'].iloc[-1]
    else:
        team_id = df_player['TEAM_ID'].iloc[0]
    url = "https://api.pbpstats.com/get-assist-networks/nba"
    params = {
        "Season": "2023-24",
        "SeasonType": "Regular Season",
        "EntityType": "Team", # Options: Team, Lineup
        "EntityId": f'{team_id}'
    }
    response = requests.get(url, params=params)
    response_json = response.json()
    df = pd.DataFrame(response_json["results"]["links"])
    df = df[df['source'] == str(player_id)]
    dict_names = dict(zip(df_names['PLAYER_ID'].astype(str),df_names['PLAYER_NAME']))
    df['source'] = df['source'].map(dict_names)
    df['target'] = df['target'].map(dict_names)
    # Define colors with transparency for each assist type
    assist_type_colors = {
        'Arc3': 'rgba(0, 0, 255, 0.5)',
        'AtRim': 'rgba(0, 128, 0, 0.5)',
        'Corner3': 'rgba(128, 0, 128, 0.5)',
        'LongMidRange': 'rgba(255, 165, 0, 0.5)',
        'ShortMidRange': 'rgba(255, 0, 0, 0.5)'
    }

    # Create nodes for source, assist type, and target players
    assist_types = ['Arc3', 'AtRim', 'Corner3', 'LongMidRange', 'ShortMidRange']
    players = list(set(df['source']).union(set(df['target'])))
    nodes = assist_types + players
    node_dict = {node: idx for idx, node in enumerate(nodes)}
    node_colors = [assist_type_colors.get(node, 'blue') for node in nodes]
    # Create links
    links = []
    for idx, row in df.iterrows():
        source = node_dict[row['source']]
        target_player = node_dict[row['target']]
        value = row['value']
        for assist_type in assist_types:
            target_type = node_dict[assist_type]
            assist_value = row[assist_type]
            link_color = assist_type_colors[assist_type]  # Get the color for the assist type
            links.append({'source': source, 'target': target_type, 'value': assist_value, 'color': link_color})
            links.append({'source': target_type, 'target': target_player, 'value': assist_value, 'color': link_color})

    # Create nodes
    node_labels = [f"{assist_type}" for assist_type in assist_types] + [f"{player}" for player in players]

    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color='black', width=0.5),
            label=node_labels,
            color=node_colors
        ),
        link=dict(
            source=[link['source'] for link in links],
            target=[link['target'] for link in links],
            value=[link['value'] for link in links],
            color=[link['color'] for link in links]
        ))])

    # Set layout title
    fig.update_layout(
        font=dict(size=14,family='Segoe UI')
    )
    return fig