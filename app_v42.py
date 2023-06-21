# -*- coding: utf-8 -*-
import io
import os
import json
import base64
import datetime
import requests
import pathlib
import math
import pandas as pd
import flask
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.plotly as py
import plotly.graph_objs as go
from sklearn.linear_model import LinearRegression
import base64
from dash.dependencies import Input, Output, State
from plotly import tools
from utils_trace import *

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],
)
app.title = "NiChart"
server = app.server
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()

#####################################################
## Hard coded parameters
## FIXME : this part will be modified in final version
NUM_PLOTS = 4

## Initial reference data files
##  csv files used as reference; users can upload additional ones
dsets_ref = {
    "Dset1_n100": pd.read_csv(DATA_PATH.joinpath("Dset1_n100.csv"), index_col=1).to_dict('records'),
    "Dset2_n100": pd.read_csv(DATA_PATH.joinpath("Dset2_n100.csv"), index_col=1).to_dict('records'),
}

## Initial user data files
##  csv files with user data; normally users will upload them
dsets_user = {
    "Dset2_n100": pd.read_csv(DATA_PATH.joinpath("Dset2_n100.csv"), index_col=1).to_dict('records'),
}

## Get ROI names
tmp_col = pd.DataFrame.from_dict(list(dsets_ref.values())[0]).columns
ROI_NAMES = tmp_col[tmp_col.str.contains('MUSE')].tolist()
#####################################################

## List of plot names
plot_names = ["Plot" + str(i+1) for i in range(NUM_PLOTS)]

#####################################################
## Functions to create different parts of the dashboard

def create_plot(dset, type_trace, type_plotlayer, roi):
    ''' Create a figure for a single plot (generated using user selections)
    '''

    ## Set x, y variables for the plot
    ##   FIXME   x var is hard-coded for now
    xvar = 'Age_At_Visit'
    yvar = roi

    # Get data
    if isinstance(dset, pd.DataFrame) == False:
        dset = pd.DataFrame.from_dict(dset)

    sel_plot_layers = []
    row = 1

    if len(type_plotlayer) > 0:
        for sel_layer in type_plotlayer:
            sel_plot_layers.append(sel_layer)

    fig = tools.make_subplots(
        rows=row,
        shared_xaxes=True,
        shared_yaxes=True,
        cols=1,
        print_grid=False,
        vertical_spacing=0.12,
    )

    # Add main trace (style) to figure
    fig.append_trace(eval(type_trace)(dset, xvar, yvar), 1, 1)

    # Add layers 
    for sel_layer in sel_plot_layers:
        fig = eval(sel_layer)(dset, xvar, yvar, fig)

    fig["layout"][
        "uirevision"
    ] = "The User is always right"  # Ensures zoom on graph is the same on update
    fig["layout"]["margin"] = {"t": 50, "l": 50, "b": 50, "r": 25}
    fig["layout"]["autosize"] = True
    fig["layout"]["height"] = 400
    fig["layout"]["xaxis"]["rangeslider"]["visible"] = False
    fig["layout"]["xaxis"]["tickformat"] = "%H:%M"
    fig["layout"]["yaxis"]["showgrid"] = True
    fig["layout"]["yaxis"]["gridcolor"] = "#3E3F40"
    fig["layout"]["yaxis"]["gridwidth"] = 1
    fig["layout"].update(paper_bgcolor="#21252C", plot_bgcolor="#21252C")

    return fig

def create_div_plot(curr_plot):
    ''' Returns html div for a single plot
    '''
    return html.Div(
        id = curr_plot + "_graph_div",
        
        className="display-none",               ## This is used to make figure visible/non-visible
        #className="chart-style six columns",
        
        children=[
            # Menu for the plot
            html.Div(
                id = curr_plot + "menu",
                #className="not_visible",
                className="visible",                
                children=[
                    # stores current menu tab
                    html.Div(
                        id = curr_plot + "menu_tab",
                        children=["PlotLayers"],
                        style={"display": "none"},
                    ),
                    html.Span(
                        "Style",
                        id = curr_plot + "style_header",
                        className="span-menu",
                        n_clicks_timestamp=2,
                    ),
                    html.Span(
                        "PlotLayers",
                        id = curr_plot + "plot_layers_header",
                        className="span-menu",
                        n_clicks_timestamp=1,
                    ),
                    # PlotLayers Checklist
                    html.Div(
                        id = curr_plot + "plot_layers_tab",
                        children=[
                            dcc.Checklist(
                                id = curr_plot + "plot_layers",
                                options=[
                                    {"label": "Lin Reg", "value": "linreg_trace"},
                                    {"label": "Lowess Reg", "value": "lowess_trace"},
                                ],
                                value=[],
                            )
                        ],
                        style={"display": "none"},
                    ),
                    # Styles checklist
                    html.Div(
                        id = curr_plot + "style_tab",
                        children=[
                            dcc.RadioItems(
                                id=curr_plot + "plot_type",
                                options=[
                                    {"label": "dots", "value": "dots_trace"},
                                    {"label": "bar", "value": "bar_trace"},
                                ],
                                value="dots_trace",
                            )
                        ],
                    ),
                ],
            ),
            # Chart Top Bar
            html.Div(
                className="row chart-top-bar",
                children=[
                    html.Span(
                        id = curr_plot + "_menu_button",
                        className="inline-block chart-title",
                        children=f"{curr_plot} ☰",
                        n_clicks=0,
                    ),
                    # Dropdown and close button float right
                    html.Div(
                        className="graph-top-right inline-block",
                        children=[
                            html.Div(
                                className="inline-block",
                                children=[
                                    dcc.Dropdown(
                                        className="dropdown-roi",
                                        id = curr_plot + "dropdown_plot_refdata",
                                        clearable=False,
                                        #placeholder="Reference Data",
                                    )
                                ],
                            ),
                            html.Div(
                                className="inline-block",
                                children=[
                                    dcc.Dropdown(
                                        className="dropdown-roi",
                                        id = curr_plot + "dropdown_plot_userdata",
                                        clearable=False,
                                        #placeholder="User Data",
                                    )
                                ],
                            ),
                            html.Div(
                                className="inline-block",
                                children=[
                                    dcc.Dropdown(
                                        className="dropdown-roi",
                                        id = curr_plot + "dropdown_roi",
                                        options=[
                                            {'label': i, 'value': i} for i in ROI_NAMES
                                        ],
                                        value = ROI_NAMES[0],
                                        placeholder="ROI",                                        
                                        clearable=False,
                                    )
                                ],
                            ),
                            html.Span(
                                id = curr_plot + "_close",
                                className = "chart-close inline-block float-right",
                                children = "×",
                                n_clicks = 0,
                            ),
                        ],
                    ),
                ],
            ),
            # Graph div
            html.Div(
                dcc.Graph(
                    id = curr_plot + "chart",
                    className="chart-graph",
                    config={"displayModeBar": False, "scrollZoom": True},
                )
            ),
        ],
    )
                
# Set a hidden var to keep plot visibility status
def get_plot_vis(curr_plot):
    if curr_plot in ["Plot1"]:
        return html.Div(
            id=curr_plot + "_vis_stat",
            n_clicks = 1
        )                
    else:
        return html.Div(
            id=curr_plot + "_vis_stat",
            n_clicks = 0
        )                

# Dash App Layout
app.layout = html.Div(
    className="row",
    children=[

        # Left Panel Div
        html.Div(
            className="three columns div-left-panel",
            children=[

                # Div for Left Panel App Info
                html.Div(
                    className="div-info",
                    children=[
                        html.H2(className="title-header", children="NiChart"),
                        html.A(
                            html.Img(
                                className="logo",
                                src=app.get_asset_url("nichart_logo_v1.png"),
                            ),
                            href="https://www.med.upenn.edu/cbica/nichart/",
                        ),
                    ],
                ),

                # Div for uploading reference data file(s)
                html.Div([
                    html.Div('Upload reference data file(s) (csv): ', 
                             style={'color': 'yellow', 'fontSize': 14}),
                    dcc.Upload(
                        id='upload_data_ref',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select Files')
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px'
                        },
                        # Allow multiple files to be uploaded
                        multiple=True
                    ),
                    dcc.Store(id = 'store_data_ref', data = dsets_ref),
                ]),

                # Div for uploading user data file(s)
                html.Div([
                    html.Div('Upload user data file(s) (csv): ', 
                             style={'color': 'yellow', 'fontSize': 14}),
                    dcc.Upload(
                        id='upload_data_user',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select Files')
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px'
                        },
                        # Allow multiple files to be uploaded
                        multiple=True
                    ),
                    dcc.Store(id = 'store_data_user', data = dsets_user),
                ]),

                # Div for showing ref data files info
                html.Div([
                    html.Div('Reference data info: ', style={'color': 'red', 'fontSize': 14}),

                    # Dropdown file list
                    html.Div(
                        className="graph-top-right inline-block",
                        children=[
                            html.Div(
                                className="inline-block",
                                children=[
                                    dcc.Dropdown(
                                        className="dropdown-roi",
                                        id = "dropdown_data_ref",
                                        options=[
                                            {'label': i, 'value': i} for i in list(dsets_ref.keys())
                                        ],
                                        value = list(dsets_ref.keys())[0],
                                        clearable=False,
                                    )
                                ],
                            ),
                        ],
                    ),
                                        
                    ### FIXME
                    dcc.Textarea(value = 'TODO: Add here info about selected ref df', 
                                 className='my-class', 
                                 id='text_ref_df'
                                ),
                ]),
                                        
                # Div for showing user data files info
                html.Div([
                    html.Div('User data info: ', style={'color': 'red', 'fontSize': 14}),

                    # Dropdown file list
                    html.Div(
                        className="graph-top-right inline-block",
                        children=[
                            html.Div(
                                className="inline-block",
                                children=[
                                    dcc.Dropdown(
                                        className="dropdown-roi",
                                        id = "dropdown_data_user",
                                        options=[
                                            {'label': i, 'value': i} for i in list(dsets_user.keys())
                                        ],
                                        value = list(dsets_user.keys())[0],
                                        clearable=False,
                                    )
                                ],
                            ),
                        ],
                    ),
                                        
                    ### FIXME
                    dcc.Textarea(value = 'TODO: Add here info about selected user df', 
                                 className='my-class', 
                                 id='text_user_df'
                                ),
                ]),
                 
                # Div for new plot button
                html.Div([
                    html.Button(
                        id = "new_plot_button",
                        children = "New Plot",
                        n_clicks = 0,
                    )
                ]),
                    
                # Hidden div to keep info for visible/hidden plots
                html.Div(
                        id="plots-vis",
                        children=[get_plot_vis(curr_plot) for curr_plot in plot_names],
                ),
                    
            ],
                    
        ),

        # Right Panel Div with plots
        html.Div(
            className="nine columns div-right-panel",
            children=[

                # Charts Div
                html.Div(
                    id="charts",
                    className="row",
                    children=[create_div_plot(curr_plot) for curr_plot in plot_names],
                ),
            ],
        ),

        # Hidden div that stores all clicked plots
        html.Div(id="plots_visible", children = 'Plot1', style={"display": "none"}),
        
        # Hidden div that stores all clicked plots
        html.Div(id="plots_visible_arr", children = ['Plot1'], style={"display": "none"}),
        
    ],
)

##########################################################################
# Dynamic Callbacks
##########################################################################

# Updates if plots are visible/non-visible (returns a list of active plots)
def generate_change_plot_vis_callback():
    def change_plot_vis_callback(*args):

        changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
        vis_arr = args[-1]

        ## Add new plot
        if 'new_plot_button' in changed_id:
            for tmp_plot in plot_names:
                if tmp_plot not in vis_arr:
                    vis_arr = vis_arr + [tmp_plot]
                    return vis_arr
                    
        ## Delete plot
        #for i in range(1, len(plot_names)+1):
        for i in range(0, len(plot_names)):
            curr_plot = plot_names[i]
            if curr_plot + "_close" in changed_id:
                vis_arr = [x for x in vis_arr if x != curr_plot]
        return vis_arr
            
    return change_plot_vis_callback

# Function to update plot figure
def generate_figure_callback(curr_plot):
    def chart_fig_callback(plot_type, plot_layers, sel_roi, sel_file, data_store):
        curr_dset = pd.DataFrame.from_dict(data_store[sel_file])
        if curr_dset is None:
            return {"layout": {}, "data": {}}

        fig = create_plot(curr_dset, plot_type, plot_layers, sel_roi)
        return fig

    return chart_fig_callback


# Function to open or close Style or PlotLayers menus
def generate_open_close_menu_callback():
    def open_close_menu(n, className):
        if n == 0:
            return "not_visible"
        if className == "visible":
            return "not_visible"
        else:
            return "visible"

    return open_close_menu

# Function for hidden div that stores the last clicked menu tab
# Also updates style and plot_layers menu headers
def generate_active_menu_tab_callback():
    def update_current_tab_name(n_style, n_plot_layers):
        if n_style >= n_plot_layers:
            return "Style", "span-menu selected", "span-menu"
        return "PlotLayers", "span-menu", "span-menu selected"

    return update_current_tab_name


# Function show or hide plot_layers menu for chart
def generate_plot_layers_content_tab_callback():
    def plot_layers_tab(current_tab):
        if current_tab == "PlotLayers":
            return {"display": "block", "textAlign": "left", "marginTop": "30"}
        return {"display": "none"}

    return plot_layers_tab


# Function show or hide style menu for chart
def generate_style_content_tab_callback():
    def style_tab(current_tab):
        if current_tab == "Style":
            return {"display": "block", "textAlign": "left", "marginTop": "30"}
        return {"display": "none"}

    return style_tab

# Resize plotting div according to the number of plots displayed
def generate_plot_set_visibility_callback(curr_plot):
    def plot_set_visibility_callback(plots_visible_arr):
        if curr_plot not in plots_visible_arr:
            return "display-none"
        len_vis_plots = len(plots_visible_arr)
        classes = "chart-style"
        if len_vis_plots % 2 == 0:
            classes = classes + " six columns"
        elif len_vis_plots == 3:
            classes = classes + " four columns"
        else:
            classes = classes + " twelve columns"
        return classes
    return plot_set_visibility_callback

def generate_uploaded_dfs_callback():
    def uploaded_dfs_callback(dict_dfs):
        dict_options =  [{'label': i, 'value': i} for i in dict_dfs.keys()]
        return dict_options
    return uploaded_dfs_callback

######################################################
# Loop through all plots
for curr_plot in plot_names:
    
    ## Callback to make plot visible/invisible
    ## - This is done by modifying the className property of the plot
    ## - className sets the style to display the plot and is defined in the css  
    app.callback(
        Output(curr_plot + "_graph_div", "className"), 
        [Input("plots_visible_arr", "children")]
    )(generate_plot_set_visibility_callback(curr_plot))
    
    # Callback to update the plot drawing
    app.callback(
        Output(curr_plot + "chart", "figure"),
        [
            Input(curr_plot + "plot_type", "value"),
            Input(curr_plot + "plot_layers", "value"),            
            Input(curr_plot + "dropdown_roi", "value"),
        ],
        [
            State('dropdown_data_ref', 'value'),
            State('store_data_ref', 'data'),            
        ],
    )(generate_figure_callback(curr_plot))

    # Show or hide graph menu
    app.callback(
        Output(curr_plot + "menu", "className"),
        [Input(curr_plot + "_menu_button", "n_clicks")],
        [State(curr_plot + "menu", "className")],
    )(generate_open_close_menu_callback())

    # Callback to update menu and header visibility for a plot
    app.callback(
        [
            Output(curr_plot + "menu_tab", "children"),
            Output(curr_plot + "style_header", "className"),
            Output(curr_plot + "plot_layers_header", "className"),
        ],
        [
            Input(curr_plot + "style_header", "n_clicks_timestamp"),
            Input(curr_plot + "plot_layers_header", "n_clicks_timestamp"),
        ],
    )(generate_active_menu_tab_callback())

    # Callback to hide/show STYLE tab content
    app.callback(
        Output(curr_plot + "style_tab", "style"),
        [Input(curr_plot + "menu_tab", "children")]
    )(generate_style_content_tab_callback())

    # Callback to hide/show MENU tab content
    app.callback(
        Output(curr_plot + "plot_layers_tab", "style"), 
        [Input(curr_plot + "menu_tab", "children")]
    )(generate_plot_layers_content_tab_callback())
    
    app.callback(
        Output(curr_plot + "dropdown_plot_refdata", "options"),
        [
            Input("store_data_ref", "data"),
        ],
    )(generate_uploaded_dfs_callback())

    app.callback(
        Output(curr_plot + "dropdown_plot_userdata", "options"),
        [
            Input("store_data_user", "data"),
        ],
    )(generate_uploaded_dfs_callback())
    
######################################################


#######################################################
# Updates if a plot is visible/non-visible
# - "new plot button" clicked: make the first non-visible plot visible
# - "delete button" (x) on a plot is clicked: make the plot non-visible
app.callback(
    Output("plots_visible_arr", "children"), 
    [Input("new_plot_button", "n_clicks")] + 
    [Input(curr_plot + "_close", "n_clicks") for curr_plot in plot_names],
    [State("plots_visible_arr", "children")], 
)(generate_change_plot_vis_callback())
#######################################################


#######################################################
# Upload data files
### Read uploaded dfs
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            
    except Exception as e:
        return None

    df = df.to_dict(orient='records')
    return df

## Upload files
def generate_upload_data_callback():
    def upload_data_callback(list_of_names, list_of_contents, store_data):
        ## Initialize empty dictionary for the storage
        if store_data is None:
            store_data = {}
        
        ## Read data files
        dfs = []
        if list_of_contents is not None:
            dfs = [parse_contents(c, n) for c, n in zip(list_of_contents, list_of_names)]

        ## Add dfs to storage
        for i, tmp_df in enumerate(dfs):
            if tmp_df is not None:                
                tmp_name = list_of_names[i]
                if tmp_name in store_data.keys():
                    print('Warning: file already in storage, skipping !')
                else:
                    store_data[tmp_name] = tmp_df
        
        ## Return stored data
        return store_data
    return upload_data_callback
        
app.callback(
    Output("store_data_ref", "data"),
    [
        Input("upload_data_ref", "filename"),
        Input("upload_data_ref", "contents"),
    ],
    [
        State("store_data_ref", "data"),
    ],
)(generate_upload_data_callback())

app.callback(
    Output("store_data_user", "data"),
    [
        Input("upload_data_user", "filename"),
        Input("upload_data_user", "contents"),
    ],
    [
        State("store_data_user", "data"),
    ],
)(generate_upload_data_callback())
#######################################################


#######################################################
## Update dropdown lists (based on data stored for reference data files and user data files)
app.callback(
    Output("dropdown_data_ref", "options"),
    [
        Input("store_data_ref", "data"),
    ],
)(generate_uploaded_dfs_callback())

app.callback(
    Output("dropdown_data_user", "options"),
    [
        Input("store_data_user", "data"),
    ],
)(generate_uploaded_dfs_callback())
#######################################################


if __name__ == "__main__":
    app.run_server(debug=True)
