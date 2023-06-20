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

# Loading historical tick data
data_dfs = {
    "Plot1": pd.read_csv(
        DATA_PATH.joinpath("EURUSD.csv.gz"), index_col=1, parse_dates=["Date"]
    ),
    "Plot2": pd.read_csv(
        DATA_PATH.joinpath("USDJPY.csv.gz"), index_col=1, parse_dates=["Date"]
    ),
    "Plot3": pd.read_csv(
        DATA_PATH.joinpath("GBPUSD.csv.gz"), index_col=1, parse_dates=["Date"]
    ),
    "Plot4": pd.read_csv(
        DATA_PATH.joinpath("USDCHF.csv.gz"), index_col=1, parse_dates=["Date"]
    ),
}

# List of plots
plot_names = ["Plot1", "Plot2", "Plot3", "Plot4"]

# Loading roi data
dsets_data = {
    "Dset1": pd.read_csv(DATA_PATH.joinpath("Dset1_n100.csv"), index_col=1),
    #"Dset2": pd.read_csv(DATA_PATH.joinpath("Dset2_n100.csv"), index_col=1),
}

dsets_data2 = {
    "Dset1": pd.read_csv(DATA_PATH.joinpath("Dset1_n100.csv"), index_col=1).to_dict('records'),
    #"Dset2": pd.read_csv(DATA_PATH.joinpath("Dset2_n100.csv"), index_col=1),
}

# Currency dsets
dsets = ["Dset1"]

tmp_col = dsets_data['Dset1'].columns
ROI_NAMES = tmp_col[tmp_col.str.contains('MUSE')].tolist()

# Return GM WM mean values
def roi_mean_gm(dfs, df_name):
    df = dfs[df_name]
    df = pd.DataFrame.from_dict(dfs[df_name])
    meanGM = df['MUSE_GM'].mean()
    meanWM = df['MUSE_WM'].mean()
    return [df_name, meanGM, meanWM]

# Creates left panel rows for plots
def get_row(curr_plot):

    return html.Div(
        children=[
            # Summary
            html.Div(
                id = curr_plot + "summary",
                className = "row summary",
                n_clicks = 0,
                children = [
                    html.Div(
                        id = curr_plot + "row",
                        className="row",
                        children=[
                            html.P(
                                curr_plot,  # currency curr_plot name
                                id = curr_plot,
                                className = "three-col",
                            ),
                            html.P(
                                'FIXME',
                                id = curr_plot + "meanGM",
                                className="three-col",
                            ),
                            html.P(
                                'FIXME',
                                id = curr_plot + "meanWM",
                                className="three-col",
                            ),
                            html.Div(
                                curr_plot,
                                id = curr_plot + "index",
                                style={"display": "none"},
                            ),
                        ],
                    )
                ],
            ),
            # Contents
            html.Div(
                id = curr_plot + "contents",
                className="row details",
                children=[
                    # Button to display chart
                    html.Div(
                        className="button-dist",
                        children=[
                            html.Button(
                                id = curr_plot + "btnDist",
                                children="Dist",
                                n_clicks=0,
                            )
                        ],
                    ),
                    # Button to display chart
                    html.Div(
                        className="button-chart",
                        children=[
                            html.Button(
                                id = curr_plot + "Button_chart",
                                children="Chart",
                                n_clicks=1
                                #if curr_plot in ["Dset1", "Dset2"]
                                if curr_plot in []
                                else 0,
                                
                            )
                        ],
                    ),
                ],
            ),
        ]
    )

# Returns Top cell bar for header area
def get_top_bar_cell(cellTitle, cellValue):
    return html.Div(
        className="two-col",
        children=[
            html.P(className="p-top-bar", children=cellTitle),
            html.P(id=cellTitle, className="display-none", children=cellValue),
            html.P(children=human_format(cellValue)),
        ],
    )

# returns modal figure for a currency dset
def get_modal_fig(currency_dset, index):
    fig = tools.make_subplots(
        rows=2, shared_xaxes=True, shared_yaxes=False, cols=1, print_grid=False
    )

    fig.append_trace(ask_modal_trace(currency_dset, index), 1, 1)
    fig.append_trace(bid_modal_trace(currency_dset, index), 2, 1)

    fig["layout"]["autosize"] = True
    fig["layout"]["height"] = 375
    fig["layout"]["margin"] = {"t": 5, "l": 50, "b": 0, "r": 5}
    fig["layout"]["yaxis"]["showgrid"] = True
    fig["layout"]["yaxis"]["gridcolor"] = "#3E3F40"
    fig["layout"]["yaxis"]["gridwidth"] = 1
    fig["layout"].update(paper_bgcolor="#21252C", plot_bgcolor="#21252C")

    return fig

# Returns graph figure
def get_fig(dset, type_trace, type_plotlayer, roi):

    # Get data
    #df = dsets_data[dset]
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


# returns chart div
def chart_div(curr_plot):
    
    dset = dsets_data['Dset1']
    
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
                        html.A(
                            html.Img(
                                className="logo",
                                src=app.get_asset_url("dash-logo-new.png"),
                            ),
                            href="https://plotly.com/dash/",
                        ),
                        html.H6(className="title-header", children="NiChart"),
                        dcc.Markdown(
                            """
                            NiChart
                            """
                        ),
                    ],
                ),

                html.Div([
                    dcc.Upload(
                        id='upload-data',
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
                    dcc.Store(id = 'df_store',
                              data = dsets_data2
                              
                              ),
                    html.H4("Current dataset"),

                    # Dropdown file list
                    html.Div(
                        className="graph-top-right inline-block",
                        children=[
                            html.Div(
                                className="inline-block",
                                children=[
                                    dcc.Dropdown(
                                        className="dropdown-roi",
                                        id = "dropdown_files",
                                        options=[
                                            {'label': i, 'value': i} for i in ['Dset1']
                                        ],
                                        value = 'Dset1',
                                        clearable=False,
                                    )
                                ],
                            ),
                            #html.Span(
                                #id = "close",
                                #className="chart-close inline-block float-right",
                                #children="×",
                                #n_clicks=0,
                            #),
                        ],
                    ),

                ]),
                
                # File View Div
                html.Div(
                    className="div-df-toggles",
                    children=[
                        html.P(
                            id="live_clock",
                            className="three-col",
                            children = '',
                        ),
                        html.P(className="three-col", children="GM Volume"),
                        html.P(className="three-col", children="WM Volume"),
                        html.Div(
                            id="uploaded_dfs",
                            className="div-gm-wm",
                            children=[
                                get_row(curr_plot) for curr_plot in plot_names
                                #get_row(roi_mean_gm(dset)) for dset in []
                            ],
                        ),
                    ],
                ),
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
                    children=[chart_div(curr_plot) for curr_plot in plot_names],
                ),
            ],
        ),

        # Hidden div that stores all clicked charts
        html.Div(id="plots_clicked"),
        
        ## Hidden div for each dset that stores orders
        #html.Div(
            #children=[
                #html.Div(id = dset + "orders", style={"display": "none"})
                #for dset in plot_names
            #]
        #),
        #html.Div([modal(dset) for dset in plot_names]),

        ## Hidden Div that stores all orders
        #html.Div(id="orders", style={"display": "none"}),
    ],
)

# Dynamic Callbacks

# Replace currency dset row
def generate_ask_bid_row_callback(dset):
    def output_callback(n, i, bid, ask):
        return replace_row(dset, int(i), float(bid), float(ask))

    return output_callback


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


## Function to update Graph Figure
#def generate_figure_callbackOld(curr_plot):
    #def chart_fig_callback(n_i, p, t, s, dsets, a, b, old_fig):

        #if dsets is None:
            #return {"layout": {}, "data": {}}

        #dsets = dsets.split(",")
        #if dset not in dsets:
            #return {"layout": {}, "data": []}

        #if old_fig is None or old_fig == {"layout": {}, "data": {}}:
            #return get_fig(dset, a, b, t, s, p)

        #fig = get_fig(dset, a, b, t, s, p)
        #return fig

    #return chart_fig_callback

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


# Open Modal
def generate_modal_open_callback():
    def open_modal(n):
        if n > 0:
            return {"display": "block"}
        else:
            return {"display": "none"}

    return open_modal


# Function to close modal
def generate_modal_close_callback():
    def close_modal(n, n2):
        return 0

    return close_modal


# Function for modal graph - set modal SL value to none
def generate_clean_sl_callback():
    def clean_sl(n):
        return 0

    return clean_sl


# Function for modal graph - set modal SL value to none
def generate_clean_tp_callback():
    def clean_tp(n):
        return 0

    return clean_tp


# Function to create figure for Buy/Sell Modal
def generate_modal_figure_callback(dset):
    def figure_modal(index, n, old_fig):
        if (n == 0 and old_fig is None) or n == 1:
            return get_modal_fig(dset, index)
        return old_fig  # avoid to compute new figure when the modal is hidden

    return figure_modal


# Function updates the dset orders div
def generate_order_button_callback(dset):
    def order_callback(n, vol, type_order, sl, tp, dset_orders, ask, bid):
        if n > 0:
            t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            l = [] if dset_orders is None else json.loads(dset_orders)
            price = bid if type_order == "sell" else ask

            if tp != 0:
                tp = (
                    price + tp * 0.001
                    if tp != 0 and dset[3:] == "JPY"
                    else price + tp * 0.00001
                )

            if sl != 0:
                sl = price - sl * 0.001 if dset[3:] == "JPY" else price + sl * 0.00001

            order = {
                "id": dset + str(len(l)),
                "time": t,
                "type": type_order,
                "volume": vol,
                "symbol": dset,
                "tp": tp,
                "sl": sl,
                "price": price,
                "profit": 0.00,
                "status": "open",
            }
            l.append(order)

            return json.dumps(l)

        return json.dumps([])

    return order_callback


# Function to update orders
def update_orders(orders, current_bids, current_asks, id_to_close):
    for order in orders:
        if order["status"] == "open":
            type_order = order["type"]
            current_bid = current_bids[plot_names.index(order["symbol"])]
            current_ask = current_asks[plot_names.index(order["symbol"])]

            profit = (
                order["volume"]
                * 100000
                * ((current_bid - order["price"]) / order["price"])
                if type_order == "buy"
                else (
                    order["volume"]
                    * 100000
                    * ((order["price"] - current_ask) / order["price"])
                )
            )

            order["profit"] = "%.2f" % profit
            price = current_bid if order["type"] == "buy" else current_ask

            if order["id"] == id_to_close:
                order["status"] = "closed"
                order["close Time"] = datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                order["close Price"] = price

            if order["tp"] != 0 and price >= order["tp"]:
                order["status"] = "closed"
                order["close Time"] = datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                order["close Price"] = price

            if order["sl"] != 0 and order["sl"] >= price:
                order["status"] = "closed"
                order["close Time"] = datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                order["close Price"] = price
    return orders


# Function to update orders div
def generate_update_orders_div_callback():
    def update_orders_callback(*args):
        orders = []
        current_orders = args[-1]
        close_id = args[-2]
        args = args[:-2]  # contains list of orders for each dset + asks + bids
        len_args = len(args)
        current_bids = args[len_args // 3 : 2 * len_args]
        current_asks = args[2 * len_args // 3 : len_args]
        args = args[: len_args // 3]
        ids = []

        if current_orders is not None:
            orders = json.loads(current_orders)
            for order in orders:
                ids.append(
                    order["id"]  # ids that allready have been added to current orders
                )

        for list_order in args:  # each currency dset has its list of orders
            if list_order != "[]":
                list_order = json.loads(list_order)
                for order in list_order:
                    if order["id"] not in ids:  # only add new orders
                        orders.append(order)
        if len(orders) == 0:
            return None

        # we update status and profit of orders
        orders = update_orders(orders, current_bids, current_asks, close_id)
        return json.dumps(orders)

    return update_orders_callback


# Resize dset div according to the number of charts displayed
def generate_show_hide_graph_div_callback(dset):
    def show_graph_div_callback(plots_clicked):
        if dset not in plots_clicked:
            return "display-none"

        plots_clicked = plots_clicked.split(",")  # [:4] max of 4 graph
        len_list = len(plots_clicked)

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
    #print(dsets_data['Dset1'])
    #print(curr_dset.shape)
    

    # Callback for Buy/Sell and Chart Buttons for Left Panel
    app.callback(
        [Output(curr_plot + "contents", "className"), Output(curr_plot + "summary", "className")],
        [Input(curr_plot + "summary", "n_clicks")],
    )(generate_contents_for_left_panel())

    # Callback for className of div for graphs
    app.callback(
        Output(curr_plot + "graph_div", "className"), [Input("plots_clicked", "children")]
    )(generate_show_hide_graph_div_callback(curr_plot))

    # Callback to update the actual graph
    app.callback(
        Output(curr_plot + "chart", "figure"),
        [
            Input("plots_clicked", "children"),
            Input(curr_plot + "chart_type", "value"),
            Input(curr_plot + "plot_layers", "value"),            
            Input(curr_plot + "dropdown_roi", "value"),
        ],
        [
            State('dropdown_files', 'value'),
            State('df_store', 'data'),            
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
    Output("plots_clicked", "children"),
    [Input(dset + "Button_chart", "n_clicks") for dset in plot_names],
    [State("plots_clicked", "children")],
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
    Output("df_store", "data"),
    #Output("output-data-upload", "children"),
    [
        Input("upload-data", "filename"),
        Input("upload-data", "contents"),
    ],
    [
        State("df_store", "data"),
    ],
    #[State('upload-data', 'filename')],
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
        Input("df_store", "data"),
    ],
    #[
        #State("uploaded_dfs", "children"),
    #],
)(generate_uploaded_dfs_callback())


if __name__ == "__main__":
    app.run_server(debug=True)
