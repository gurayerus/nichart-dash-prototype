# -*- coding: utf-8 -*-
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

from dash.dependencies import Input, Output, State
from plotly import tools


app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],
)

app.title = "NiChart"

server = app.server

PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()


# Loading roi data
dsets_data = {
    #"Dset1": pd.read_csv(DATA_PATH.joinpath("Dset1.csv"), index_col=1),
    #"Dset2": pd.read_csv(DATA_PATH.joinpath("Dset2.csv"), index_col=1),
    "Dset1": pd.read_csv(DATA_PATH.joinpath("Dset1_n100.csv"), index_col=1),
    "Dset2": pd.read_csv(DATA_PATH.joinpath("Dset2_n100.csv"), index_col=1),
}

# Currency dsets
dsets = ["Dset1", "Dset2"]

# Display big numbers in readable format
def human_format(num):
    try:
        num = float(num)
        # If value is 0
        if num == 0:
            return 0
        # Else value is a number
        if num < 1000000:
            return num
        magnitude = int(math.log(num, 1000))
        mantissa = str(int(num / (1000 ** magnitude)))
        return mantissa + ["", "K", "M", "G", "T", "P"][magnitude]
    except:
        return num


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

####### STUDIES TRACES ######

# Moving average
def moving_average_trace(df, fig):
    df2 = df.rolling(window=5).mean()
    trace = go.Scatter(
        x=df2.index, y=df2["close"], mode="lines", showlegend=False, name="MA"
    )
    fig.append_trace(trace, 1, 1)  # plot in first row
    return fig


# Exponential moving average
def e_moving_average_trace(df, fig):
    df2 = df.rolling(window=20).mean()
    trace = go.Scatter(
        x=df2.index, y=df2["close"], mode="lines", showlegend=False, name="EMA"
    )
    fig.append_trace(trace, 1, 1)  # plot in first row
    return fig


# Bollinger Bands
def bollinger_trace(df, fig, window_size=10, num_of_std=5):
    price = df["close"]
    rolling_mean = price.rolling(window=window_size).mean()
    rolling_std = price.rolling(window=window_size).std()
    upper_band = rolling_mean + (rolling_std * num_of_std)
    lower_band = rolling_mean - (rolling_std * num_of_std)

    trace = go.Scatter(
        x=df.index, y=upper_band, mode="lines", showlegend=False, name="BB_upper"
    )

    trace2 = go.Scatter(
        x=df.index, y=rolling_mean, mode="lines", showlegend=False, name="BB_mean"
    )

    trace3 = go.Scatter(
        x=df.index, y=lower_band, mode="lines", showlegend=False, name="BB_lower"
    )

    fig.append_trace(trace, 1, 1)  # plot in first row
    fig.append_trace(trace2, 1, 1)  # plot in first row
    fig.append_trace(trace3, 1, 1)  # plot in first row
    return fig


# Accumulation Distribution
def accumulation_trace(df):
    df["volume"] = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / (
        df["high"] - df["low"]
    )
    trace = go.Scatter(
        x=df.index, y=df["volume"], mode="lines", showlegend=False, name="Accumulation"
    )
    return trace


# Commodity Channel Index
def cci_trace(df, ndays=5):
    TP = (df["high"] + df["low"] + df["close"]) / 3
    CCI = pd.Series(
        (TP - TP.rolling(window=10, center=False).mean())
        / (0.015 * TP.rolling(window=10, center=False).std()),
        name="cci",
    )
    trace = go.Scatter(x=df.index, y=CCI, mode="lines", showlegend=False, name="CCI")
    return trace


# Price Rate of Change
def roc_trace(df, ndays=5):
    N = df["close"].diff(ndays)
    D = df["close"].shift(ndays)
    ROC = pd.Series(N / D, name="roc")
    trace = go.Scatter(x=df.index, y=ROC, mode="lines", showlegend=False, name="ROC")
    return trace


# Stochastic oscillator %K
def stoc_trace(df):
    SOk = pd.Series((df["close"] - df["low"]) / (df["high"] - df["low"]), name="SO%k")
    trace = go.Scatter(x=df.index, y=SOk, mode="lines", showlegend=False, name="SO%k")
    return trace


# Momentum
def mom_trace(df, n=5):
    M = pd.Series(df["close"].diff(n), name="Momentum_" + str(n))
    trace = go.Scatter(x=df.index, y=M, mode="lines", showlegend=False, name="MOM")
    return trace


# Pivot points
def pp_trace(df, fig):
    PP = pd.Series((df["high"] + df["low"] + df["close"]) / 3)
    R1 = pd.Series(2 * PP - df["low"])
    S1 = pd.Series(2 * PP - df["high"])
    R2 = pd.Series(PP + df["high"] - df["low"])
    S2 = pd.Series(PP - df["high"] + df["low"])
    R3 = pd.Series(df["high"] + 2 * (PP - df["low"]))
    S3 = pd.Series(df["low"] - 2 * (df["high"] - PP))
    trace = go.Scatter(x=df.index, y=PP, mode="lines", showlegend=False, name="PP")
    trace1 = go.Scatter(x=df.index, y=R1, mode="lines", showlegend=False, name="R1")
    trace2 = go.Scatter(x=df.index, y=S1, mode="lines", showlegend=False, name="S1")
    trace3 = go.Scatter(x=df.index, y=R2, mode="lines", showlegend=False, name="R2")
    trace4 = go.Scatter(x=df.index, y=S2, mode="lines", showlegend=False, name="S2")
    trace5 = go.Scatter(x=df.index, y=R3, mode="lines", showlegend=False, name="R3")
    trace6 = go.Scatter(x=df.index, y=S3, mode="lines", showlegend=False, name="S3")
    fig.append_trace(trace, 1, 1)
    fig.append_trace(trace1, 1, 1)
    fig.append_trace(trace2, 1, 1)
    fig.append_trace(trace3, 1, 1)
    fig.append_trace(trace4, 1, 1)
    fig.append_trace(trace5, 1, 1)
    fig.append_trace(trace6, 1, 1)
    return fig


# MAIN CHART TRACES (STYLE tab)
def line_trace(df):
    trace = go.Scatter(x = df['Age_At_Visit'], y = df["MUSE_GM"], mode="lines", showlegend=False, name="line")
    return trace

def area_trace(df):
    trace = go.Scatter(
        x=df.index, y=df["close"], showlegend=False, fill="toself", name="area"
    )
    return trace


def bar_trace(df):
    return go.Ohlc(
        x=df.index,
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        increasing=dict(line=dict(color="#888888")),
        decreasing=dict(line=dict(color="#888888")),
        showlegend=False,
        name="bar",
    )


def colored_bar_trace(df):
    return go.Ohlc(
        x=df.index,
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        showlegend=False,
        name="colored bar",
    )


def candlestick_trace(df):
    return go.Candlestick(
        x=df.index,
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        increasing=dict(line=dict(color="#00ff00")),
        decreasing=dict(line=dict(color="white")),
        showlegend=False,
        name="candlestick",
    )


# For buy/sell modal
def ask_modal_trace(curr_dset, index):
    df = roi_data[curr_dset].iloc[index - 10 : index]  # returns ten rows
    return go.Scatter(x=df.index, y=df["Ask"], mode="lines", showlegend=False)


# For buy/sell modal
def bid_modal_trace(curr_dset, index):
    df = roi_data[curr_dset].iloc[index - 10 : index]  # returns ten rows
    return go.Scatter(x=df.index, y=df["Bid"], mode="lines", showlegend=False)


# returns modal figure for a currency dset
def get_modal_fig(curr_dset, index):
    fig = tools.make_subplots(
        rows=2, shared_xaxes=True, shared_yaxes=False, cols=1, print_grid=False
    )

    fig.append_trace(ask_modal_trace(curr_dset, index), 1, 1)
    fig.append_trace(bid_modal_trace(curr_dset, index), 2, 1)

    fig["layout"]["autosize"] = True
    fig["layout"]["height"] = 375
    fig["layout"]["margin"] = {"t": 5, "l": 50, "b": 0, "r": 5}
    fig["layout"]["yaxis"]["showgrid"] = True
    fig["layout"]["yaxis"]["gridcolor"] = "#3E3F40"
    fig["layout"]["yaxis"]["gridwidth"] = 1
    fig["layout"].update(paper_bgcolor="#21252C", plot_bgcolor="#21252C")

    return fig


# Returns graph figure
def get_fig(curr_dset, ask, bid, type_trace, studies, period):
    # Get OHLC data
    data_frame = roi_data[curr_dset]
    t = datetime.datetime.now()
    data = data_frame.loc[
        : t.strftime(
            "2016-01-05 %H:%M:%S"
        )  # all the data from the beginning until current time
    ]
    data_bid = data["Bid"]
    df = data_bid.resample(period).ohlc()

    subplot_traces = [  # first row traces
        "accumulation_trace",
        "cci_trace",
        "roc_trace",
        "stoc_trace",
        "mom_trace",
    ]
    selected_subplots_studies = []
    selected_first_row_studies = []
    row = 1  # number of subplots

    if studies:
        for study in studies:
            if study in subplot_traces:
                row += 1  # increment number of rows only if the study needs a subplot
                selected_subplots_studies.append(study)
            else:
                selected_first_row_studies.append(study)

    fig = tools.make_subplots(
        rows=row,
        shared_xaxes=True,
        shared_yaxes=True,
        cols=1,
        print_grid=False,
        vertical_spacing=0.12,
    )

    # Add main trace (style) to figure
    fig.append_trace(eval(type_trace)(df), 1, 1)

    # Add trace(s) on fig's first row
    for study in selected_first_row_studies:
        fig = eval(study)(df, fig)

    row = 1
    # Plot trace on new row
    for study in selected_subplots_studies:
        row += 1
        fig.append_trace(eval(study)(df), row, 1)

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
def chart_div(dset):
    return html.Div(
        id=dset + "graph_div",
        className="display-none",
        children=[
            # Menu for Currency Graph
            html.Div(
                id=dset + "menu",
                className="not_visible",
                children=[
                    # stores current menu tab
                    html.Div(
                        id=dset + "menu_tab",
                        children=["Studies"],
                        style={"display": "none"},
                    ),
                    html.Span(
                        "Style",
                        id=dset + "style_header",
                        className="span-menu",
                        n_clicks_timestamp=2,
                    ),
                    html.Span(
                        "Studies",
                        id=dset + "studies_header",
                        className="span-menu",
                        n_clicks_timestamp=1,
                    ),
                    # Studies Checklist
                    html.Div(
                        id=dset + "studies_tab",
                        children=[
                            dcc.Checklist(
                                id=dset + "studies",
                                options=[
                                    {
                                        "label": "Accumulation/D",
                                        "value": "accumulation_trace",
                                    },
                                    {
                                        "label": "Bollinger bands",
                                        "value": "bollinger_trace",
                                    },
                                    {"label": "MA", "value": "moving_average_trace"},
                                    {"label": "EMA", "value": "e_moving_average_trace"},
                                    {"label": "CCI", "value": "cci_trace"},
                                    {"label": "ROC", "value": "roc_trace"},
                                    {"label": "Pivot points", "value": "pp_trace"},
                                    {
                                        "label": "Stochastic oscillator",
                                        "value": "stoc_trace",
                                    },
                                    {
                                        "label": "Momentum indicator",
                                        "value": "mom_trace",
                                    },
                                ],
                                value=[],
                            )
                        ],
                        style={"display": "none"},
                    ),
                    # Styles checklist
                    html.Div(
                        id=dset + "style_tab",
                        children=[
                            dcc.RadioItems(
                                id=dset + "chart_type",
                                options=[
                                    {
                                        "label": "candlestick",
                                        "value": "candlestick_trace",
                                    },
                                    {"label": "line", "value": "line_trace"},
                                    {"label": "mountain", "value": "area_trace"},
                                    {"label": "bar", "value": "bar_trace"},
                                    {
                                        "label": "colored bar",
                                        "value": "colored_bar_trace",
                                    },
                                ],
                                value="colored_bar_trace",
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
                        id=dset + "menu_button",
                        className="inline-block chart-title",
                        children=f"{dset} ☰",
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
                                        className="dropdown-period",
                                        id=dset + "dropdown_period",
                                        options=[
                                            {"label": "5 min", "value": "5Min"},
                                            {"label": "15 min", "value": "15Min"},
                                            {"label": "30 min", "value": "30Min"},
                                        ],
                                        value="15Min",
                                        clearable=False,
                                    )
                                ],
                            ),
                            html.Span(
                                id=dset + "close",
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
                    id=dset + "chart",
                    className="chart-graph",
                    config={"displayModeBar": False, "scrollZoom": True},
                )
            ),
        ],
    )


# returns modal Buy/Sell
def modal(dset):
    return html.Div(
        id=dset + "modal",
        className="modal",
        style={"display": "none"},
        children=[
            html.Div(
                className="modal-content",
                children=[
                    html.Span(
                        id=dset + "closeModal", className="modal-close", children="×"
                    ),
                    html.P(id="modal" + dset, children=dset),
                    # row div with two div
                    html.Div(
                        className="row",
                        children=[
                            # graph div
                            html.Div(
                                className="six columns",
                                children=[
                                    dcc.Graph(
                                        id=dset + "modal_graph",
                                        config={"displayModeBar": False},
                                    )
                                ],
                            ),
                            # order values div
                            html.Div(
                                className="six columns modal-user-control",
                                children=[
                                    html.Div(
                                        children=[
                                            html.P("Volume"),
                                            dcc.Input(
                                                id=dset + "volume",
                                                className="modal-input",
                                                type="number",
                                                value=0.1,
                                                min=0,
                                                step=0.1,
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        children=[
                                            html.P("Type"),
                                            dcc.RadioItems(
                                                id=dset + "trade_type",
                                                options=[
                                                    {"label": "Buy", "value": "buy"},
                                                    {"label": "Sell", "value": "sell"},
                                                ],
                                                value="buy",
                                                labelStyle={"display": "inline-block"},
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        children=[
                                            html.P("SL TPS"),
                                            dcc.Input(
                                                id=dset + "SL",
                                                type="number",
                                                min=0,
                                                step=1,
                                            ),
                                        ]
                                    ),
                                    html.Div(
                                        children=[
                                            html.P("TP TPS"),
                                            dcc.Input(
                                                id=dset + "TP",
                                                type="number",
                                                min=0,
                                                step=1,
                                            ),
                                        ]
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="modal-order-btn",
                        children=html.Button(
                            "Order", id=dset + "button_order", n_clicks=0
                        ),
                    ),
                ],
            )
        ],
    )


# Dash App Layout
app.layout = html.Div(
    className="row",
    children=[
        # Interval component for live clock
        dcc.Interval(id="interval", interval=1 * 1000, n_intervals=0),
        # Interval component for ask bid updates
        dcc.Interval(id="i_bis", interval=1 * 2000, n_intervals=0),
        # Interval component for graph updates
        dcc.Interval(id="i_tris", interval=1 * 5000, n_intervals=0),
        # Interval component for graph updates
        dcc.Interval(id="i_news", interval=1 * 60000, n_intervals=0),
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
                # Ask Bid Currency Div
                html.Div(
                    className="div-currency-toggles",
                    children=[
                        html.P(
                            id="live_clock",
                            className="three-col",
                            children=datetime.datetime.now().strftime("%H:%M:%S"),
                        ),
                        html.P(className="three-col", children="GMPlot"),
                        html.P(className="three-col", children="WMPlot"),
                        html.Div(
                            id="dsets",
                            className="div-bid-ask",
                            children=[
                                get_row(first_ask_bid(dset, datetime.datetime.now()))
                                for dset in dsets
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
                # Top Bar Div - Displays Balance, Equity, ... , Open P/L
                html.Div(
                    id="top_bar", className="row div-top-bar", children=get_top_bar()
                ),
                # Charts Div
                html.Div(
                    id="charts",
                    className="row",
                    children=[chart_div(dset) for dset in dsets],
                ),
                # Panel for orders
                html.Div(
                    id="bottom_panel",
                    className="row div-bottom-panel",
                    children=[
                        html.Div(
                            className="display-inlineblock",
                            children=[
                                dcc.Dropdown(
                                    id="dropdown_positions",
                                    className="bottom-dropdown",
                                    options=[
                                        {"label": "Open Positions", "value": "open"},
                                        {
                                            "label": "Closed Positions",
                                            "value": "closed",
                                        },
                                    ],
                                    value="open",
                                    clearable=False,
                                    style={"border": "0px solid black"},
                                )
                            ],
                        ),
                        html.Div(
                            className="display-inlineblock float-right",
                            children=[
                                dcc.Dropdown(
                                    id="closable_orders",
                                    className="bottom-dropdown",
                                    placeholder="Close order",
                                )
                            ],
                        ),
                        html.Div(id="orders_table", className="row table-orders"),
                    ],
                ),
            ],
        ),
        # Hidden div that stores all clicked charts (EURUSD, USDCHF, etc.)
        html.Div(id="charts_clicked", style={"display": "none"}),
        # Hidden div for each dset that stores orders
        html.Div(
            children=[
                html.Div(id=dset + "orders", style={"display": "none"})
                for dset in dsets
            ]
        ),
        html.Div([modal(dset) for dset in dsets]),
        # Hidden Div that stores all orders
        html.Div(id="orders", style={"display": "none"}),
    ],
)

# Dynamic Callbacks

# returns string containing clicked charts
def generate_chart_button_callback():
    def chart_button_callback(*args):
        dsets = ""
        for i in range(len(currencies)):
            if args[i] > 0:
                dset = currencies[i]
                if dsets:
                    dsets = dsets + "," + dset
                else:
                    dsets = dset
        return dsets

    return chart_button_callback

# Function to update Graph Figure
def generate_figure_callback(dset):
    def chart_fig_callback(n_i, p, t, s, dsets, a, b, old_fig):

        if dsets is None:
            return {"layout": {}, "data": {}}

        dsets = dsets.split(",")
        if dset not in dsets:
            return {"layout": {}, "data": []}

        if old_fig is None or old_fig == {"layout": {}, "data": {}}:
            return get_fig(dset, a, b, t, s, p)

        fig = get_fig(dset, a, b, t, s, p)
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
# Also updates style and studies menu headers
def generate_active_menu_tab_callback():
    def update_current_tab_name(n_style, n_studies):
        if n_style >= n_studies:
            return "Style", "span-menu selected", "span-menu"
        return "Studies", "span-menu", "span-menu selected"

    return update_current_tab_name

# Function show or hide studies menu for chart
def generate_studies_content_tab_callback():
    def studies_tab(current_tab):
        if current_tab == "Studies":
            return {"display": "block", "textAlign": "left", "marginTop": "30"}
        return {"display": "none"}

    return studies_tab


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
            current_bid = current_bids[currencies.index(order["symbol"])]
            current_ask = current_asks[currencies.index(order["symbol"])]

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
    def show_graph_div_callback(charts_clicked):
        if dset not in charts_clicked:
            return "display-none"

        charts_clicked = charts_clicked.split(",")  # [:4] max of 4 graph
        len_list = len(charts_clicked)

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


# Loop through all currencies
for dset in dsets:

    # Callback to update the actual graph
    app.callback(
        Output(dset + "chart", "figure"),
        [
            Input("i_tris", "n_intervals"),
            Input(dset + "dropdown_period", "value"),
            Input(dset + "chart_type", "value"),
            Input(dset + "studies", "value"),
            Input("charts_clicked", "children"),
        ],
        [
            State(dset + "ask", "children"),
            State(dset + "bid", "children"),
            State(dset + "chart", "figure"),
        ],
    )(generate_figure_callback(dset))

    # updates the ask and bid prices
    app.callback(
        Output(dset + "row", "children"),
        [Input("i_bis", "n_intervals")],
        [
            State(dset + "index", "children"),
            State(dset + "bid", "children"),
            State(dset + "ask", "children"),
        ],
    )(generate_ask_bid_row_callback(dset))

    # close graph by setting to 0 n_clicks property
    app.callback(
        Output(dset + "Button_chart", "n_clicks"),
        [Input(dset + "close", "n_clicks")],
        [State(dset + "Button_chart", "n_clicks")],
    )(generate_close_graph_callback())

    # show or hide graph menu
    app.callback(
        Output(dset + "menu", "className"),
        [Input(dset + "menu_button", "n_clicks")],
        [State(dset + "menu", "className")],
    )(generate_open_close_menu_callback())

    # stores in hidden div name of clicked tab name
    app.callback(
        [
            Output(dset + "menu_tab", "children"),
            Output(dset + "style_header", "className"),
            Output(dset + "studies_header", "className"),
        ],
        [
            Input(dset + "style_header", "n_clicks_timestamp"),
            Input(dset + "studies_header", "n_clicks_timestamp"),
        ],
    )(generate_active_menu_tab_callback())

    # hide/show STYLE tab content if clicked or not
    app.callback(
        Output(dset + "style_tab", "style"), [Input(dset + "menu_tab", "children")]
    )(generate_style_content_tab_callback())

    # hide/show MENU tab content if clicked or not
    app.callback(
        Output(dset + "studies_tab", "style"), [Input(dset + "menu_tab", "children")]
    )(generate_studies_content_tab_callback())

    # show modal
    app.callback(Output(dset + "modal", "style"), [Input(dset + "Buy", "n_clicks")])(
        generate_modal_open_callback()
    )

    # set modal value SL to O
    app.callback(Output(dset + "SL", "value"), [Input(dset + "Buy", "n_clicks")])(
        generate_clean_sl_callback()
    )

    # set modal value TP to O
    app.callback(Output(dset + "TP", "value"), [Input(dset + "Buy", "n_clicks")])(
        generate_clean_tp_callback()
    )

    # hide modal
    app.callback(
        Output(dset + "Buy", "n_clicks"),
        [
            Input(dset + "closeModal", "n_clicks"),
            Input(dset + "button_order", "n_clicks"),
        ],
    )(generate_modal_close_callback())

    # updates modal figure
    app.callback(
        Output(dset + "modal_graph", "figure"),
        [Input(dset + "index", "children"), Input(dset + "Buy", "n_clicks")],
        [State(dset + "modal_graph", "figure")],
    )(generate_modal_figure_callback(dset))

    # each dset saves its orders in hidden div
    app.callback(
        Output(dset + "orders", "children"),
        [Input(dset + "button_order", "n_clicks")],
        [
            State(dset + "volume", "value"),
            State(dset + "trade_type", "value"),
            State(dset + "SL", "value"),
            State(dset + "TP", "value"),
            State(dset + "orders", "children"),
            State(dset + "ask", "children"),
            State(dset + "bid", "children"),
        ],
    )(generate_order_button_callback(dset))

# Callback to update live clock
@app.callback(Output("live_clock", "children"), [Input("interval", "n_intervals")])
def update_time(n):
    return datetime.datetime.now().strftime("%H:%M:%S")


if __name__ == "__main__":
    app.run_server(debug=True)