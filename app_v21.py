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

# List of plots
plot_names = ["Plot1", "Plot2", "Plot3", "Plot4"]

# Init ref data
dsets_ref = {
    "Dset1": pd.read_csv(DATA_PATH.joinpath("Dset1_n100.csv"), index_col=1).to_dict('records'),
    "Dset2": pd.read_csv(DATA_PATH.joinpath("Dset2_n100.csv"), index_col=1),
}

# Init user data
dsets_user = {
    "Dset2": pd.read_csv(DATA_PATH.joinpath("Dset2_n100.csv"), index_col=1).to_dict('records'),
}

## Tmp FIXME
tmp_col = pd.DataFrame.from_dict(dsets_ref['Dset1']).columns
#tmp_col = dsets_ref['Dset1'].columns
ROI_NAMES = tmp_col[tmp_col.str.contains('MUSE')].tolist()

## FIXME
# Left panel with data file info

def get_fig(dset, type_trace, type_plotlayer, roi):
    ''' Returns the figure
    '''

    # Get data
    #df = dsets_ref[dset]
    if isinstance(dset, pd.DataFrame) == False:
        dset = pd.DataFrame.from_dict(dset)
    
    print('kkkkkkkkkkkkkkkkkkkkkkkkkk')
    print(dset.shape)

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

    ## FIXME   hard coded x y for now
    xvar = 'Age_At_Visit'
    yvar = 'MUSE_GM'
    yvar = roi

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
    
    dset = dsets_ref['Dset1']
    
    return html.Div(
        id = curr_plot + "graph_div",
        className="display-none",
        children=[
            # Menu for Currency Graph
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
                                id=curr_plot + "chart_type",
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
                        id = curr_plot + "menu_button",
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
                                        id = curr_plot + "dropdown_roi",
                                        options=[
                                            {'label': i, 'value': i} for i in ROI_NAMES
                                        ],
                                        value = ROI_NAMES[0],
                                        clearable=False,
                                    )
                                ],
                            ),
                            html.Span(
                                id = curr_plot + "close",
                                className="chart-close inline-block float-right",
                                children="×",
                                n_clicks=0,
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
                        id='upload-data-ref',
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
                    #dcc.Store(id = 'store_df_ref', data = dsets_ref),
                ]),

                # Div for uploading user data file(s)
                html.Div([
                    html.Div('Upload user data file(s) (csv): ', 
                             style={'color': 'yellow', 'fontSize': 14}),
                    dcc.Upload(
                        id='upload-data-user',
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
                    #dcc.Store(id = 'store_df_user', data = dsets_user),
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
                                        id = "dropdown_df_ref",
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
                    dcc.Textarea(value = 'TODO: Temp info about selected ref df', 
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
                                        id = "dropdown_df_user",
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
                    dcc.Textarea(value = 'TODO: Temp info about selected user df', 
                                 className='my-class', 
                                 id='text_user_df'
                                ),
                ]),
            ],
        ),

        # Right Panel Div
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

        # Hidden div that stores all clicked charts
        html.Div(id="plots_visible"),
    ],
)

##########################################################################
# Dynamic Callbacks
##########################################################################

# returns string containing clicked charts
def generate_chart_button_callback():
    def chart_button_callback(*args):
        dsets = ""
        for i in range(len(plot_names)):
            if args[i] > 0:
                dset = plot_names[i]
                if dsets:
                    dsets = dsets + "," + dset
                else:
                    dsets = dset
        return dsets

    return chart_button_callback

# Function to update Graph Figure
def generate_figure_callback(curr_plot):
    #def chart_fig_callback(dsets, t, p, r, old_fig):
    def chart_fig_callback(dsets, t, p, r, dfl, dfd):


        curr_dset = pd.DataFrame.from_dict(dfd[dfl])

        print('OOOO')
        print(dfl)
        print(t)
        print(p)
        print(r)
        
        if curr_dset is None:
            return {"layout": {}, "data": {}}

        #dsets = dsets.split(",")
        #if dset not in dsets:
            #return {"layout": {}, "data": []}

        #if old_fig is None or old_fig == {"layout": {}, "data": {}}:
            #return get_fig(curr_dset, t, p, r)

        fig = get_fig(curr_dset, t, p, r)
        return fig

    return chart_fig_callback


# Function to close currency dset graph
def generate_close_graph_callback():
    def close_callback(n, n2):
        if n == 0:
            if n2 == 1:
                return 1
            return 0
        return 0

    return close_callback

# Function to open or close STYLE or STUDIES menu
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


# Resize dset div according to the number of charts displayed
def generate_show_hide_graph_div_callback(dset):
    def show_graph_div_callback(plots_visible):
        if dset not in plots_visible:
            return "display-none"

        plots_visible = plots_visible.split(",")  # [:4] max of 4 graph
        len_list = len(plots_visible)

        classes = "chart-style"
        if len_list % 2 == 0:
            classes = classes + " six columns"
        elif len_list == 3:
            classes = classes + " four columns"
        else:
            classes = classes + " twelve columns"
        return classes

    return show_graph_div_callback


# Generate Buy/Sell and Chart Buttons for Left Panel
def generate_contents_for_left_panel():
    def show_contents(n_clicks):
        if n_clicks is None:
            return "display-none", "row summary"
        elif n_clicks % 2 == 0:
            return "display-none", "row summary"
        return "row details", "row summary-open"

    return show_contents

# Loop through all plot_names
for curr_plot in plot_names:
    
    #print('aaaaeee')
    #print(dsets_ref['Dset1'])
    #print(curr_dset.shape)
    

    # Callback for Buy/Sell and Chart Buttons for Left Panel
    app.callback(
        [Output(curr_plot + "contents", "className"), Output(curr_plot + "summary", "className")],
        [Input(curr_plot + "summary", "n_clicks")],
    )(generate_contents_for_left_panel())

    # Callback for className of div for graphs
    app.callback(
        Output(curr_plot + "graph_div", "className"), [Input("plots_visible", "children")]
    )(generate_show_hide_graph_div_callback(curr_plot))

    # Callback to update the actual graph
    app.callback(
        Output(curr_plot + "chart", "figure"),
        [
            Input("plots_visible", "children"),
            Input(curr_plot + "chart_type", "value"),
            Input(curr_plot + "plot_layers", "value"),            
            Input(curr_plot + "dropdown_roi", "value"),
        ],
        [
            State('dropdown_files', 'value'),
            State('store_df_ref', 'data'),            
        ],
    )(generate_figure_callback(curr_plot))

    # close graph by setting to 0 n_clicks property
    app.callback(
        Output(curr_plot + "Button_chart", "n_clicks"),
        [Input(curr_plot + "close", "n_clicks")],
        [State(curr_plot + "Button_chart", "n_clicks")],
    )(generate_close_graph_callback())

    # show or hide graph menu
    app.callback(
        Output(curr_plot + "menu", "className"),
        [Input(curr_plot + "menu_button", "n_clicks")],
        [State(curr_plot + "menu", "className")],
    )(generate_open_close_menu_callback())

    # stores in hidden div name of clicked tab name
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

    # hide/show STYLE tab content if clicked or not
    app.callback(
        Output(curr_plot + "style_tab", "style"), [Input(curr_plot + "menu_tab", "children")]
    )(generate_style_content_tab_callback())

    # hide/show MENU tab content if clicked or not
    app.callback(
        Output(curr_plot + "plot_layers_tab", "style"), [Input(curr_plot + "menu_tab", "children")]
    )(generate_plot_layers_content_tab_callback())

# updates hidden div with all the clicked charts
app.callback(
    Output("plots_visible", "children"),
    [Input(dset + "Button_chart", "n_clicks") for dset in plot_names],
    [State("plots_visible", "children")],
)(generate_chart_button_callback())




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

def generate_upload_data_callback():
    def upload_data_callback(list_of_names, list_of_contents, store_data):
        
        ## Initialize empty dictionary for the storage
        if store_data is None:
            store_data = {}
        
        ## Read data files
        dfs = []
        if list_of_contents is not None:
            dfs = [
                parse_contents(c, n) for c, n in zip(list_of_contents, list_of_names)]

        ## Add dfs to storage
        for i, tmp_df in enumerate(dfs):
            if tmp_df is not None:                
                tmp_name = list_of_names[i]
                
                print('BBB')
                print(len(tmp_name))
                #input()
                
                if tmp_name in store_data.keys():
                    print('File already in storage, skipping !')
                else:
                    store_data[tmp_name] = tmp_df

        if store_data is not None:
            print('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAa')
            print(store_data.keys())
            #input()
        
        ## Return stored data
        return store_data
    return upload_data_callback
        
app.callback(
    Output("store_df_ref", "data"),
    #Output("output-data-upload", "children"),
    [
        Input("upload-data-ref", "filename"),
        Input("upload-data-ref", "contents"),
    ],
    [
        State("store_df_ref", "data"),
    ],
    #[State('upload-data-ref', 'filename')],
)(generate_upload_data_callback())


def generate_uploaded_dfs_callback():
    def uploaded_dfs_callback(dict_dfs):
        dict_options =  [{'label': i, 'value': i} for i in dict_dfs.keys()]
        return dict_options
        
    return uploaded_dfs_callback


app.callback(
    Output("dropdown_files", "options"),
    #Output("output-data-upload", "children"),
    [
        Input("store_df_ref", "data"),
    ],
    #[
        #State("uploaded_dfs", "children"),
    #],
)(generate_uploaded_dfs_callback())


if __name__ == "__main__":
    app.run_server(debug=True)