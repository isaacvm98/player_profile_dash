import pandas as pd
from dash import Output,Input, html, dcc, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
from app import app_dash
import colorlover

years = ['2021-22','2022-23']
df = pd.read_csv('./assets/NBA_Play_Types_16_23.csv')
df = df[(df['SEASON'].isin(years))]
def discrete_background_color_bins(df, n_bins=5, columns='all'):
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
        backgroundColor = colorlover.scales[str(n_bins)]['seq']['Blues'][i - 1]
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
    player_names = list(df['PLAYER_NAME'].unique())
    layout = html.Div([dbc.Row(html.H1('Player Profiles 2022-2023'),justify='center'),
                    html.Hr(),
                    dbc.Row([html.H5('Select a player'),
                             dcc.Dropdown(player_names,
                                   value='James Harden',
                                   id='player')],
                      justify='center'),
                    html.Br(),
                    dbc.Col(id='tendencies-tables',sm=10)
                      ])
    return layout

@app_dash.callback(Output('tendencies-tables','children'),
                   Input('player','value'))
def render_tendency_table(player_name):
    try:
        percentage = dash_table.FormatTemplate.percentage(1)

        df_player = df[(df['PLAYER_NAME']==player_name)]
        player_id = df_player['PLAYER_ID'].iloc[0]

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
                style_data_conditional=styles_all
            )
        table_2 = dash_table.DataTable(
                data=df_pivoted_2.to_dict('records'),
                columns= columns_2,
                style_data_conditional=styles_all_2
            )
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
        tables = html.Div([
            dbc.Row([html.H3(f'Play Type Frequency & Efficiency for {player_name}'),
                     html.Img(src=f'https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png',style=style_img)]),
            html.Br(),
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