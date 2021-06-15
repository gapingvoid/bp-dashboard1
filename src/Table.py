import pandas as pd
import streamlit as st
import pickle
import numpy as np
from .helpers import download_blob
from sklearn.feature_extraction.text import TfidfVectorizer


class Table:
    def __init__(self):
        # algos
        self.algo_types = ["Sentiment"]
        self.sentiment = self.read_data("bearingpoint_dash", "sentiment.csv").Sentiment
        # df
        self.df, self.og_columns = self.read_assessment("bearingpoint_dash", "BPsurvey.csv")
        self.df = pd.concat([self.df, self.sentiment], axis=1)
        self.height = self.df.shape[0]
        self.tfidf, self.tfidf_story = self.tfidf()
        # read filter data if exists already
        try:
            self.mask = pd.read_csv("filter.csv").iloc[:, 1].values.astype(np.bool_)  # column one is the index for some reason
        except:
            self.mask = np.ones(self.df.shape[0],  dtype=np.bool_)
        # triad / diad
        self.triads, self.diads = self.read_triads("bearingpoint_dash", "triad_data.csv")
        # save
        self.saved_stories = []

    def read_data(self, bucket_name, source_blob_name):
        # read in data from csv to df
        df = pd.read_csv("http://storage.googleapis.com/{}/{}".format(bucket_name, source_blob_name)).fillna(0)
        return df

    @st.cache
    def read_triads(self, bucket_name, source_blob_name):
        df = self.read_data(bucket_name, source_blob_name)
        triad = df.iloc[:, 8:44]
        diad = df.iloc[:, 44:56]
        # get batches (eg. divide by # of elements per graph)
        batch_triad = int(len(triad.columns) / 6)
        batch_diad = int(len(diad.columns) / 4)

        def graph_dfs(df, batch, triad):
            df.columns = [c.split("_")[-1].title() for c in df.columns]
            dfs = []
            for i in range(batch):
                if triad:
                    selection = df.iloc[:, i * 6: (i + 1) * 6 - 1]  # last columns is NA ignore Na columns
                    selection = selection.drop(selection.columns[:2], axis=1)
                else:
                    selection = df.iloc[:, i * 4: (i + 1) * 4 - 1]
                    selection = selection.drop(selection.columns[0], axis=1)
                # remove Nans (where entire row == 0) and match with filter
                mask = ((selection != 0).any(axis=1) & self.mask)
                idx = mask.where(mask == 1)
                idx = mask[mask == idx].astype(np.bool_).index
                selection = selection.loc[mask]

                dfs.append([selection, idx])
            return dfs

        triad_dfs = graph_dfs(triad, batch_triad, True)
        diad_dfs = graph_dfs(diad, batch_diad, False)

        return triad_dfs, diad_dfs  # mask with current selections

    @st.cache
    def read_assessment(self, bucket_name, source_blob_name):
        df = self.read_data(bucket_name, source_blob_name)
        first_cols = ["Story", "Hashtag", "Common", "Function", "Role", "Experience", "Country"]
        og_columns = list(df.columns) + self.algo_types  # important for saving data

        df.columns = first_cols + [col.split("_")[-1].capitalize() for col in df.columns][7:]
        return df, og_columns

    def display(self, filtered_df, expander):
        tfidf = self.tfidf_story[self.mask]
        df = pd.concat([filtered_df.iloc[:expander.height, :2], tfidf.iloc[:expander.height,:]], axis=1)
        st.table(df)  # to hashtag data

    def add_story(self, idx):
        self.saved_stories.append(idx)

    def filter_data(self, expander):
        culture = [expander.leadership + expander.office + expander.people + expander.relationships]
        selectors = [expander.common, expander.function, expander.role, expander.experience, expander.country]
        algorithms = [expander.sentiment]

        # mask for text queries
        def query_mask():
            terms = expander.terms
            if "and" in terms:
                terms.remove("and")
                regstr = ''.join(["(?=.*" + t + ")" for t in terms])
                q_mask = np.array(self.df.Story.str.contains(regstr).values, dtype=np.bool_)
            else:
                regstr = '|'.join(terms)
                q_mask = np.array(self.df.Story.str.contains(regstr).values, dtype=np.bool_)
            return q_mask.reshape(-1, 1)

        # mask for survey-taker attributes
        def string_var_mask(selections, cols_names):
            stat = []
            for i, c in enumerate(cols_names):
                regstr = '|'.join(selections[i])
                stat.append(np.array(self.df[c].str.contains(regstr).values))
            return np.array(stat).squeeze().transpose().reshape(-1, len(stat))

        # mask for story category
        def cat_mask(logical_data):
            if logical_data:
                return np.array([(self.df[c] == 1).values for c in logical_data])[0]
            else:
                return np.ones((self.df.shape[0], 1))

        cats = cat_mask(culture).astype(np.bool_)
        strs = query_mask().astype(np.bool_)
        stat = string_var_mask(selectors, ["Common", "Function", "Role", "Experience", "Country"]).astype(np.bool_)
        algo = string_var_mask(algorithms, ["Sentiment"]).astype(np.bool_)

        mask = np.concatenate([strs, cats, stat, algo], axis=1)
        ph = mask[:, 0]
        for i in range(1, mask.shape[1]):
            ph = np.logical_and(ph, mask[:, i], dtype=np.bool_)

        if not np.array_equal(self.mask, ph):  # don't save if mask hasn't changed
            pd.DataFrame(ph).to_csv("filter.csv")  # store filter
            self.mask = ph
        return self.df[ph]

    @st.cache
    def tfidf(self):
        word_tracker = {}  # global tracker
        tfidf_story = {"Key Words": []}  # story tracker
        for txt in self.df.Story:
            try:
                tfIdfVectorizer = TfidfVectorizer(use_idf=True, stop_words='english')  # vectorize story data
                tfIdf = tfIdfVectorizer.fit_transform([txt])
                df = pd.DataFrame(tfIdf[0].T.todense(), index=tfIdfVectorizer.get_feature_names(),
                                  columns=["Importance"])
                # take top 15 tfidf words for each story, keep track in dict, return most import words in dataframe
                df = df.sort_values("Importance", ascending=False).iloc[:25, :].index
                for key in df:
                    if key not in word_tracker:
                        word_tracker[key] = 0
                    word_tracker[key] += 1
                tfidf_story["Key Words"].append(list(df.values[:5]))
            except:
                tfidf_story["Key Words"].append([])  # if txt is only stopwords
        tfIdf = pd.DataFrame.from_dict(word_tracker, orient='index')
        tfIdf = tfIdf.sort_values(tfIdf.columns[0], ascending=False)
        return tfIdf.iloc[:50, :].index, pd.DataFrame(tfidf_story)

    # @st.cache
    # def tsne(self, pp=30):
    #
    #     tsne = TSNE(n_components=2, verbose=0, perplexity=pp, n_iter=300)
    #     tsne_results = tsne.fit_transform(self.embeddings)
    #     data_tsne = {}
    #     data_tsne['tsne-2d-one'] = tsne_results[:, 0]
    #     data_tsne['tsne-2d-two'] = tsne_results[:, 1]