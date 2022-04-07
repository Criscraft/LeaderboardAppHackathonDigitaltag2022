"""
https://towardsdatascience.com/deploying-your-dash-app-to-heroku-the-magical-guide-39bd6a0c586c
"""
import base64
import io
import re
from os import environ
from os.path import isfile

import dropbox
import numpy as np
import pandas as pd
from dash import Dash, Input, Output, dcc, html
from dash.dependencies import Input, Output, State

RGX = r'(.*)_submission.csv'
DATA_PATH = 'static/data.csv'
EPS = 1e-6
COLS = ['team_name', 'accuracy']

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(
    __name__, external_stylesheets=external_stylesheets
)
server = app.server

app.layout = html.Div([
    dcc.Markdown(f'''
    # Hackathon 2022 Leaderboard

    Upload your submission csv file, and see your temporary score.
    
    Only csv files of the form *"your team name"*_submission.csv are processed.

    '''),
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
        # only one file is processed at a time
        multiple=False
    ),
    html.Div(id='output-data-upload'),
    html.Div(
        [html.Button("Download Leaderboard", id="btn-download"),
         dcc.Download(id="download-text")],
        style={'display': 'none'},
        id='hidden-button'
    )
])


@app.callback(
    Output("download-text", "data"),
    Input("btn-download", "n_clicks"),
    prevent_initial_call=True,
)
def download_leaderboard_file(n_clicks):
    """Download the leaderboard dataframe as a csv file.
    """
    if isfile(DATA_PATH):
        df = pd.read_csv(DATA_PATH)[COLS]
        return dcc.send_data_frame(df.to_csv, "leaderboard.csv")


@app.callback(Output('output-data-upload', 'children'),
              Output('hidden-button', 'style'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'),
              prevent_initial_call=True,
)
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        table_div, button_style = parse_contents(
            list_of_contents,
            list_of_names,
            list_of_dates,
        )
        return table_div, button_style


def parse_contents(contents, filename, date):
    """Read the uploaded file, extract the accuracy and log-loss, add it to
    the leaderboard and display the leaderboard

    Parameters
    ----------
    contents : 
        the uploaded csv file
    filename : string
    date : str

    Returns
    -------
    html.Div object
        The leaderboard – or an error message.
    """
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    show_wo_submission = False
    team_name = 'none'

    load_from_dropbox()

    if filename == 'show_me_the_leaderboard.csv':
        # special case for debugging
        show_wo_submission = True

    elif not re.fullmatch(RGX, filename):
        # user did not upload a correct submission csv file!
        return html.Div([
            dcc.Markdown(
                '**Wrong filename! It should look like this: [some_name]_submission.csv**')
        ]), {'display': 'none'}

    else:
        # the actual upload case
        team_name = re.match(RGX, filename).group(1)

    if not show_wo_submission:
        logits = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        logits = logits.to_numpy()[:,1:]
        try:
            acc = compute_score(logits)
        except:
            return html.Div([
                dcc.Markdown('**Undefined error**')
            ]), {'display': 'none'}

        if acc is None:
            return html.Div([
                dcc.Markdown(
                    '**The number of predictions does not match the number of test samples.**')
            ]), {'display': 'none'}

        loaded_data = pd.read_csv(DATA_PATH)[COLS]

        new_data = pd.DataFrame({
            'team_name': [team_name], 'accuracy': [acc]
        }, index=[0])[COLS]
        loaded_data = pd.concat([loaded_data, new_data]).reset_index(drop=True)
        loaded_data.to_csv(DATA_PATH)
        # update the data.csv in the repository
        write_to_dropbox()
    else:
        acc = -1.

        loaded_data = pd.read_csv(DATA_PATH)[COLS]

    loaded_data = loaded_data.sort_values(COLS[1], ascending=False).reset_index(drop=True)

    return html.Div([dcc.Markdown(f'''

    ### Your accuracy: {acc}
    '''), dcc.Markdown(
        loaded_data.to_markdown()
    )]), {'display': 'block'}


def compute_score(logits):
    pred = logits.argmax(1)
    y = np.load('test_labels.npy')

    if pred.shape[0] != y.shape[0]:
        return None

    accuracy = (y == pred).mean()

    return accuracy


def write_to_dropbox():
    dbx = dropbox.Dropbox(environ['ACC_TOKEN'])
    with open(DATA_PATH, 'rb') as f:
        #dbx.files_upload(f.read(), '/Apps/ml_dl_challenge/data.csv')
        dbx.files_upload(
            f.read(), '/data.csv',
            mode=dropbox.files.WriteMode.overwrite
        )


def load_from_dropbox():
    dbx = dropbox.Dropbox(environ['ACC_TOKEN'])
    dbx.files_download_to_file(DATA_PATH, '/data.csv')


if __name__ == '__main__':
    app.run_server(debug=False)
