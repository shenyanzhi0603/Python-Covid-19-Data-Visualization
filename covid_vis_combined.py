import pandas as pd
import plotly.express as px 
import plotly.graph_objects as go
import plotly.io as pio
#pio.templates.default = "plotly_dark"

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from dash import callback_context

import requests
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import time

from urllib.request import urlopen
import json

#external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
external_stylesheets = ['assets/main.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server #allow heroku to find this app
# ------------------------------------------------------------------------------
# Import and clean data
header = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us/'
end = '.csv'

def check_latest_updated_date():
    counter = 0
    today_date = date.today()
    url = header + today_date.strftime("%m-%d-%Y") + end
    code = requests.get(url).status_code
    while code != 200:
        counter += 1
        today_date = today_date - relativedelta(days=counter)
        url = header + today_date.strftime("%m-%d-%Y") + end
        code = requests.get(url).status_code
    return today_date

base_date = check_latest_updated_date()

def get_data_df1():
    counter = 0
    df = pd.DataFrame()
    FIELDS_USE = ['Province_State', 'Confirmed', 'Deaths', 'Recovered', 'Active', 'FIPS', 'Incident_Rate',
       'Testing_Rate']

    while counter < 1000:
        current_date = base_date - relativedelta(days=counter)
        url = header + current_date.strftime("%m-%d-%Y") + end
        current_data = pd.read_csv(url)[FIELDS_USE]
        current_data['Date'] = current_date.strftime("%m-%d-%Y")
        df = df.append(current_data, ignore_index=True)
        if current_date.strftime("%m-%d-%Y") == '04-12-2020':
            break
        counter += 1

    df.set_index('Date', inplace=True, drop=False)
    return df

df1 = get_data_df1()
#import another file with states code
states1 = pd.read_csv("assets/us_state_code.csv")
df1 = pd.merge(df1, states1, how='inner', left_on='Province_State', right_on='state')

#order the dates
dates = list(df1['Date'].unique())
dates.reverse() #begin_to_end
begin_to_end_dates = dates
date_num = len(begin_to_end_dates)

#create the reference for slider markers
slider_dates = {}
for i in range(date_num):
    slider_dates[begin_to_end_dates[i]] =  i
slider_markers = {} #find marker dates
start = date(2020,4,12)
marker_date = date(year=start.year, month=start.month+1, day=1)
while base_date.year!=marker_date.year or base_date.month!=marker_date.month:
    slider_markers[marker_date] = slider_dates[marker_date.strftime("%m-%d-%Y")]
    if marker_date.month < 12:
        marker_date += relativedelta(months=1)
    else:
        marker_date = date(year=marker_date.year+1, month=1, day=1)
slider_markers[marker_date] = slider_dates[marker_date.strftime("%m-%d-%Y")]

### store max value for each category
axis_max_values = {'Confirmed':0, 'Deaths':0, 'Recovered':0, 'Active':0}
for k in axis_max_values.keys():
    value = df1.loc[:, "{}".format(k)].max().item()
    axis_max_values[k] = int(value)

### record the memory for button clicked if the fig updates
triggered_memory = {'button_id': 'btn_confirmed'} #initialize the default button selection, and renew the value when a new button is clicked on

###data preparation for line chart
def get_data_df2(i):
    current_date = base_date - relativedelta(days=i)
    url = header + current_date.strftime("%m-%d-%Y") + end
    df = pd.read_csv(url, encoding='utf-8')
    df['date'] = current_date.strftime("%m-%d-%Y")
    return df
#为了保证14天的新增都不为空，取到最近15天的数据情况
df2 = pd.concat([get_data_df2(i) for i in range(31)]) #15 for 2 weeks; 31 for 1 month
df2 = df2.drop(columns=["Country_Region","Last_Update","Lat","Long_","FIPS","People_Hospitalized","UID","ISO3","Hospitalization_Rate"])
df2 = df2.set_index(['Province_State'])
df2.sort_values(by=['date'],ascending=True,inplace=True)

states2=['Alabama', 'Alaska', 'American Samoa', 'Arizona', 'Arkansas',\
       'California', 'Colorado', 'Connecticut', 'Delaware', 'Diamond Princess',\
       'District of Columbia', 'Florida', 'Georgia', 'Grand Princess', 'Guam',\
       'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky',\
       'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan',\
       'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',\
       'New Hampshire', 'New Jersey', 'New Mexico', 'New York',\
       'North Carolina', 'North Dakota', 'Northern Mariana Islands', 'Ohio',\
       'Oklahoma', 'Oregon', 'Pennsylvania', 'Puerto Rico', 'Rhode Island',\
       'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah',\
       'Vermont', 'Virgin Islands', 'Virginia', 'Washington', 'West Virginia',\
       'Wisconsin', 'Wyoming']

def get_new(state):
    temp=df2.loc[state]
    date=temp['date']
    temp=temp.drop(columns='date').diff()
    temp=temp.add_suffix('_increased')
    temp['date']=date
    return temp
temp_df=pd.concat([get_new(state) for state in states2])
temp_df=temp_df.reset_index(drop=False)

df2.reset_index(drop=False)
df2=pd.merge(df2,temp_df,on=['Province_State','date'])

df2 = df2[['Province_State','date','Confirmed','Confirmed_increased','Deaths','Deaths_increased','Recovered','Recovered_increased']]
df2 = df2.set_index(['Province_State'])
traced_date = base_date - relativedelta(days=30) #14 for 2 weeks; 30 for 1 month
df2=df2[df2['date']!= traced_date]
df2=df2.fillna(0)

###data preparation for bar chart
def get_data_df3(i):
    current_date = base_date - relativedelta(days=i)
    url = header + current_date.strftime("%m-%d-%Y") + end
    df = pd.read_csv(url, encoding='utf-8')
    df=df.iloc[:,[0,1,5,6,7]]
    df['date'] = current_date.strftime("%m-%d-%Y")
    return df

first = date(2020,4,12)
interval = base_date - first

df3 = pd.concat([get_data_df3(i) for i in range(0,interval.days+1)])
df3.dropna(axis=0,how='any',inplace=True)
df3 = df3.sort_values(['date','Province_State'],ascending=True)
#prepare unique color for each state
states3 = list(df3['Province_State'].unique())
states_count = len(states3)
color_1 = [px.colors.qualitative.Alphabet[i] for i in range(26)]
color_2 = [px.colors.qualitative.Light24[i] for i in range(24)]
color_3 = [px.colors.qualitative.Dark24[i] for i in range(24)]
color_list = (color_1 + color_2 + color_3)*3  
color_list = color_list[:states_count]   

for state,color in zip(states3,color_list):
    df3.loc[df3['Province_State']==state,'color'] = color
#set the range of xaxis
max_confirm = axis_max_values['Confirmed']
max_death = axis_max_values['Deaths']

# get the top 15 states for both
dates_list = list(df3['date'].unique())
dates3 = [str(date) for date in dates_list]

def get_largest(date,mode): #mode: 'Confirmed' & 'Deaths'
    df = df3[df3['date']==date]
    df = df.nlargest(n=15,columns=[mode])
    df = df.sort_values(by=['date',mode])
    return df
largest_confirmed = pd.concat([get_largest(date,'Confirmed') for date in dates3])  
largest_deaths = pd.concat([get_largest(date,'Deaths') for date in dates3])  

# draw bar chart layout for confirmed cases
fig_dict_confirmed={
    "data":[],
    "layout":{},
    "frames":[],
}
fig_dict_confirmed['layout']['xaxis']=dict(range=[0,max_confirm*1.05],visible=False)
fig_dict_confirmed['layout']['yaxis']=dict(range=[-0.5, 15.5],autorange=False,tickfont=dict(size=14))
fig_dict_confirmed['layout']['hovermode']='y'
fig_dict_confirmed['layout']['template']='plotly_white'
fig_dict_confirmed['layout']['title']=dict(text="Top 15 States Confirmed: 04-12-2020",
                          font=dict(size=24),x=0.5,y=0.9,xanchor='center')

# draw bar chart layout for confirmed cases
fig_dict_deaths={
    "data":[],
    "layout":{},
    "frames":[],
}
fig_dict_deaths['layout']['xaxis']=dict(range=[0,max_death*1.05],visible=False)
fig_dict_deaths['layout']['yaxis']=dict(range=[-0.5, 15.5],autorange=False,tickfont=dict(size=14))
fig_dict_deaths['layout']['hovermode']='y'
fig_dict_deaths['layout']['template']='plotly_white'
fig_dict_deaths['layout']['title']=dict(text="Top 15 States Deaths: 04-12-2020",
                          font=dict(size=24),x=0.5,y=0.9,xanchor='center')

#add buttons for confirmed cases
fig_dict_confirmed['layout']['updatemenus']=[
            {"buttons":[
                    {"args":[None,{
                        "frame":{"duration":500,"redraw":True},
                        "fromcurrent": True,
                        "transition":{"duration":50,"easing":"quadratic-in-out"}}],
                    "label":"Play",
                    "method":"animate"},
                    
                    {"args":[[None],{
                        "frame":{"duration":0,"redraw":False},
                        "mode": "immediate",
                        "transition":{"duration":0}}],
                    "label":"Pause",
                    "method":"animate"},
                ],
            "direction":'left',
            "type":"buttons",
            "pad":{"r":5,"t":40},
            "showactive":False,
            "x":0,
            "xanchor":"right",
            "y":0,
            "yanchor":"top"}]

#add buttons for deaths
fig_dict_deaths['layout']['updatemenus']=[
            {"buttons":[
                    {"args":[None,{
                        "frame":{"duration":500,"redraw":True},
                        "fromcurrent": True,
                        "transition":{"duration":50,"easing":"quadratic-in-out"}}],
                    "label":"Play",
                    "method":"animate"},
                    
                    {"args":[[None],{
                        "frame":{"duration":0,"redraw":False},
                        "mode": "immediate",
                        "transition":{"duration":0}}],
                    "label":"Pause",
                    "method":"animate"},
            ],
            "direction":'left',
            "type":"buttons",
            "pad":{"r":5,"t":40},
            "showactive":False,
            "x":0,
            "xanchor":"right",
            "y":0,
            "yanchor":"top"}]

#make data for confirmed bar chart
fig_dict_confirmed['data']=[
    go.Bar(
        x = largest_confirmed[largest_confirmed['date']=='04-12-2020']['Confirmed'],
        y = largest_confirmed[largest_confirmed['date']=='04-12-2020']['Province_State'],
        orientation = 'h',
        text = largest_confirmed[largest_confirmed['date']=='04-12-2020']['Confirmed'],
        texttemplate='%{text:.3s}',
        textfont = {'size':12},
        textposition = 'outside',
        insidetextanchor='start',
        width = 1.0,
        marker = {'color':largest_confirmed[largest_confirmed['date']=='04-12-2020']['color']},
        hovertemplate = "Confirmed: %{x}"
    )
]

#make data for deaths bar chart
fig_dict_deaths['data']=[
    go.Bar( 
        x = largest_deaths[largest_deaths['date']=='04-12-2020']['Deaths'],
        y = largest_deaths[largest_deaths['date']=='04-12-2020']['Province_State'],
        orientation = 'h',
        text = largest_deaths[largest_deaths['date']=='04-12-2020']['Deaths'],
        texttemplate = '%{text:.3s}',
        textfont = {'size':12},
        textposition = 'outside',
        insidetextanchor = 'start',
        width = 1.0,
        marker = {'color':largest_deaths[largest_deaths['date']=='04-12-2020']['color']},
        hovertemplate = "Deaths: %{x}"
        )
]

#add sliders for both
sliders = [{
    "active":0,
    "yanchor":"top",
    "xanchor":"left",
    "visible":True,
    "currentvalue":{
        "font":{"size": 20},
        "prefix":"Date:",
        "visible":True,
        "xanchor":"right"
    },
    "transition":{"duration":50, "easing":"cubic-in-out"},
    "pad":{"b":10, "t":50},
    "len":0.9,
    "x":0.1,
    "y":0.12,
    "steps":[{
        "visible":True,
        "label":date,
        "method":"animate" ,       
        "args":[
        ['frame_{}'.format(date)],
        {"frame":{"duration":500, "redraw":True},
          "mode":"immediate",
          "transition":{"duration":50}}
        ]   
    } for date in dates3]
}]

#make frames -- confirmed
fig_dict_confirmed['frames']=[{
    'name':'frame_{}'.format(date),
    'data':[{
        'type':'bar',
        'x0':0,
        'x':largest_confirmed[largest_confirmed['date']==date]['Confirmed'],
        'y':largest_confirmed[largest_confirmed['date']==date]['Province_State'],
        'orientation':'h',
        'text':largest_confirmed[largest_confirmed['date']==date]['Confirmed'],
        'marker':{'color':largest_confirmed[largest_confirmed['date']==date]['color']},
        'hovertemplate':"Confirmed: %{x}"
    }],
    'layout':go.Layout(
                xaxis=dict(range=[0,max_confirm*1.05],visible=False),
                yaxis=dict(range=[-0.5, 15.5],autorange=False,tickfont=dict(size=14)),
                title=dict(text="Top 15 States Confirmed: "+str(date),
                          font=dict(size=24)),
                template="plotly_white",
                hovermode="y")
} for date in dates3]

#make frames -- deaths
fig_dict_deaths['frames']=[{
    'name':'frame_{}'.format(date),
    'data':[{
        'type':'bar',
        'x0':0,
        'x':largest_deaths[largest_deaths['date']==date]['Deaths'],
        'y':largest_deaths[largest_deaths['date']==date]['Province_State'],
        'orientation':'h',
        'text':largest_deaths[largest_deaths['date']==date]['Deaths'],
        'marker':{'color':largest_deaths[largest_deaths['date']==date]['color']},
        'hovertemplate':"Deaths: %{x}"
    }],
    'layout':go.Layout(
                xaxis=dict(range=[0,max_death*1.05],visible=False),
                yaxis=dict(range=[-0.5, 15.5],autorange=False,tickfont=dict(size=14)),
                title=dict(text="Top 15 States Deaths: "+str(date),
                          font=dict(size=24)),
                template="plotly_white",
                hovermode="y")
} for date in dates3]

fig_dict_confirmed['layout']['sliders'] = sliders
fig_bar_confirmed = go.Figure(fig_dict_confirmed)

fig_dict_deaths['layout']['sliders'] = sliders
fig_bar_deaths = go.Figure(fig_dict_deaths)

# ------------------------------------------------------------------------------
# App layout
app.layout = html.Div([
    dcc.Interval(
        id='my_interval',
        disabled=False, #if true the counter will no longer update
        n_intervals=0, #number of times the interval has passed
        interval=3600*1000, #increment the counter n_intervals every 60 minutes(60*60s=3600)*1000
        max_intervals=100, #number of times the interval will be fired
                            # if -1, the interval hs no limit(the default)
                            # if 0, the Interval stops running
    ),

    html.H3("COVID-19 Data Visualization Website", style={'text-align':'center'}),
    html.Div([
        html.H5("Last updated by: {} {} {}".format(date.today(), datetime.now().strftime("%X"), time.strftime('%Z', time.localtime())), style={'text-align':'center'}),
        html.P("the page auto updates per hour", style={'text-align':'center'})
    ], id="last_update_div"),
    html.Div([
        #add date slider
        dcc.Slider(
        id='date_slider',
        min=0, #error 因为min只能为number 去看slider documentation
        max=date_num-1,
        step=1,
        value=date_num-1,
        marks={loc: date for date,loc in slider_markers.items()},
        #tooltip={'always_visible':True, 'placement':'top'},
        updatemode='drag'
        ),
        #html.P("date: {}")
    ], style={'width':'98%', 'margin': "1%"}),

    html.Div([

        #choropleth map
        dcc.Graph(
            id='container_map',
            figure={},
            style={'display':'inline-block', 'width':'70%', 'height':550}), 

        html.Div([
            html.Div([
                html.Button('Confirmed', 
                    autoFocus=True,
                    id='btn_confirmed', 
                    n_clicks=0, 
                    style={'display': "block", 
                        'width': '80%', 
                        'height': '17%',
                        'text-align': 'center', 
                        'margin' : '8% auto'}),

                html.Button('Deaths',
                    id='btn_deaths',
                    n_clicks=0, 
                    style={'display': "block", 
                            'width': '80%',
                            'height': '17%', 
                            'text-align': 'center', 
                            'margin' : '8% auto'}),

                html.Button('Recovered', 
                    id='btn_recovered', 
                    n_clicks=0, 
                    style={'display': "block", 
                            'width': '80%', 
                            'height': '17%',
                            'text-align': 'center', 
                            'margin' : '8% auto'}),

                 html.Button('Active', 
                    id='btn_active', 
                    n_clicks=0, 
                    style={'display': "block", 
                            'width': '80%',
                            'height': '20%', 
                            'text-align': 'center', 
                            'margin' : '8% auto'})
            ], style={'width':'100%', 'padding': '30% auto'}),
        ], style={'display': 'block', 
                'width': '30%', 
                'margin': '0px',
                'text-align':'center',
                'float': 'right',
                'padding-top': '8%'
                }) #button div的style
    #dynamic graph+button的div
    ], style={'display':'block', 'text-align':'center', 'height':550, 'padding':'10% auto'}),

    #add the line chart
    html.Div([
        html.H3("COVID-19 Line Chart within latest 30 days", style={'text-align':'center'}),
        html.Br(),
        html.Div([
            dcc.Dropdown(
                id='state_select_dropdown',
                options=[
                    {'label': i, 'value': i} for i in states2
                ],
                placeholder='Please select a state'
                #value='Maryland'
            )
        ], style={'width':'90%', 'margin':'1% auto'}),
        dcc.Graph(id="line_chart", figure={})
    ], style={'width':'100%'}),

    #add the bar chart
    html.Div([
        html.Div([
            html.H3("Top States Ranking of the Cummulated Comfirmed Cases", style={'textAlign':'center'})
        ]),
        dcc.Graph(id="bar_chart_confirmed", figure=fig_bar_confirmed, style={'width':'48%', 'height':650, 'margin': "1%",'display':'inline-block'}),
        dcc.Graph(id="bar_chart_deaths", figure=fig_bar_deaths, style={'width':'48%', 'height':650, 'margin': "1%",'display':'inline-block'})
    ], style={'width':'98%', 'margin': "1%"})
    
])

# ------------------------------------------------------------------------------
"""
# App Callback: for the update div
@app.callback(
    Output(component_id='last_update_div', component_property='content'),
    [Input("my_interval", "n_intervals")]
    )
def update_div(n):
    pass
"""
# App Callback: for the chropleth map
@app.callback(
    #图形作为输出的载体
    Output('container_map', 'figure'),
    #slider作为输入的载体
    [Input('date_slider', 'value'),
    Input('btn_confirmed', 'n_clicks'),
    Input('btn_deaths', 'n_clicks'),
    Input('btn_recovered', 'n_clicks'),
    Input('btn_active', 'n_clicks'),
    Input("my_interval", "n_intervals")]
    )
#针对slider滑动操作的回调函数，输入参数为滑动条的当前值
def update_figure(selected_date_id, btn1, btn2, btn3, btn4, n):
    #从df中过滤出特定date的数据
    dff = df1.copy()
    dff = dff[dff['Date'] == begin_to_end_dates[selected_date_id]]
    
    ctx = dash.callback_context

    ctx_msg = json.dumps({
    'states': ctx.states,
    'triggered': ctx.triggered,
    'inputs': ctx.inputs
    }, indent=2)

    button_id_dict = {'btn_confirmed':'Confirmed', 'btn_deaths':'Deaths', 'btn_recovered':'Recovered', 'btn_active':'Active'}
    if not ctx.triggered:
        button_id = triggered_memory['button_id']
    else:
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if triggered_id not in button_id_dict.keys():
            #when user clicks on the time slider
            button_id = triggered_memory['button_id'] #retrace the clicked button memory
        else:
            button_id = triggered_id
            triggered_memory['button_id'] = button_id #renew the value of button_id in triggered_memory when a new button is clicked on

    #Plotly Express choropleth map based on button value
    fig = px.choropleth(
        data_frame = dff,
        locations = "code",
        locationmode = "USA-states",
        scope = "usa",
        color = button_id_dict[button_id],
        range_color = (0, axis_max_values[button_id_dict[button_id]]*1.05),
        hover_data = ['Date', 'Confirmed', 'Deaths', 'Recovered', 'Active'],
        #hover_data定义需展示的data column
        #hoverlabel定义label的样式
        hover_name = "state", # column to add to hover information
        color_continuous_scale=px.colors.sequential.Reds if button_id!='btn_recovered' else px.colors.sequential.Blues,
        labels = { button_id_dict[button_id] : '{} Number'.format(button_id_dict[button_id])},
        title = 'Date "'+begin_to_end_dates[selected_date_id]+'" - US Overview of Cumulated Cases by State'
    )
    fig.update_layout(
        font=dict(
            size=17,
            color="#2f3f4c"
        )
    )
    return fig


# App Callback: for line chart
@app.callback(
    Output(component_id='line_chart', component_property='figure'),
    [Input(component_id='state_select_dropdown', component_property='value'),
    Input("my_interval", "n_intervals")]
    )
def update_figure(selected_state,n):
    if selected_state is None:
        raise PreventUpdate
    else:
        #print(selected_state)
        fig=go.Figure()
        conf_new=df2.loc[selected_state,"Confirmed_increased"]
        death_new=df2.loc[selected_state,"Deaths_increased"]
        recov_new=df2.loc[selected_state,"Recovered_increased"]
        date = df2.loc[selected_state,"date"].values
        fig.add_trace(go.Scatter(x=date,y=conf_new,mode='lines+markers',name='Confirmed'))
        fig.add_trace(go.Scatter(x=date,y=death_new,mode='lines+markers',name='Deaths'))
        fig.add_trace(go.Scatter(x=date,y=recov_new,mode='lines+markers',name='Recovered'))
        fig.update_layout(title=dict(text='State "'+selected_state+'" - Newly Increased Cases in latest 30 days (per day)',font_size=24),
                        xaxis=dict(showline=True,showgrid=True,showticklabels=True,type='category'),
                        yaxis=dict(showline=True,showgrid=True,showticklabels=True))
        
        return fig


#-------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)

# develop process plan: 
# 1. express -> go -> mapbox for beauty
# 2. the slider of choropleth graphs -> time range by months/weeks(end as today) 
# 3. line charts dropdown -> try multiple choice dropdown and display sharing x-axis subplots 
# 4. time navigation and time range selector for confirmed & deaths of overall us/districts/states (display all at once or enable users select from a dropdown)


#fix bugs
#解决map legend range随时间变化问题
#解决map只有两周数据问题
#解决合并后module和class引用问题
#add dash callback timestamps
#加一个“页面正在加载”的提示 or 进度条
#自动更新 & 给刷新按钮