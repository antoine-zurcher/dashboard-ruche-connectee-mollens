# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, dcc, html, Input, Output, State, ctx
import dash_daq as daq
from datetime import datetime, timedelta
from datetime import date
import plotly.graph_objects as go
import pandas as pd
import requests
import json
from plotly.graph_objs import Layout

url_wan = 'http://178.199.62.136/data'
url_lan = 'http://192.168.1.116/data'
ticker = 'TemperatureInterieure'
start_date = None
end_date = None
timeframe = 'day'
ma_window = 50
period_save = 1000 * 60 * 60  # 1 hour in ms
BS = 'https://cdn.jsdelivr.net/npm/bootswatch@4.5.2/dist/slate/bootstrap.min.css'
layout = Layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)'
)

# styling the sidebar
SIDEBAR_STYLE = {
    'position': 'fixed',
    'top': 0,
    'left': 0,
    'bottom': 0,
    'width': '24rem',
    'padding': '1rem 1rem',
    'background-color': '#f8f9fa',
}

# padding for the page content
CONTENT_STYLE = {
    'margin-left': '27rem',
    'margin-right': '1rem',
    'padding': '1rem 1rem',
}


def append_data(df):
    temperature_interieure = 0
    humidite_interieure = 0
    temperature_exterieure = 0
    masse = 0
    while not (temperature_interieure and humidite_interieure and temperature_exterieure and masse):
        response = requests.get(url_wan)
        text = response.text
        data = json.loads(text)
        temperature_interieure = round(data[0]['value'], 1)
        humidite_interieure = round(data[1]['value'], 0)
        temperature_exterieure = round(data[2]['value'], 1)
        masse = round(data[3]['value'], 1)
    # datetime object containing current date and time
    now = datetime.now()
    today = date.today()
    
    # dd/mm/YY H:M:S
    now_string = now.strftime('%d/%m/%Y %H:%M:%S')

    df_temp = pd.DataFrame(
        [[now, today, temperature_interieure, humidite_interieure, temperature_exterieure, masse]],
        columns=['Datetime', 'Date', 'TemperatureInterieure', 'HumiditeInterieure', 'TemperatureExterieure', 'Masse']
    )
    df = pd.concat([df, df_temp], ignore_index=True)
    return df


app = Dash(external_stylesheets=[BS], suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    html.Div([
        html.H1('Mesures'),
        html.Div([
            html.Div(
                daq.Thermometer(
                    id='thermometer-int',
                    value=20,
                    min=-20,
                    max=50,
                    label={'label': 'Température intérieure', 'style': {'color': '#272B30'}},
                    labelPosition='bottom',
                    showCurrentValue=True,
                    units="C",
                    color='#b2050f'
                ),
                style={'width': '49%', 'display': 'inline-block'}),
            html.Div(
                daq.Thermometer(
                    id='thermometer-ext',
                    value=20,
                    min=-20,
                    max=50,
                    label={'label': 'Température extérieure', 'style': {'color': '#272B30'}},
                    labelPosition='bottom',
                    showCurrentValue=True,
                    units="C",
                    color='#b2050f'
                ),
                style={'width': '49%', 'display': 'inline-block'}),
        ]),
        html.Hr(style={'background-color': '#AAAAAA'}),
        html.Div([
            daq.Gauge(
                id='gauge-hum',
                showCurrentValue=True,
                units="%",
                value=50,
                label={'label': 'Humidité intérieure (%)', 'style': {'color': '#272B30'}},
                labelPosition='bottom',
                max=100,
                min=0,
                color='#b2050f'
            ),
        ], style={'height': '18rem'}),
        html.Hr(style={'background-color': '#AAAAAA'}),
        html.Div([
            daq.LEDDisplay(
                id='led-masse',
                label={'label': 'Masse (kg)', 'style': {'color': '#272B30'}},
                labelPosition='bottom',
                value=50,
                color='#b2050f'
            ),
        ], ),
        html.Div([
            html.Div([
                dcc.Input(
                    id="input-a",
                    type="number",
                    placeholder="a",
                    style={'width': '5vh'}
                ),
                dcc.Input(
                    id="input-b",
                    type="number",
                    placeholder="b",
                    style={'width': '10vh'}
                ),
            ], style={'width': '49%', 'display': 'inline-block'}),
            html.Div(
                html.Button('Calibrer balance', id='button-calibrate', n_clicks=0),
                style={'width': '49%', 'display': 'inline-block'}),
        ], style={'display': 'none'}),

    ],
        style=SIDEBAR_STYLE,
    ),
    ###############
    html.Div([
        html.Div(id='hidden-div', style={'display': 'none'}),
        html.Div(id='hidden-div2', style={'display': 'none'}),
        html.Div(id='hidden-div3', style={'display': 'none'}),
        html.Div(id='hidden-div4', style={'display': 'none'}),
        dcc.Store(id='memory', storage_type='local'),
        dcc.Store(id='memory-a', storage_type='local'),
        dcc.Store(id='memory-b', storage_type='local'),
        dcc.Interval(
            id='interval-component',
            interval=period_save,
            n_intervals=0),
        dcc.Interval(
            id='interval-data',
            interval=period_save,
            n_intervals=0),
        html.H1('Graphique'),
        html.H4('Sélectionner les variables à afficher:'),
        html.Div([
            html.Div([
                dcc.Checklist(
                    id='ticker',
                    options=[
                        {'label': 'Température intérieure', 'value': 'TemperatureInterieure'},
                        {'label': 'Humidité intérieure', 'value': 'HumiditeInterieure'},
                        {'label': 'Température extérieure', 'value': 'TemperatureExterieure'},
                        {'label': 'Masse', 'value': 'Masse'},
                    ],
                    value=['TemperatureInterieure'],
                    inline=False,
                    labelStyle={'padding': '1rem'},
                ),
            ], style={'width': '49%', 'display': 'inline-block'}),
            html.Div([
                html.Button('Actualiser', id='button-refresh', n_clicks=0)
            ], style={'width': '49%', 'display': 'inline-block'}),
        ]),
        html.Hr(style={'background-color': '#f8f9fa'}),
        html.H4("Sélectionner l'échelle de temps:"),
        html.Div([
            html.Div([
                dcc.DatePickerRange(
                    id='date-picker',
                    start_date_placeholder_text="Début",
                    end_date_placeholder_text="Fin",
                    display_format='DD/MM/YYYY',
                    clearable=True,
                    with_portal=True,
                ),
            ], style={'width': '49%', 'display': 'inline-block'}),
            html.Div([
                dcc.RadioItems(
                    id='radio-timeframe',
                    options=[
                        {'label': 'Dernier jour', 'value': 'day'},
                        {'label': 'Dernière semaine', 'value': 'week'},
                        {'label': 'Dernier mois', 'value': 'month'},
                    ],
                    value='day',
                    labelStyle={'padding': '1rem'},
                ),
            ], style={'width': '49%', 'display': 'inline-block'}),
        ]),
        html.Hr(style={'background-color': '#f8f9fa'}),
        dcc.Graph(id='time-series-chart', style={'height': '90vh'}),
    ],
        style=CONTENT_STYLE,
    ),
])


# Callback to update the invisible intermediate-value element
@app.callback([Output('time-series-chart', 'figure'),
               Output('thermometer-int', 'value'),
               Output('thermometer-ext', 'value'),
               Output('gauge-hum', 'value'),
               Output('led-masse', 'value'),
               Output('memory', 'data'),
               ],
              [Input('interval-component', 'n_intervals'),
               Input('memory', 'data'),
               Input('ticker', 'value'),
               Input('radio-timeframe', 'value'),
               Input('button-refresh', 'n_clicks'),
               Input('date-picker', 'end_date')
               ],
              State('date-picker', 'start_date'), )
def update_graph(value, df_dict, selection, timeframe_selection, n_clicks, end, start):
    triggered_id = ctx.triggered_id
    if triggered_id == 'interval-component':
        return refresh_data(value, df_dict)
    elif triggered_id == 'button-refresh':
        if n_clicks:
            return refresh_data_wo_save(value, df_dict)
    elif triggered_id == 'ticker':
        return change_ticker(selection, df_dict)
    elif triggered_id == 'radio-timeframe':
        return change_timeframe(timeframe_selection, df_dict)
    elif triggered_id == 'date-picker':
        if start and end:
            return change_start_end(start, end, df_dict)


def refresh_data(value, df_dict):
    global ticker
    df_sensor = pd.DataFrame.from_dict(df_dict)
    if df_sensor.empty:
        df_sensor = pd.DataFrame(
            columns=['Datetime', 'Date', 'TemperatureInterieure', 'HumiditeInterieure', 'TemperatureExterieure',
                     'Masse'])
    df_sensor = append_data(df_sensor)

    df_sensor['Date'] = pd.to_datetime(df_sensor['Date']).dt.date
    mask_time = (df_sensor['Date'] >= start_date) & (df_sensor['Date'] <= end_date)
    df_time = df_sensor.loc[mask_time]

    fig = go.Figure(layout=layout)
    fig.update_layout(
        font_color="white",
    )
    if 'TemperatureInterieure' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['TemperatureInterieure'],
                                 line_shape='spline',
                                 name='Température intérieure'))
    if 'HumiditeInterieure' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['HumiditeInterieure'],
                                 line_shape='spline',
                                 name='Humidité intérieure'))
    if 'TemperatureExterieure' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['TemperatureExterieure'],
                                 line_shape='spline',
                                 name='Température extérieure'))
    if 'Masse' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['Masse'],
                                 line_shape='spline',
                                 name='Masse'))
    return fig, df_sensor['TemperatureInterieure'].tail(1).item(), df_sensor['TemperatureExterieure'].tail(1).item(), \
           df_sensor['HumiditeInterieure'].tail(1).item(), df_sensor['Masse'].tail(1).item(), df_sensor.to_dict()


def refresh_data_wo_save(value, df_dict):
    global ticker
    global start_date
    global end_date
    df_sensor = pd.DataFrame.from_dict(df_dict)
    if df_sensor.empty:
        df_sensor = pd.DataFrame(
            columns=['Datetime', 'Date', 'TemperatureInterieure', 'HumiditeInterieure', 'TemperatureExterieure',
                     'Masse'])
    df_sensor = append_data(df_sensor)

    df_sensor['Date'] = pd.to_datetime(df_sensor['Date']).dt.date
    mask_time = (df_sensor['Date'] >= start_date) & (df_sensor['Date'] <= end_date)
    df_time = df_sensor.loc[mask_time]

    fig = go.Figure(layout=layout)
    fig.update_layout(
        font_color="white",
    )
    if 'TemperatureInterieure' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['TemperatureInterieure'],
                                 line_shape='spline',
                                 name='Température intérieure'))
    if 'HumiditeInterieure' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['HumiditeInterieure'],
                                 line_shape='spline',
                                 name='Humidité intérieure'))
    if 'TemperatureExterieure' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['TemperatureExterieure'],
                                 line_shape='spline',
                                 name='Température extérieure'))
    if 'Masse' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['Masse'],
                                 line_shape='spline',
                                 name='Masse'))
    return fig, df_sensor['TemperatureInterieure'].tail(1).item(), df_sensor['TemperatureExterieure'].tail(1).item(), \
           df_sensor['HumiditeInterieure'].tail(1).item(), df_sensor['Masse'].tail(1).item(), df_sensor.to_dict()


def change_ticker(selection, df_dict):
    global ticker
    df_sensor = pd.DataFrame.from_dict(df_dict)
    if df_sensor.empty:
        df_sensor = pd.DataFrame(
            columns=['Datetime', 'Date', 'TemperatureInterieure', 'HumiditeInterieure', 'TemperatureExterieure',
                     'Masse'])
    ticker = selection
    df_sensor['Date'] = pd.to_datetime(df_sensor['Date']).dt.date
    mask_time = (df_sensor['Date'] >= start_date) & (df_sensor['Date'] <= end_date)
    df_time = df_sensor.loc[mask_time]

    fig = go.Figure(layout=layout)
    fig.update_layout(
        font_color="white",
    )
    if 'TemperatureInterieure' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['TemperatureInterieure'],
                                 line_shape='spline',
                                 name='Température intérieure'))
    if 'HumiditeInterieure' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['HumiditeInterieure'],
                                 line_shape='spline',
                                 name='Humidité intérieure'))
    if 'TemperatureExterieure' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['TemperatureExterieure'],
                                 line_shape='spline',
                                 name='Température extérieure'))
    if 'Masse' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['Masse'],
                                 line_shape='spline',
                                 name='Masse'))
    return fig, df_sensor['TemperatureInterieure'].tail(1).item(), df_sensor['TemperatureExterieure'].tail(1).item(), \
           df_sensor['HumiditeInterieure'].tail(1).item(), df_sensor['Masse'].tail(1).item(), df_sensor.to_dict()


def change_timeframe(value, df_dict):
    global timeframe
    global start_date
    global end_date
    timeframe = value
    end_date = date.today()
    if timeframe == 'day':
        start_date = date.today()
    elif timeframe == 'week':
        start_date = date.today() - timedelta(days=7)
    elif timeframe == 'month':
        start_date = date.today() - timedelta(days=30)

    df_sensor = pd.DataFrame.from_dict(df_dict)
    if df_sensor.empty:
        df_sensor = pd.DataFrame(
            columns=['Datetime', 'Date', 'TemperatureInterieure', 'HumiditeInterieure', 'TemperatureExterieure',
                     'Masse'])
    df_sensor['Date'] = pd.to_datetime(df_sensor['Date']).dt.date
    mask_time = (df_sensor['Date'] >= start_date) & (df_sensor['Date'] <= end_date)
    df_time = df_sensor.loc[mask_time]

    fig = go.Figure(layout=layout)
    fig.update_layout(
        font_color="white",
    )
    if 'TemperatureInterieure' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['TemperatureInterieure'],
                                 line_shape='spline',
                                 name='Température intérieure'))
    if 'HumiditeInterieure' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['HumiditeInterieure'],
                                 line_shape='spline',
                                 name='Humidité intérieure'))
    if 'TemperatureExterieure' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['TemperatureExterieure'],
                                 line_shape='spline',
                                 name='Température extérieure'))
    if 'Masse' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['Masse'],
                                 line_shape='spline',
                                 name='Masse'))
    return fig, df_sensor['TemperatureInterieure'].tail(1).item(), df_sensor['TemperatureExterieure'].tail(1).item(), \
           df_sensor['HumiditeInterieure'].tail(1).item(), df_sensor['Masse'].tail(1).item(), df_sensor.to_dict()


def change_start_end(start, end, df_dict):
    global start_date
    global end_date
    start_date = datetime.strptime(start, '%Y-%m-%d').date()
    end_date = datetime.strptime(end, '%Y-%m-%d').date()

    df_sensor = pd.DataFrame.from_dict(df_dict)
    if df_sensor.empty:
        df_sensor = pd.DataFrame(
            columns=['Datetime', 'Date', 'TemperatureInterieure', 'HumiditeInterieure', 'TemperatureExterieure',
                     'Masse'])
    df_sensor['Date'] = pd.to_datetime(df_sensor['Date']).dt.date
    mask_time = (df_sensor['Date'] >= start_date) & (df_sensor['Date'] <= end_date)
    df_time = df_sensor.loc[mask_time]

    fig = go.Figure(layout=layout)
    fig.update_layout(
        font_color="white",
    )
    if 'TemperatureInterieure' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['TemperatureInterieure'],
                                 line_shape='spline',
                                 name='Température intérieure'))
    if 'HumiditeInterieure' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['HumiditeInterieure'],
                                 line_shape='spline',
                                 name='Humidité intérieure'))
    if 'TemperatureExterieure' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['TemperatureExterieure'],
                                 line_shape='spline',
                                 name='Température extérieure'))
    if 'Masse' in ticker:
        fig.add_trace(go.Scatter(x=df_time['Datetime'],
                                 y=df_time['Masse'],
                                 line_shape='spline',
                                 name='Masse'))
    return fig, df_sensor['TemperatureInterieure'].tail(1).item(), df_sensor['TemperatureExterieure'].tail(1).item(), \
           df_sensor['HumiditeInterieure'].tail(1).item(), df_sensor['Masse'].tail(1).item(), df_sensor.to_dict()


if __name__ == '__main__':
    app.run_server(debug=True)
