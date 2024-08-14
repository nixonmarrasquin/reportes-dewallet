import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

# Datos de ejemplo para los gráficos circulares con etiquetas largas
labels1 = ['MONITOR LG 24"', 'PS5', 'COMPUTADOR ASUS MKYE3', 'MOUSE GENIUS M3']
values1 = [30, 20, 15, 35]

labels2 = ['WWWWWWWWW', 'XXXXXXXXXXXXXX', 'YYYYYYYYYY', 'ZZZZZZZZZZZZZZZZZZ']
values2 = [10, 40, 25, 25]

# Datos de ejemplo para el gráfico de barras
bar_x = ['Category A', 'Category B', 'Category C']
bar_y = [100, 200, 150]

# Estilos de fuente Montserrat Bold
title_style = {'font-family': 'Montserrat, sans-serif', 'font-weight': 'bold'}

# Paleta de colores azules
blue_palette = ['#1f77b4', '#aec7e8', '#7f7f7f', '#17becf']

# Crear aplicación Dash
app = dash.Dash(__name__)

# Función para crear un gráfico circular
def create_pie_chart(labels, values, title, colors):
    return dcc.Graph(
        figure={
            'data': [go.Pie(labels=labels, values=values, hole=0.3, marker=dict(colors=colors))],
            'layout': {
                'title': title,
                'font': title_style,
                'margin': {'l': 10, 'r': 10, 'b': 10, 't': 40},
                'legend': {'x': 1.0, 'y': 0.5, 'xanchor': 'left'}
            }
        }
    )

# Función para crear un gráfico de barras
def create_bar_chart(x, y, colors):
    return dcc.Graph(
        figure={
            'data': [go.Bar(x=x, y=y, marker=dict(color=colors))],
            'layout': {
                'title': 'Gráfico de Barras',
                'font': title_style
            }
        }
    )

# Diseño del dashboard
app.layout = html.Div(style={'font-family': 'Montserrat, sans-serif', 'max-width': '800px', 'margin': '0 auto'}, children=[
    html.H1('Dashboard', style=title_style),
    
    html.Div([
        html.Div(create_pie_chart(labels1, values1, 'Gráfico Circular 1', blue_palette), style={'width': '50%', 'display': 'inline-block'}),
        html.Div(create_pie_chart(labels2, values2, 'Gráfico Circular 2', blue_palette), style={'width': '50%', 'display': 'inline-block'}),
    ], style={'display': 'flex', 'justify-content': 'space-around'}),
    
    html.Div([
        create_bar_chart(bar_x, bar_y, blue_palette)
    ], style={'width': '100%', 'display': 'block', 'margin-top': '20px'}),
    
    html.Div([
        html.Div([
            html.H2('Valor Monetario y Aumento', style=title_style),
            html.H3('Valor: $100,000 (10% de aumento)', style=title_style)
        ], style={'width': '100%', 'display': 'block', 'margin-top': '20px'}),
        
        html.Div([
            html.H2('Productos Canjeados', style=title_style),
            html.H3('Cantidad: 500', style=title_style)
        ], style={'width': '100%', 'display': 'block', 'margin-top': '20px'}),
    ])
])

if __name__ == '__main__':
    app.run_server(debug=True)
