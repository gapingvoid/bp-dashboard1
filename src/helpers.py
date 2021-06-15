from google.cloud import storage
import streamlit as st
import json
import plotly.graph_objects as go
import base64
import pandas as pd
from io import BytesIO



def download_blob(bucket_name, source_blob_name):
    """Downloads a blob from the bucket."""
    # bucket_name = "your-bucket-name"
    # source_blob_name = "storage-object-name"
    # destination_file_name = "local/path/to/file"

    # current_directory = os.path.abspath(os.path.dirname(__file__))
    read_secret()

    # path_to_service_account_json = os.path.join(current_directory, secret)
    storage_client = storage.Client.from_service_account_json("./secret.txt")

    bucket = storage_client.bucket(bucket_name)

    # Construct a client side representation of a blob.
    # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
    # any content from Google Cloud Storage. As we don't need additional data,
    # using `Bucket.blob` is preferred here.
    blob = bucket.get_blob(source_blob_name)
    return blob


def read_secret():
    type_ = st.secrets["type"]
    project_id = st.secrets["project_id"]
    private_key_id = st.secrets["private_key_id"]
    private_key = st.secrets["private_key"]
    client_email = st.secrets["client_email"]
    client_id = st.secrets["client_id"]
    auth_uri = st.secrets["auth_uri"]
    token_uri = st.secrets["token_uri"]
    auth = st.secrets["auth_provider_x509_cert_url"]
    client = st.secrets["client_x509_cert_url"]
    dictionary = {type_[0]: type_[1], project_id[0]: project_id[1], private_key_id[0]: private_key_id[1],
                  private_key[0]: private_key[1], client_email[0]: client_email[1], client_id[0]: client_id[1],
                  auth_uri[0]: auth_uri[1], token_uri[0]: token_uri[1], auth[0]: auth[1], client[0]: client[1]}
    with open('./secret.txt', 'w') as outfile:
        json.dump(dictionary, outfile)


def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    processed_data = output.getvalue()
    return processed_data


def get_table_download_link(df):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    val = to_excel(df)
    b64 = base64.b64encode(val)
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="GVfiltered.xlsx">Download Filtered Data</a>'


def percent_data(filtered_df, table):
    num_filtered = [filtered_df.shape[0]]
    total_data = [table.df.shape[0] - filtered_df.shape[0]]
    fig = go.Figure(data=[
        go.Bar(name="Filtered Stories", x=num_filtered, y=["Stories     "], orientation="h", width=[.1]),
        go.Bar(name="Total Stories", x=total_data, y=["Stories     "], orientation="h", width=[.1])
    ])
    fig.update_layout(
        barmode='stack',
        margin=dict(l=5, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=75,
        showlegend=False
    )
    fig.update_xaxes(
        visible=False
    )
    return fig

