import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
import pandas as pd


class Graph:
    def __init__(self):
        self.graph_types = {"Important Terms": [], "Responses by Country": [], "Ranked Category Descriptions": [],
                            "Sentiment": [], "Triads": [], "Diads": [], "Heatmap": []}

        self.rows = self.get_rows([])

    def text_graph(self, col, df):
        col.dataframe(df, height=450, width=300)
        return df

    def bar_graph(self, col, x, y, o, s):
        # x, y, orientation, multi_select title
        fig = go.Figure(go.Bar(
            x=x,
            y=y,
            orientation=o,
        ), )

        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
        )

        col.plotly_chart(fig, use_container_width=True)
        return fig

    def pie_chart(self, col, x, y):
        fig = go.Figure(data=[go.Pie(values=x, labels=y)])
        col.plotly_chart(fig, use_container_width=True)
        return fig

    def triad_chart(self, col, df, a, b, c, idxs):
        fig = go.FigureWidget(px.scatter_ternary(df, a=a, b=b, c=c, hover_name=idxs))
        fig.update_layout(
            font=dict(size=8),
            margin=dict(l=25, r=25, t=20, b=20),
            dragmode='lasso',
        )
        col.plotly_chart(fig, use_container_width=True)
        return fig

    def dist_plot(self, col, df):
        group_labels = [df.columns[0], df.columns[1]]  # for legend
        x1, x2 = df.iloc[:, 0], df.iloc[:, 1]
        colors = ['#835AF1', '#7FA6EE', '#B8F7D4']

        fig = ff.create_distplot([x1, x2], group_labels, bin_size=.1,
                                 colors=colors)
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(
                x=0,
                y=.3,
                traceorder='normal',
                font=dict(
                    size=12, ))
        )
        col.plotly_chart(fig, use_container_width=True)
        return fig

    def heatmap(self, col, x, y):
        data = pd.crosstab(x, y)
        fig = ff.create_annotated_heatmap(data.values, x=list(data.columns.values), y=list(data.index.values),
                                        colorscale="OrRd")
        fig.update_xaxes(side="bottom")
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
        )
        col.write(f"{x.name} v. {y.name}")
        col.plotly_chart(fig, use_container_width=True)
        return fig

    # Get number of rows to accommodate graphs
    def get_rows(self, graph_selections):
        num_graphs = len(graph_selections)
        rows = []
        # 3 graphs per row
        if num_graphs > 3:
            num_graphs %= 3
        else:
            num_graphs = 1

        for i in range(num_graphs % 3):
            rows.append(st.beta_columns([1, 1, 1]))  # append columns to row
        return rows

    # increment next graph's position
    def increment_position(self, row, col):
        if col == 0 and row != 0:
            row += 1
        col = (col + 1) % 3
        return row, col

    # display graphs
    def display(self, selections, table):
        if selections is not []:
            pos = self.get_rows(selections)
            row, col = 0, 0

            for s in selections:

                if s == "Important Terms":
                    fig = self.text_graph(pos[row][col], table.tfidf)
                    self.graph_types[s] = fig
                    row, col = self.increment_position(row, col)
                if s == "Responses by Country":
                    stats = table.df.Country.iloc[
                        table.mask].value_counts()  # count number of times each country appears
                    fig = self.bar_graph(pos[row][col], x=stats.values, y=stats.index, o="h", s=s)
                    self.graph_types[s] = fig
                    row, col = self.increment_position(row, col)
                if s == "Ranked Category Descriptions":
                    # create formatting function for legibility
                    def format_ranked_category(table):
                        cats = table.df.columns[7:-len(table.algo_types)]  # algo scores are appended to end of table,
                        # remove from consideration
                        cats = [x for x in cats if not x.startswith("Other")]  # remove "other" columns
                        fixed_df = table.df[cats].iloc[table.mask].groupby(level=0,
                                                                           axis=1).sum()  # sum together columns with same name and filter
                        # create and sort categories by value
                        cats_dict = dict((key, fixed_df[key].sum()) for key in cats)
                        cats_dict = dict(sorted(cats_dict.items(), key=lambda item: item[1], reverse=True))
                        x, y = list(cats_dict.values())[:15], list(cats_dict.keys())[:15]
                        return x, y

                    x, y = format_ranked_category(table)
                    fig = self.bar_graph(pos[row][col], x=x, y=y, o="h", s=s)
                    self.graph_types[s] = fig
                    row, col = self.increment_position(row, col)
                if s == "Sentiment":
                    sent = table.df.Sentiment.iloc[table.mask].value_counts()
                    fig = self.pie_chart(pos[row][col], x=sent.values, y=sent.index)
                    self.graph_types[s] = fig
                    row, col = self.increment_position(row, col)
                if s == "Triads":
                    for triads in table.triads:
                        triad, idxs = triads[0], triads[1]
                        corners = triad.columns
                        fig = self.triad_chart(pos[row][col], triad, corners[0], corners[1], corners[2], idxs)
                        self.graph_types[s].append([fig, pos[row][col]])  #  save figure and place on page to update later
                        row, col = self.increment_position(row, col)
                if s == "Diads":
                    for diads in table.diads:
                        diad, idxs = diads[0], diads[1]
                        fig = self.dist_plot(pos[row][col], diad)
                        self.graph_types[s].append(fig)
                        row, col = self.increment_position(row, col)
                if s == "Heatmap":
                    signifiers = table.df.iloc[:, 2:7]
                    for i in range(signifiers.shape[1]):
                        for j in range(i+1, signifiers.shape[1]):  # stop duplicates
                            x, y = signifiers[signifiers.columns[i]],  signifiers[signifiers.columns[j]]
                            fig = self.heatmap(pos[row][col], x, y)
                            self.graph_types[s].append(fig)
                            row, col = self.increment_position(row, col)