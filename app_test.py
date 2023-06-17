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
from sklearn.linear_model import LinearRegression


from dash.dependencies import Input, Output, State
from plotly import tools

from utils_trace import *
#import utils_trace as uuu


app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],
)

app.title = "NiChart"

server = app.server

PATH = pathlib.Path(__file__).parent

e_moving_average_trace()




if __name__ == "__main__":
    app.run_server(debug=True)
