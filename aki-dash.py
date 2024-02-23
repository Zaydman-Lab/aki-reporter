"""
aki-dash.py

Mark A Zaydman
11/21/2022

Purpose: UI for aki-reporter package

Functions:

    make_maindashtable(df : pd.DataFrame)->dash_table.DataTable:
        '''Returns main dashtable of new aki samples'''

    make_scatterplot(specimen_table : pd.DataFrame,slct_row_name:list[str])->dcc.Graph:
        '''Returns graph of Cr vs time for selected MRN'''

    make_specdashtable(specimen_table : pd.DataFrame)->dash_table.DataTable:
        '''Returns dashtable of available specimen for selected MRN'''
        
    update_elements(slctd_mrn):
        '''Returns updated app elements based on user selections'''

"""


#%%

import dash  
import dash_bootstrap_components as dbc
from dash import ctx, dash_table , html, dcc
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import pickle
from datetime import datetime,timedelta
import dash_auth
import queries
import aki_analysis
import numpy as np



#%%

VALID_USERNAME_PASSWORD_PAIRS=dict(pd.read_csv('users.txt',header=None).values)

#%% Import data
df=queries.main()
df=aki_analysis.main(df)


#%% Helper functions
def make_maintable(df: pd.DataFrame)->pd.DataFrame:
    """Returns main table pandas dataframe"""
    filt_maintable=((df['aki_sample']!=False)&(df['NEW_RESULT_IND']!=0))
    cols_maintable={'NAME_FULL_FORMATTED':'NAME',
            'BIRTH_DT_TM':'DOB',
            'EPIC_MRN':'MRN',
            'PATIENT_SEX':'Sex',
            'ACCESSION':'Acc #',
            'DRAWN_DT_TM':'Drawn DTTM',
            'RECEIVED_DT_TM':'Received DTTM',
            'RESULT_VAL':'New Cr',
            'OUTPATIENT_BASELINE':'OP Base',
            'encounter_baseline': 'IP Base',
            'twoday_baseline':'48 Base',
            'mdrd_baseline':'MDRD Base',
            'aki_sample':'KDIGO'}
    main_table=df.loc[filt_maintable,cols_maintable.keys()].sort_values(by='DRAWN_DT_TM',ascending=False).drop_duplicates(subset='EPIC_MRN',keep='first').rename(columns=cols_maintable).reset_index(drop=True)
    main_table['Acc #']=main_table['Acc #'].str.slice(7)
    main_table['id']=main_table['MRN']
    main_table['Drawn DTTM']=main_table['Drawn DTTM'].dt.strftime("%Y-%m-%d %H:%M:%S")
    main_table['Received DTTM']=main_table['Received DTTM'].dt.strftime("%Y-%m-%d %H:%M:%S")
    main_table['DOB']=pd.to_datetime(main_table['DOB']).dt.strftime("%Y-%m-%d")
    main_table=main_table.drop_duplicates(subset=['MRN']).sort_values(by='MRN',ignore_index=True)
    return(main_table)

def make_maindashtable(main_table : pd.DataFrame)->dash_table.DataTable:
    """Returns main dashtable of new aki samples"""
    main_dashtable=dash_table.DataTable(
        id='main-dashtable',
        columns=[    
            {
                'name':'MRN',
                'id':'id',
                'deletable':False,
                'selectable':False,
                'hideable':True,
            },
            {
                'name':'NAME',
                'id':'NAME',
                'deletable':False,
                'selectable':False,
                'hideable':True,
            },
            {
                'name':'DOB',
                'id':'DOB',
                'deletable':False,
                'selectable':False,
                'hideable':True,
            },
            {
                'name':'Sex',
                'id':'Sex',
                'deletable':False,
                'selectable':False,
                'hideable':True,
            },
            {
                'name':'New Cr',
                'id':'New Cr',
                'deletable':False,
                'selectable':False,
                'hideable':True,
            },
            {
                'name':'OP Base',
                'id':'OP Base',
                'deletable':False,
                'selectable':False,
                'hideable':True,
            },
            {
                'name':'IP Base',
                'id':'IP Base',
                'deletable':False,
                'selectable':False,
                'hideable':True,
            },        
            {
                'name':'48 Base',
                'id':'48 Base',
                'deletable':False,
                'selectable':False,
                'hideable':True,
            },        
            {
                'name':'MDRD Base',
                'id':'MDRD Base',
                'deletable':False,
                'selectable':False,
                'hideable':True,
                'type':'numeric',
                'format': {'specifier': '.2f'}
            },
            {
                'name':'KDIGO',
                'id':'KDIGO',
                'deletable':False,
                'selectable':False,
                'hideable':True,
            },        
        ],
        data=main_table.to_dict('records'),  # the contents of the table
        hidden_columns=['NAME','DOB'],
        editable=True,              # allow editing of data inside all cells
        filter_action="native",     # allow filtering of data by user ('native') or not ('none')
        sort_action="native",       # enables data to be sorted per-column by user or not ('none')
        sort_mode="single",         # sort across 'multi' or 'single' columns
        column_selectable="multi",  # allow users to select 'multi' or 'single' columns
        row_selectable="single",     # allow users to select 'multi' or 'single' rows
        row_deletable=False,         # choose if user can delete a row (True) or not (False)
        selected_columns=[],        # ids of columns that user selects
        selected_rows=[],           # indices of rows that user selects
        page_action="native",       # all data is passed to the table up-front or not ('none')
        page_current=0,             # page number that user is on
        page_size=8,                # number of rows visible per page
    )
    return(main_dashtable)

def make_scatterplot(specimen_table : pd.DataFrame,colors)->dcc.Graph:
    '''Returns graph of Cr vs time for selected MRN'''
    outpatient_baseline=np.nan
    if len(specimen_table)>0:
        title=f'EPIC MRN = {specimen_table.MRN[0]}'
        outpatient_baseline=specimen_table['OP Base'][0]
    else: 
        title='EPIC MRN =          '
    fig=px.scatter(
        data_frame=specimen_table,
        x='Drawn DTTM',
        y='Cr',
        hover_data=['Acc #'],
        title=title
    )
    fig.update_layout(
        margin=dict(l=20,r=20,t=30,b=30)
    )
    fig.update_traces(
        marker_color=colors,
        marker={'size':10}
    )
    fig.add_vline(
        datetime.now()-timedelta(days=5),
            line=dict(
            color="black",
            width=0.75,
            dash="dash"
        )
    )
    if not np.isnan(outpatient_baseline):
        fig.add_trace(
            go.Scatter(
                x=[min(specimen_table['Drawn DTTM']),max(specimen_table['Drawn DTTM'])],
                y=[outpatient_baseline,outpatient_baseline],
                mode='lines',
                name='1.0x OP Base',
                line=dict(
                    color="#0000ff",
                    width=0.75,
                )
            )
        ),
        fig.add_trace(
            go.Scatter(
                x=[min(specimen_table['Drawn DTTM']),max(specimen_table['Drawn DTTM'])],
                y=[1.5*outpatient_baseline,1.5*outpatient_baseline],
                mode='lines',
                name='1.5x OP Base',
                line=dict(
                    color="#00FF00",
                    width=0.75,
                )
            )
        ),
        fig.add_trace(
            go.Scatter(
                x=[min(specimen_table['Drawn DTTM']),max(specimen_table['Drawn DTTM'])],
                y=[2*outpatient_baseline,2*outpatient_baseline],
                mode='lines',
                name='2.0x OP Base',
                line=dict(
                    color="#FFA500",
                    width=0.75,
                )
            )
        ),
        fig.add_trace(
            go.Scatter(
                x=[min(specimen_table['Drawn DTTM']),max(specimen_table['Drawn DTTM'])],
                y=[3*outpatient_baseline,3*outpatient_baseline],
                mode='lines',
                name='3.0x OP Base',
                line=dict(
                    color="#FF0000",
                    width=0.75,
                )
            )
        )
    return(dcc.Graph(id='scatter-plot',figure=fig))

def make_spectable(df:pd.DataFrame,slctd_mrn:list[str])->pd.DataFrame:
    filt_mrn=[x in slctd_mrn for x in df['EPIC_MRN']]
    dff=df.loc[filt_mrn]
    cols_spectable={'ACCESSION':'Acc #',
        'NAME_FULL_FORMATTED':'NAME',
        'BIRTH_DT_TM':'DOB',
        'DRAWN_DT_TM':'Drawn DTTM',
        'RECEIVED_DT_TM':'Received DTTM',
        'RESULT_VAL':'Cr',
        'EPIC_MRN':'MRN',
        'OUTPATIENT_BASELINE':'OP Base',
        'aki_sample':'KDIGO',
        'TUBE_TYPE':'Tube'}
    specimen_table=dff[cols_spectable.keys()].drop_duplicates().rename(columns=cols_spectable).reset_index(drop=True)
    specimen_table['Acc #']=specimen_table['Acc #'].str.slice(7)
    specimen_table['id']=specimen_table['Acc #']
    specimen_table['Drawn DTTM']=specimen_table['Drawn DTTM'].dt.strftime("%Y-%m-%d %H:%M:%S")
    specimen_table['Received DTTM']=specimen_table['Received DTTM'].dt.strftime("%Y-%m-%d %H:%M:%S")
    specimen_table['DOB']=pd.to_datetime(specimen_table['DOB']).dt.strftime("%Y-%m-%d")
    specimen_table=specimen_table.sort_values(by='Drawn DTTM',ascending=False,ignore_index=True)
    return(specimen_table)

def make_specdashtable(specimen_table : pd.DataFrame)->dash_table.DataTable:
    '''Returns dashtable of available specimen for selected MRN'''
    # week_ago = datetime.today() - timedelta(days=7)
    # week_agoDate = week_ago.strftime("%Y-%m-%d %H:%M:%S")
    specimen_dashtable=dash_table.DataTable(
        id='specimen-dashtable',
        columns=[
        {
            'name':'MRN',
            'id':'MRN',
            'deletable':False,
            'selectable':False,
            'hideable':True,
        },
        {
            'name':'NAME',
            'id':'NAME',
            'deletable':False,
            'selectable':False,
            'hideable':True,
        },
        {
            'name':'DOB',
            'id':'DOB',
            'deletable':False,
            'selectable':False,
            'hideable':True,
        },
        {
            'name':'Acc #',
            'id':'id',
            'deletable':False,
            'selectable':False,
            'hideable':True,
        },
        {
            'name':'Drawn DTTM',
            'id':'Drawn DTTM',
            'deletable':False,
            'selectable':False,
            'hideable':True,
        },
        {
            'name':'Received DTTM',
            'id':'Received DTTM',
            'deletable':False,
            'selectable':False,
            'hideable':True,
        },        
        {
            'name':'Cr',
            'id':'Cr',
            'deletable':False,
            'selectable':False,
            'hideable':True,
        },
        {
            'name':'OP Base',
            'id':'OP Base',
            'deletable':False,
            'selectable':False,
            'hideable':True,
        },        
        {
            'name':'KDIGO',
            'id':'KDIGO',
            'deletable':False,
            'selectable':False,
            'hideable':True,
        },       
        {
            'name':'Tube',
            'id':'Tube',
            'deletable':False,
            'selectable':False,
            'hideable':True,
        }              
    ],
    data=specimen_table.to_dict('records'),  # the contents of the table
    hidden_columns=['MRN','NAME','DOB','Drawn DTTM','OP Base'],
    editable=True,              # allow editing of data inside all cells
    filter_action="native",     # allow filtering of data by user ('native') or not ('none')
    sort_action="native",       # enables data to be sorted per-column by user or not ('none')
    sort_mode="single",         # sort across 'multi' or 'single' columns
    column_selectable="multi",  # allow users to select 'multi' or 'single' columns
    row_selectable="multi",     # allow users to select 'multi' or 'single' rows
    row_deletable=False,         # choose if user can delete a row (True) or not (False)
    selected_columns=[],        # ids of columns that user selects
    selected_rows=[],           # indices of rows that user selects
    page_action="native",       # all data is passed to the table up-front or not ('none')
    page_current=0,             # page number that user is on
    page_size=10,                # number of rows visible per page
    style_data_conditional=[
            # {
            #     'if': {
            #         'column_id' : 'Received DTTM',
            #         'filter_query': ('{Received DTTM} <' + week_agoDate)
            #     },
            #     'backgroundColor': 'white',
            #     'color': '#ed0909',
            # },                             
    ]
    )    
    return(specimen_dashtable)

def make_inventorydashtable(inventory_table : pd.DataFrame)->dash_table.DataTable:
    '''Returns dashtable of inventoried specimen'''
    inventory_dashtable=dash_table.DataTable(
        id='inventory-dashtable',
        columns=[
        {
            'name':'Acc #',
            'id':'Acc #',
            'deletable':False,
            'selectable':False,
            'hideable':True,
        },
        {
            'name':'NAME',
            'id':'NAME',
            'deletable':False,
            'selectable':False,
            'hideable':True,
        },
        {
            'name':'DOB',
            'id':'DOB',
            'deletable':False,
            'selectable':False,
            'hideable':True,
        },        
        {
            'name':'Drawn DTTM',
            'id':'Drawn DTTM',
            'deletable':False,
            'selectable':False,
            'hideable':True,
        },
        {
            'name':'Cr',
            'id':'Cr',
            'deletable':False,
            'selectable':False,
            'hideable':True,
        },
        {
            'name':'OP Base',
            'id':'OP Base',
            'deletable':False,
            'selectable':False,
            'hideable':True,
        },        
        {
            'name':'KDIGO',
            'id':'KDIGO',
            'deletable':False,
            'selectable':False,
            'hideable':True,
        },       
        {
            'name':'Tube',
            'id':'Tube',
            'deletable':False,
            'selectable':False,
            'hideable':True,
        }              
    ],
    data=inventory_table.to_dict('records'),  # the contents of the table
    hidden_columns=['MRN','Tube','OP Base'],
    editable=True,              # allow editing of data inside all cells
    filter_action="native",     # allow filtering of data by user ('native') or not ('none')
    sort_action="native",       # enables data to be sorted per-column by user or not ('none')
    sort_mode="single",         # sort across 'multi' or 'single' columns
    column_selectable="multi",  # allow users to select 'multi' or 'single' columns
    row_selectable="multi",     # allow users to select 'multi' or 'single' rows
    row_deletable=False,         # choose if user can delete a row (True) or not (False)
    selected_columns=[],        # ids of columns that user selects
    selected_rows=[],           # indices of rows that user selects
    page_action="native",       # all data is passed to the table up-front or not ('none')
    page_current=0,             # page number that user is on
    page_size=30,                # number of rows visible per page
    )    
    return(inventory_dashtable)



#%% Initialize App and authenticate user
app = dash.Dash(__name__, prevent_initial_callbacks=True,external_stylesheets=[dbc.themes.BOOTSTRAP]) # this was introduced in Dash version 1.12.0

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

##%% Callback functions ## need to add trigger context and not remake specimen table if that is what triggerd
@app.callback(
    [Output(component_id='plot-container', component_property='children'),
    Output(component_id='specimentable-container', component_property='children')],
    [Input(component_id='main-dashtable', component_property='derived_virtual_selected_row_ids'),
    Input('specimen-dashtable',component_property='selected_rows')])
def update_elements(slctd_mrn,slctd_rows):
    '''Updates app elements based on user selections'''
    specimen_table=make_spectable(df,slctd_mrn)
    if ctx.triggered_id == 'specimen-dashtable':
        colors=["#808080" if row['Acc #'] not in specimen_table.loc[slctd_rows,'Acc #'].values else '#3498DB' for i,row in specimen_table.iterrows() ]
        return([
            make_scatterplot(specimen_table,colors),
            dash.no_update
        ])
    else:
        colors=["#808080" for i,row in specimen_table.iterrows() ]
        return([
            make_scatterplot(specimen_table,colors),
            make_specdashtable(specimen_table)
    ])

    
@app.callback(
    Output('main-dashtable', 'style_data_conditional'),
    [Input('main-dashtable', 'selected_rows')]
)
def highlight_slctdrowmain(selected_rows):
    return [{
        'if': {'row_index': i},
        'background_color': '#D2F3FF'
    } for i in selected_rows]

@app.callback(
    Output('specimen-dashtable', 'style_data_conditional'),
    Input('specimen-dashtable', 'selected_rows')
)
def highlight_slctdrowspec(selected_rows):
    return [{
        'if': {'row_index': i},
        'background_color': '#D2F3FF'
    } for i in selected_rows]

@app.callback(
    Output('inventorytable-container', 'children'),
    Input('inventory-button', 'n_clicks'),
    State('inventory-dashtable','data'),
    State('specimen-dashtable','data'),
    State('specimen-dashtable','selected_rows')
)
def update_inventory(_,inventory,data,slctd_rows):
    dff=pd.DataFrame(data).iloc[slctd_rows]
    new_inventory_table=pd.concat([pd.DataFrame(inventory),dff],axis=0).drop_duplicates().reset_index(drop=True)
    return(make_inventorydashtable(new_inventory_table))

@app.callback(
    Output("download-inventory-csv", "data"),
    Input("download-button", "n_clicks"),
    State('inventory-dashtable','data'),
    prevent_initial_call=True,
)
def func(_,data):
    dff=pd.DataFrame(data)
    return dcc.send_data_frame(dff.to_csv, f"{datetime.now().strftime('%Y%m%d %H%M')} AKI_samples.csv")


app.layout = dbc.Container([
    html.H1(children='AKI specimen finder v0.0'),
    html.Div(f"Last data refresh: {datetime.now().strftime('%D %I:%m:%p')}"),
    html.Br(),
    dbc.Row(make_maindashtable(make_maintable(df))),
    dbc.Row([
        dbc.Col(make_scatterplot(make_spectable(df,[]),[]),id='plot-container',width=5),
        dbc.Col(make_specdashtable(make_spectable(df,[])),id='specimentable-container',width=7)   
    ],
    align='start',
    className='g-0 mt-0'),
    dbc.Row(
        [dbc.Col(width=10),
        dbc.Col(html.Button('Inventory selected rows',id='inventory-button',n_clicks=0))]
    ),
    dbc.Row(make_inventorydashtable(make_spectable(df,[])),id='inventorytable-container'),
    dbc.Row(
        [dbc.Col(width=10),
        dbc.Col(html.Button('Download inventory',id='download-button',n_clicks=0)),
        dcc.Download(id="download-inventory-csv")]
    ),
    html.Br(),
    html.Div('Created by Mark A Zaydman (zaydmanm@wustl.edu)'),
])

##%% Run app

if __name__ == '__main__':
    app.run_server(host='0.0.0.0',port=8088)
    
    

# %%