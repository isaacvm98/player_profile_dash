import plotly.graph_objects as go
court_shapes = []

outer_lines_shape = dict(
  type='rect',
  xref='x',
  yref='y',
  x0='-250',
  y0='-47.5',
  x1='250',
  y1='422.5',
  line=dict(
      color='rgba(10, 10, 10, 1)',
      width=1
  )
)

court_shapes.append(outer_lines_shape)


hoop_shape = dict(
  type='circle',
  xref='x',
  yref='y',
  x0='7.5',
  y0='7.5',
  x1='-7.5',
  y1='-7.5',
  line=dict(
    color='rgba(10, 10, 10, 1)',
    width=1
  )
)

court_shapes.append(hoop_shape)

backboard_shape = dict(
  type='rect',
  xref='x',
  yref='y',
  x0='-30',
  y0='-7.5',
  x1='30',
  y1='-6.5',
  line=dict(
    color='rgba(10, 10, 10, 1)',
    width=1
  ),
  fillcolor='rgba(10, 10, 10, 1)'
)

court_shapes.append(backboard_shape)

outer_three_sec_shape = dict(
  type='rect',
  xref='x',
  yref='y',
  x0='-80',
  y0='-47.5',
  x1='80',
  y1='143.5',
  line=dict(
      color='rgba(10, 10, 10, 1)',
      width=1
  )
)

court_shapes.append(outer_three_sec_shape)

inner_three_sec_shape = dict(
  type='rect',
  xref='x',
  yref='y',
  x0='-60',
  y0='-47.5',
  x1='60',
  y1='143.5',
  line=dict(
      color='rgba(10, 10, 10, 1)',
      width=1
  )
)

court_shapes.append(inner_three_sec_shape)

left_line_shape = dict(
  type='line',
  xref='x',
  yref='y',
  x0='-220',
  y0='-47.5',
  x1='-220',
  y1='92.5',
  line=dict(
      color='rgba(10, 10, 10, 1)',
      width=1
  )
)

court_shapes.append(left_line_shape)

right_line_shape = dict(
  type='line',
  xref='x',
  yref='y',
  x0='220',
  y0='-47.5',
  x1='220',
  y1='92.5',
  line=dict(
      color='rgba(10, 10, 10, 1)',
      width=1
  )
)

court_shapes.append(right_line_shape)

three_point_arc_shape = dict(
  type='path',
  xref='x',
  yref='y',
  path='M -220 92.5 C -70 300, 70 300, 220 92.5',
  line=dict(
      color='rgba(10, 10, 10, 1)',
      width=1
  )
)

court_shapes.append(three_point_arc_shape)

circulo = dict(
  type='circle',
  xref='x',
  yref='y',
  x0='60',
  y0='482.5',
  x1='-60',
  y1='362.5',
  line=dict(
      color='rgba(10, 10, 10, 1)',
      width=1
  )
)

court_shapes.append(circulo)

res_circle_shape = dict(
  type='circle',
  xref='x',
  yref='y',
  x0='20',
  y0='442.5',
  x1='-20',
  y1='402.5',
  line=dict(
      color='rgba(10, 10, 10, 1)',
      width=1
  )
)

court_shapes.append(res_circle_shape)

free_throw_circle_shape = dict(
  type='circle',
  xref='x',
  yref='y',
  x0='60',
  y0='200',
  x1='-60',
  y1='80',
  line=dict(
      color='rgba(10, 10, 10, 1)',
      width=1
  )
)

court_shapes.append(free_throw_circle_shape)

res_area_shape = dict(
  type='circle',
  xref='x',
  yref='y',
  x0='40',
  y0='40',
  x1='-40',
  y1='-40',
  line=dict(
    color='rgba(10, 10, 10, 1)',
    width=1,
    dash='dot'
  )
)

court_shapes.append(res_area_shape)

def create_shotchart(data):
    missed_shot_trace=go.Scatter(
    x=data[data["EVENT_TYPE"]=="Missed Shot"]["LOC_X"],
    y=data[data["EVENT_TYPE"]=="Missed Shot"]["LOC_Y"],
    mode="markers",
    name="Miss",
    marker={"color":"red","size":5},
    hoverinfo='skip')

    made_shot_trace=go.Scatter(
        x=data[data["EVENT_TYPE"]=="Made Shot"]["LOC_X"],
        y=data[data["EVENT_TYPE"]=="Made Shot"]["LOC_Y"],
        mode="markers",
        name="Made",
        marker={"color":"green","size":5},
        hoverinfo='skip')

    df=[missed_shot_trace,made_shot_trace]
    layout = go.Layout(
        showlegend=True,
        xaxis=dict(
            showgrid=False,
            range=[-300, 300],
            showticklabels=False
        ),
        yaxis=dict(
            showgrid=False,
            range=[-100, 500],
            showticklabels=False
        ),
        height=600,
        width=650,
        shapes=court_shapes,
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        legend=dict(y=1.08, x=0.5, orientation='h', xanchor='center', yanchor='middle', itemsizing='constant'),
    )

    shotchart = go.Figure(data=df, layout=layout)

    return shotchart