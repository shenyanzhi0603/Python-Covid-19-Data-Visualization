import pandas as pd
import datetime

file="https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us/"

def get_data(i):
    date=(datetime.date.today() + datetime.timedelta(days=-i)).strftime('%m-%d')
    df=pd.read_csv(file+date+"-2020.csv",encoding='utf-8')
    df=pd.DataFrame(df)
    df['date']=date
    return df
#为了保证14天的新增都不为空，取到最近15天的数据情况
data=pd.concat([get_data(i) for i in range(1,16)])
data=data.drop(columns=["Country_Region","Last_Update","Lat","Long_","FIPS","People_Hospitalized","UID","ISO3","Hospitalization_Rate"])
data=data.set_index(['Province_State'])
data.sort_values(by=['date'],ascending=True,inplace=True)

states=['Alabama', 'Alaska', 'American Samoa', 'Arizona', 'Arkansas',\
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
    temp=data.loc[state]
    date=temp['date']
    temp=temp.drop(columns='date').diff()
    temp=temp.add_suffix('_increased')
    temp['date']=date
    return temp
temp_df=pd.concat([get_new(state) for state in states])
temp_df=temp_df.reset_index(drop=False)

data.reset_index(drop=False)
df=pd.merge(data,temp_df,on=['Province_State','date'])

df=df[['Province_State','date','Confirmed','Confirmed_increased','Deaths','Deaths_increased','Recovered','Recovered_increased']]
df=df.set_index(['Province_State'])
date=(datetime.date.today() + datetime.timedelta(days=-15)).strftime('%m-%d')
df=df[df['date']!=date]
df=df.fillna(0)

import plotly.graph_objects as go
def line_chart(state):
    fig=go.Figure()
    conf_new=df.loc[state,"Confirmed_increased"]
    death_new=df.loc[state,"Deaths_increased"]
    recov_new=df.loc[state,"Recovered_increased"]
    date=df.loc[state,"date"].values
    fig.add_trace(go.Scatter(x=date,y=conf_new,mode='lines+markers',name='Confirmed'))
    fig.add_trace(go.Scatter(x=date,y=death_new,mode='lines+markers',name='Deaths'))
    fig.add_trace(go.Scatter(x=date,y=recov_new,mode='lines+markers',name='Recovered'))
    fig.update_layout(title=dict(text="COVID-19 in "+state+" - Recent 2 weeks",font_size=26),
                     xaxis=dict(title='Date',showline=True,showgrid=True,showticklabels=True,type='category'),
                     yaxis=dict(title='Newly Increased Number',showline=True,showgrid=True,showticklabels=True),
                     plot_bgcolor='#e0ebeb')
    fig.show()
    
for state in states:
    line_chart(state)   