# -*- coding: utf-8 -*-
import math
import pandas as pd
import plotly.plotly as py
import plotly.graph_objs as go
from sklearn.linear_model import LinearRegression
from plotly import tools
import statsmodels.api as sm
import numpy as np

####### Plot types ######


def percentile_trace(df, xvar, yvar):
    
    #trace = go.Scatter(
        #x=df[xvar], y=df[yvar], showlegend=False, mode = 'markers', name = "datapoint"
    #)
    ##return trace

    yvar1 = 'centile_25'
    yvar2 = 'centile_75'

    # Create line traces
    trace1 = go.Scatter(x=xvar, y=yvar1, mode='lines', name='Line 1')
    trace2 = go.Scatter(x=xvar, y=yvar2, mode='lines', name='Line 2')

    # Create trace for filling between lines
    fill_trace = go.Scatter(x = xvar + xvar[::-1], 
                            y=yvar1 + yvar2[::-1], 
                            fill='tozerox', 
                            fillcolor='rgba(0, 176, 246, 0.2)', 
                            line_color='rgba(255, 255, 255, 0)', 
                            name='Fill')

    return fill_trace


def dots_trace(df, xvar, yvar):
    trace = go.Scatter(
        x=df[xvar], y=df[yvar], showlegend=False, mode = 'markers', name = "datapoint"
    )
    return trace

def linreg_trace(df, xvar, yvar, fig):
    model = LinearRegression().fit(np.array(df[xvar]).reshape(-1,1), 
                                   (np.array(df[yvar])))
    y_hat = model.predict(np.array(df[xvar]).reshape(-1,1))
    trace = go.Scatter(
        x=df[xvar], y=y_hat, showlegend=False, mode = 'lines', name = "linregfit"
    )
    fig.append_trace(trace, 1, 1)  # plot in first row
    return fig

def lowess_trace(df, xvar, yvar, fig):
    lowess = sm.nonparametric.lowess

    #y_hat = lowess(np.array(df[yvar], np.array(df[xvar], frac=1./3)
    y_hat = lowess(df[yvar], df[xvar], frac=1./3)
    trace = go.Scatter(
        x = y_hat[:,0], y=y_hat[:,1], showlegend=False, mode = 'lines', name = "lowessfit"
    )
    fig.append_trace(trace, 1, 1)  # plot in first row
    return fig
