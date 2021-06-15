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
        if "Triads" in graph_selections:  # select from stories
            story_selections = st.multiselect(label="Display Stories", options=table.df.index)
            if story_selections:  # display stories as table if not empty
                st.table(table.df.Story.iloc[story_selections])
                for triads in graph.graph_types["Triads"]:  # update points on graph
                    fig, col = triads[0], triads[1]
                    # get actual index of story on graph, unrelated to value because of previously removed NaNs
                    idxs = [i for i, val in enumerate(fig.data[0].hovertext) if val in story_selections]
                    fig.data[0].update(selectedpoints=idxs,
                                       selected=dict(marker=dict(color='red')),  # color of selected points
                                       unselected=dict(marker=dict(color='rgb(200,200, 200)',  # color of unselected pts
                                                                   opacity=0.9)))
                    col.plotly_chart(fig, use_container_width=True)

# display table and expander
st.sidebar.subheader("Data")
show_table = st.sidebar.checkbox("Display Data", value=True)
if show_table:
    expander = Expander(table)
    filtered_df = table.filter_data(expander)
    prog_bar, percent = st.beta_columns([9, 1])
    prog_bar.plotly_chart(percent_data(filtered_df, table), config=dict(displayModeBar=False), use_container_width=True)
    percent.write(" ")  # hack for formatting
    percent.write("{}%".format(round(filtered_df.shape[0] / table.df.shape[0] * 100)))
    table.display(filtered_df, expander)
    st.sidebar.markdown(get_table_download_link(filtered_df), unsafe_allow_html=True)