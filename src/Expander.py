import streamlit as st
import pandas as pd
from spellchecker import SpellChecker


class Expander:
    def __init__(self, table):
        self.expander = st.beta_expander("Search and Filter")
        self.df = table.df
        self.row1 = self.expander.beta_columns([1, 2])
        self.row2 = self.expander.beta_columns([1, 1, 1, 1])
        self.row3 = self.expander.beta_columns([1, 1, 1, 1, 1])
        self.row4 = self.expander.beta_columns([1])

        # ROW 1
        self.height = self.df_height(self.row1[0], table)  # num rows input
        self.terms = self.word_search(self.row1[1])  # search

        # ROW 2
        self.leadership = self.multiselect(self.row2[0], "Leaderhsip focused on...",
                                           table.df.columns[7:17])
        self.office = self.multiselect(self.row2[1], "Office could benefit from...",
                                       table.df.columns[20:29])
        self.people = self.multiselect(self.row2[2], "People were...",
                                       table.df.columns[32:42])
        self.relationships = self.multiselect(self.row2[3], "Relationships were based on...",
                                              table.df.columns[45:55])
        # ROW 3
        self.common = self.multiselect(self.row3[0], "Common",
                                       table.df.Common.unique())
        self.function = self.multiselect(self.row3[1], "Function",
                                         table.df.Function.unique())
        self.role = self.multiselect(self.row3[2], "Role",
                                     table.df.Role.unique())
        self.experience = self.multiselect(self.row3[3], "Experience",
                                           table.df.Experience.unique())
        self.country = self.multiselect(self.row3[4], "Country",
                                        table.df.Country.unique())

        # ROW 4
        self.sentiment = self.multiselect(self.row4[0], "Sentiment",
                                          table.df.Sentiment.unique())

    def df_height(self, col, table):
        # number input for displaying rows
        return col.number_input("Rows Displayed", max_value=table.df.shape[0], value=5)

    def multiselect(self, col, label, options):
        return col.multiselect(label=label, options=options, key="label")

    def word_search(self, col):
        # word searcher
        terms = col.text_input("Search Stories").lower()
        return terms.split(" ")