import pandas as pd
import numpy as np
import scipy.spatial.distance as spatial_distance
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import dash_core_components as dcc
import dash_html_components as html
from PIL import Image
from io import BytesIO
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objs as go
import scipy.spatial.distance as spatial_distance

main_df = pd.read_csv("tsne-videos-apr-18.csv", encoding="utf-8")
categories = ["type", "ratings", "pop_genre", "least_pop_genre"]

category = "type"
df = main_df

def getNeighbours(select_vid, n=9, m=1):
    vector = main_df[["title", "x", "y", "z"]].set_index('title')
    selected_vec = vector.loc[select_vid]

    def compare_pd(vector):
        return spatial_distance.euclidean(vector, selected_vec)

    distance_map = vector.apply(compare_pd, axis=1)
    nearest_neighbors = distance_map.sort_values()[m:n+1]
    selectedVid = main_df[main_df.title == select_vid]
    neigbours = pd.merge(main_df, pd.DataFrame(nearest_neighbors, columns=["score"]).reset_index(), on="title")
    neigbours = neigbours.sort_values(by="score")
    return selectedVid, neigbours

def getPlots(category, df):
    plots = []
    if not category:
        return [go.Scatter3d(
            x=df['x'],
            y=df['y'],
            z=df['z'],
            text=df["title"],
            textposition='middle-center',
            mode='markers',
            marker=dict(
                size=6,
                symbol='circle'
            )
        )]
    uniqs = df[category].unique()


    for un in uniqs:
        tmp = df[df[category] == un]
        trace1 = go.Scatter3d(
            name=un,
            x=tmp['x'],
            y=tmp['y'],
            z=tmp['z'],
            text=tmp["title"],
            textposition='middle-center',
            mode='markers',
            marker=dict(
                size=6,
                symbol='circle'
            )
        )
        plots.append(trace1)
    return plots

def merge(a, b):
    return dict(a, **b)

def omit(omitted_keys, d):
    return {k: v for k, v in d.items() if k not in omitted_keys}

def Card(children, **kwargs):
    return html.Section(
        children,
        style=merge({
            'padding': 20,
            'margin': 5,
            'borderRadius': 5,
            'border': 'thin lightgrey solid',

            # Remove possibility to select the text for better UX
            'user-select': 'none',
            '-moz-user-select': 'none',
            '-webkit-user-select': 'none',
            '-ms-user-select': 'none'
        }, kwargs.get('style', {})),
        **omit(['style'], kwargs)
    )

# embedsLayout = html.Div([
#     getGraph(category)
# ])


embedsLayout = html.Div(
    className="container",
    style={
        'width': '90%',
        'max-width': 'none',
        'font-size': '1.5rem',
        'padding': '10px 30px'
    },
    children=[
        # Header
        html.Div(className="row", children=[
            html.H2(
                'Video Embeddings Explorer',
                id='title',
                style={
                    'float': 'left',
                    'margin-top': '20px',
                    'margin-bottom': '0',
                    'margin-left': '7px'
                }
            ),

            html.Img(
                src="https://s3-us-west-1.amazonaws.com/plotly-tutorials/logo/new-branding/dash-logo-by-plotly-stripe.png",
                style={
                    'height': '100px',
                    'float': 'right'
                }
            )
        ]),

        # Body
        html.Div(className="row", children=[
            html.Div(className="eight columns", children=[
                dcc.Graph(
                    id='graph-3d-plot-tsne',
                    style={'height': '98vh'}
                )
            ]),

            html.Div(className="four columns", children=[
                Card([
                         dcc.Dropdown(
                            id='dropdown-title',
                            searchable=True,
                            options=[{'label': t, 'value': t} for t in main_df["title"]],
                            placeholder="Select video title to explore neighbours"
                        ),
                    dcc.Dropdown(
                        id='dropdown-category',
                        searchable=False,

                        options=[
                            {'label': 'Video Type', 'value': 'type'},
                            {'label': 'TVPG/MPAA Ratings', 'value': 'ratings'},
                            {'label': 'Major Genre', 'value': 'pop_genre'},
                            {'label': 'Minor Genre', 'value': 'least_pop_genre'}
                        ],
                        placeholder="Select video label categories"
                    ),
                    dcc.Dropdown(
                        id='dropdown-catvalue',
                        searchable=False,
                        options=[],
                        placeholder="Select specific category"
                    ),
                ]),

                Card(style={'padding': '5px'}, children=[
                    html.Div(id='div-plot-click-message',
                             style={'text-align': 'center',
                                    'margin-bottom': '7px',
                                    'font-weight': 'bold'}
                             ),

                    html.Div(id='div-plot-click-image', className="div-plot-click-image-cls", style={}),

                    html.Div(id='div-plot-click-wordemb')
                ])
            ])
        ]),


    ]
)

def shorten_title(title):
    return title[:20] + (".." if len(title) >= 20 else "")

def embeds_callbacks(app):

    @app.callback(Output('graph-3d-plot-tsne', 'figure'),
                  [Input('dropdown-category', 'value'),
                   Input('dropdown-title', 'value'),
                   Input('dropdown-catvalue', 'value')])
    def display_3d_scatter_plot(category, title, catvalue):
        df = None

        if title:
            _, df = getNeighbours(title, n=100, m=0)
        elif category:
            df = main_df
            if catvalue:
                df = df[df[category]==catvalue]
        else:
            df = main_df

        axes = dict(
            title='',
            showgrid=True,
            zeroline=False,
            showticklabels=False
        )

        layout = go.Layout(
            margin=dict(l=0, r=0, b=0, t=0),
            scene=dict(
                xaxis=axes,
                yaxis=axes,
                zaxis=axes
            ),
            legend=dict(x=0, y=1.0, font=dict(
                family='sans-serif',
                size=16,
                color='#000'
            ))
        )

        if category and not catvalue:
            figure = go.Figure(
                data=getPlots(category, df),
                layout=layout
            )
        elif title:
            print("Over here")
            df["new"] = [df["title"][0]] + ["Neighbours" for x in range(len(df)-1)]
            figure = go.Figure(
                data=getPlots("new", df),
                layout=layout
            )
        else:
            figure = go.Figure(
                data=getPlots(None, df),
                layout=layout
            )

        return figure

    @app.callback(Output('dropdown-catvalue', 'options'),
                  [Input('dropdown-category', 'value')])
    def display_category_options(category):
        uniqs = df[category].unique()
        return [{'label':k, 'value':k} for k in uniqs]

    @app.callback(Output('div-plot-click-image', 'children'),
                  [Input('graph-3d-plot-tsne', 'clickData'),
                   Input('dropdown-title', 'value')])
    def display_click_image(clickData, title):
        if clickData:
            selectedVideo = clickData['points'][0]['text']
        else:
            selectedVideo= title
        selectedVid, neigbours = getNeighbours(selectedVideo)

        # print(selectedVid)
        imgs = [html.Div(style={'display': 'flex', 'flex-direction': 'column', 'padding': '10px'}, children=[
            html.Label(shorten_title(v["title"]) + "("  + str(round(v["score"], 2)) + ")", style={
            'text-align': 'center',
            'width': '90px',
            'height': '80px',
            'align-self': 'center'
        }),
                            html.Img(src=v["pic"].replace("[", "").replace("]", ""), style={
                        'width': '120',
                        'align-self': 'center',
                    })]) for i, v in neigbours.iterrows()]
        # print(neigbours)
        imgs2 = [html.Div(style={'display': 'flex', 'flex-direction': 'column', 'width': '100%'}, children=[html.Label("Similar To:" + shorten_title(v["title"]),
                                                      style={
                                                          "text-align": "center",
                                                          "font-weight": "bold",
                                                          "font-size": "20px",
                                                          'width': '80px',
                                                          'height': '90px',
                                                          'align-self': 'center'
                                                      }),
                            html.Img(src=v["pic"].replace("[", "").replace("]", ""), style={
                        'width': '120',
                        'align-self': 'center',
                    })]) for i, v in selectedVid.iterrows()]
        return  html.Div(children=  imgs2 + imgs, style={
            "display": "flex",
            "flex-direction": "row",
            "flex-wrap": "wrap",
        })

 # + [html.Table(
 #
 #            [html.Tr([html.Td(v["title"]),
 #                      html.Td(v["score"])],
 #                     html.Td(children=[html.Img(src=v["pic"].replace("[", "").replace("]", ""), style={
 #                    'height': '100px',
 #                    'float': 'right'
 #                })])) for i, v in neigbours.iterrows()]
 #        )]