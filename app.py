import dash
from dash import html, dcc, Input, Output, State
import plotly.express as px
import pandas as pd
from src.data_fetcher import get_weather, get_forecast, get_aqi
import traceback

app = dash.Dash(__name__)

# --- LAYOUT ---
app.layout = html.Div(children=[
    
    # 1. HEADER & SEARCH
    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '20px'}, children=[
        html.H1("Weather Dashboard", style={'color': 'white', 'fontSize': '1.5rem', 'marginLeft': '20px'}),
        html.Div([
            dcc.Input(id='city-input', type='text', value='Bangalore', placeholder='Enter City...', 
                      style={'padding': '10px', 'borderRadius': '10px', 'border': 'none', 'backgroundColor': '#1e293b', 'color': 'white'}),
            html.Button('Search', id='search-btn', n_clicks=0, 
                        style={'marginLeft': '10px', 'padding': '10px 20px', 'borderRadius': '10px', 'border': 'none', 'background': '#3b82f6', 'color': 'white', 'cursor': 'pointer'})
        ])
    ]),

    # 2. MASTER GRID
    html.Div(className='dashboard-container', children=[
        
        # ZONE 1: SIDEBAR (Blue Card + Stats)
        html.Div(className='area-sidebar', children=[
            # Blue Card
            html.Div(className='blue-card', children=[
                html.Div([
                    html.H2(id='city-name', style={'color': 'white', 'opacity': '0.9', 'margin': '0'}), 
                    html.P("Current Location", style={'opacity': '0.7', 'fontSize': '0.8rem', 'margin': '0'})
                ]),
                html.Div([
                    html.H1(id='temp-main', style={'fontSize': '3.5rem', 'margin': '10px 0'}), 
                    html.P(id='condition-main', style={'fontSize': '1.2rem', 'margin': '0'})
                ]),
                html.Div("Last Updated: Just now", style={'opacity': '0.6', 'fontSize': '0.8rem'})
            ]),

            # Mini Stats Grid
            html.Div(className='stats-grid', children=[
                html.Div(className='mini-card', children=[html.P("💧 Humidity", className='label-text'), html.H3(id='val-hum', className='value-text')]),
                html.Div(className='mini-card', children=[html.P("💨 Wind", className='label-text'), html.H3(id='val-wind', className='value-text')]),
                html.Div(className='mini-card', children=[html.P("👁️ Visibility", className='label-text'), html.H3(id='val-vis', className='value-text')]),
                html.Div(className='mini-card', children=[html.P("⏲️ Pressure", className='label-text'), html.H3(id='val-press', className='value-text')]),
            ])
        ]),

        # ZONE 2: WEEKLY STRIP
        html.Div(className='area-weekly', id='weekly-strip'),

        # ZONE 3: CHART
        html.Div(className='area-chart glass-card', children=[
            html.H2("Temperature Forecast (24h)"),
            dcc.Graph(id='main-chart', config={'displayModeBar': False}, style={'height': '200px'})
        ]),

        # ZONE 4: SUNRISE/SET
        html.Div(className='area-sun glass-card', style={'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center'}, children=[
            html.P("Sunrise & Sunset", style={'color': '#94a3b8', 'marginBottom': '20px'}),
            html.Div([html.P("🌅 Sunrise"), html.H3(id='val-sunrise', style={'color': '#fbbf24'})]),
            html.Hr(style={'borderColor': 'rgba(255,255,255,0.1)', 'margin': '15px 0'}),
            html.Div([html.P("🌇 Sunset"), html.H3(id='val-sunset', style={'color': '#f87171'})])
        ]),

        # ZONE 5: AIR QUALITY (Updated Layout)
        html.Div(className='area-air glass-card', children=[
            html.H2("Air Quality Overview"),
            html.Div(style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'height': '100%'}, children=[
                
                # Left: The Circle Badge
                html.Div(style={'textAlign': 'center'}, children=[
                    html.Div(id='aqi-badge', style={'width': '80px', 'height': '80px', 'borderRadius': '50%', 'border': '4px solid #22c55e', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'fontSize': '2rem', 'fontWeight': 'bold'}, children="?"),
                    html.P(id='aqi-text', style={'marginTop': '10px', 'color': '#22c55e'})
                ]),

                # Right: The 2x3 Grid of Pollutants
                html.Div(id='pollutants-grid', style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '15px', 'width': '60%'})
            ])
        ]),

        # ZONE 6: RAIN
        html.Div(className='area-rain glass-card', children=[
            html.H2("Chances of Rain"),
            html.Div([html.P("Tonight: 10%"), html.Div(style={'height': '6px', 'background': '#334155', 'borderRadius': '3px'}, children=html.Div(style={'width': '10%', 'height': '100%', 'background': '#3b82f6', 'borderRadius': '3px'}))]),
            html.Div(style={'marginTop': '15px'}, children=[html.P("Tomorrow: 30%"), html.Div(style={'height': '6px', 'background': '#334155', 'borderRadius': '3px'}, children=html.Div(style={'width': '30%', 'height': '100%', 'background': '#3b82f6', 'borderRadius': '3px'}))])
        ])
    ]),

    # ERROR MESSAGE (Hidden unless needed)
    html.Div(id='error-log', style={'color': 'red', 'textAlign': 'center', 'marginTop': '20px'})
])

# --- HELPER: Returns a colored dot + value for the AQI grid ---
def create_pollutant_card(label, value):
    # Simple color logic
    color = "#22c55e" # Green
    if value > 100: color = "#eab308" # Yellow
    if value > 200: color = "#ef4444" # Red
    
    return html.Div(style={'display': 'flex', 'alignItems': 'center'}, children=[
        html.Div(style={'width': '8px', 'height': '8px', 'borderRadius': '50%', 'backgroundColor': color, 'marginRight': '10px'}),
        html.Div([
            html.P(str(value), style={'fontWeight': 'bold', 'fontSize': '1.1rem', 'margin': 0}),
            html.P(label, style={'fontSize': '0.7rem', 'color': '#94a3b8', 'margin': 0})
        ])
    ])

# --- CALLBACK ---
@app.callback(
    [Output('city-name', 'children'), Output('temp-main', 'children'), Output('condition-main', 'children'),
     Output('val-hum', 'children'), Output('val-wind', 'children'), Output('val-vis', 'children'), Output('val-press', 'children'),
     Output('weekly-strip', 'children'), Output('main-chart', 'figure'),
     Output('val-sunrise', 'children'), Output('val-sunset', 'children'),
     Output('aqi-badge', 'children'), Output('aqi-text', 'children'), Output('pollutants-grid', 'children'),
     Output('error-log', 'children')],
    [Input('search-btn', 'n_clicks')], [State('city-input', 'value')]
)
def update_dashboard(n, city):
    if not city: city = "Bangalore"
    
    try:
        # 1. Fetch Data
        w = get_weather(city)
        c_data, d_data = get_forecast(city)
        
        if "error" in w:
            return ["Error"] * 14 + [f"API Error: {w['error']}"]

        # 2. Build Weekly Strip
        weekly_cards = []
        for day in d_data:
            weekly_cards.append(html.Div(className='day-card', children=[
                html.P(day['day'], style={'fontSize': '0.8rem', 'margin': '0'}),
                html.Img(src=f"http://openweathermap.org/img/w/{day['icon']}.png", style={'width': '40px'}),
                html.P(f"{day['temp']}°", style={'fontWeight': 'bold', 'margin': '0'})
            ]))
        
        # 3. Build Chart
        if c_data:
            fig = px.line(pd.DataFrame(c_data), x='time', y='temp', markers=True)
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', 
                            margin=dict(l=20,r=20,t=10,b=20), xaxis_showgrid=False, yaxis_showgrid=True, 
                            yaxis_gridcolor='rgba(255,255,255,0.1)', height=180)
            fig.update_traces(line_color='#3b82f6', line_shape='spline', fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.2)')
        else:
            fig = px.line(title="No Data")

        # 4. Build AQI Grid (The new layout)
        aqi = get_aqi(w['lat'], w['lon'])
        comp = aqi.get('comp', {})
        
        # We manually select the 6 key pollutants to match your image
        pollutant_ui = [
            create_pollutant_card("PM10", comp.get("pm10", 0)),
            create_pollutant_card("O3", comp.get("o3", 0)),
            create_pollutant_card("SO2", comp.get("so2", 0)),
            create_pollutant_card("PM2.5", comp.get("pm2_5", 0)),
            create_pollutant_card("CO", comp.get("co", 0)),
            create_pollutant_card("NO2", comp.get("no2", 0)),
        ]

        aqi_val = aqi.get('val', 0)
        aqi_status = "Good" if aqi_val < 3 else "Poor"

        return (
            w['city'], f"{w['temp']}°C", w['condition'],
            f"{w['humidity']}%", f"{w['wind_speed']} km/h", f"{w['visibility']} km", f"{w['pressure']} hPa",
            html.Div(className='weekly-container', children=weekly_cards), 
            fig, w['sunrise'], w['sunset'], 
            f"{aqi_val}", aqi_status, pollutant_ui,
            "" # No Error
        )

    except Exception as e:
        print("CRITICAL ERROR:", traceback.format_exc())
        return ["Error"] * 14 + [f"System Crash: {str(e)}"]

if __name__ == '__main__':
    app.run(debug=True)