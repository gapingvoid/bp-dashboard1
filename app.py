from src.Expander import Expander
from src.Table import Table
from src.Graph import Graph
from src.helpers import percent_data, get_table_download_link
import streamlit as st

st.set_page_config(layout="wide")

# Title
st.markdown("<h1 style='text-align: center;'>Gapingvoid x BearingPoint</h1>", unsafe_allow_html=True)

# make table and expander
table = Table()

# display graphs
st.sidebar.subheader("Graphs")
graph = Graph()
graph_selections = st.sidebar.multiselect("Select graphs to display", list(graph.graph_types.keys()))
display_graphs = False if graph_selections == [] else True
# display graphs
if display_graphs:
    with st.beta_expander("Graphs", True):
        graph.display(graph_selections, table)
        # update triads to allow selecting stories
        if "Triads" in graph_selections:
            graph.update_triads(table)

# display table and expander
st.sidebar.subheader("Data")
show_table = st.sidebar.checkbox("Display Data", value=True)
if show_table:
    expander = Expander(table)
    # filter dataframe
    filtered_df = table.filter_data(expander)
    # create progress bar showing filter as a fraction of total data
    prog_bar, percent, select = st.beta_columns([7, 1, 2])
    # get the category we will use as the denominator
    denominator_q = select.selectbox("Fraction of", options=expander.questions, index=0)
    # if there hasn't been filter selected, just use "All" which refers to the unfiltered df
    if denominator_q == "All" or filtered_df.shape == table.df.shape:
        prog_df = table.df
    else:   #TODO: Hacky af
        try:
            # get selected value from the question we're using as the denominator
            denominator_sel = getattr(expander, denominator_q.lower())[0]
            # get all data that used the selector
            try:
                prog_df = table.df[(table.df[denominator_sel] == 1)]
            except:
                prog_df = table.df[table.df[denominator_q] == denominator_sel]
        except:
            st.warning("If selecting a category, you must also select a question from the category in the expander. "
                       "Otherwise the dashboard will default to all data.")
            prog_df = table.df  # in case someone selects a category but not a subcategory

    # calculate percent and create figure
    prog_bar.plotly_chart(percent_data(filtered_df, prog_df), config=dict(displayModeBar=False), use_container_width=True)
    percent.write(" ")  # whitespace
    percent.write(" ")
    percent.write("{}%".format(round(filtered_df.shape[0] / prog_df.shape[0] * 100)))
    # display table
    table.display(filtered_df, expander)
    # donwnloadable link
    st.sidebar.markdown(get_table_download_link(filtered_df), unsafe_allow_html=True)