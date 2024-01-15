import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import operator

class CollaborationFilter():
    def __init__(self):
        # self.animes = pd.read_csv('api/anime.csv')
        # self.ratings = pd.read_csv('api/rating.csv')

        cosmetics = pd.read_csv('api/base_review.csv')

        self.cosmetics = cosmetics.drop_duplicates(subset='brand_id')
        self.cosme_ratings = cosmetics.iloc[:, :3]

        ### not required
        # self.ratings = self.ratings[self.ratings.rating != -1]
        #
        # # avg number of ratings given per anime
        # ratings_per_anime = self.ratings.groupby('anime_id')['rating'].count()
        #
        # ratings_per_user = self.ratings.groupby('user_id')['rating'].count()
        #
        # # counts of ratings per anime as a df
        # ratings_per_anime_df = pd.DataFrame(ratings_per_anime)
        # # remove if < 1000 ratings
        # filtered_ratings_per_anime_df = ratings_per_anime_df[ratings_per_anime_df.rating >= 1000]
        # # build a list of anime_ids to keep
        # popular_anime = filtered_ratings_per_anime_df.index.tolist()
        #
        # # counts ratings per user as a df
        # ratings_per_user_df = pd.DataFrame(ratings_per_user)
        # # remove if < 500
        # filtered_ratings_per_user_df = ratings_per_user_df[ratings_per_user_df.rating >= 500]
        # # build a list of user_ids to keep
        # prolific_users = filtered_ratings_per_user_df.index.tolist()
        #
        # filtered_ratings = self.ratings[self.ratings.user_id.isin(prolific_users)]
        #
        # rating_matrix = filtered_ratings.pivot_table(index='user_id', columns='anime_id', values='rating')
        # # replace NaN values with 0
        # self.rating_matrix = rating_matrix.fillna(0)

        rating_matrix = self.cosme_ratings.pivot_table(index='user_id', columns='brand_id', values='rate')
        # replace NaN values with 0
        self.rating_matrix = rating_matrix.fillna(0)

    def add_new_user_ratings(self, user_id, ratings):
        # Check if the user already exists in the ratings DataFrame
        if user_id in self.rating_matrix.index:
            print(f"User {user_id} already exists in the rating matrix.")
            return

        # Create a new row for the user with NaN values
        new_user_row = pd.Series(index=self.rating_matrix.columns, name=user_id)
        new_user_row = new_user_row.fillna(0)

        # Update the new user row with the provided anime ratings
        for anime_id, rating in ratings.items():
            if anime_id in self.rating_matrix.columns:
                new_user_row[anime_id] = rating
            else:
                print(f"Ignoring unknown anime_id {anime_id}.")

        # Add the new user row to the rating matrix
        # self.rating_matrix = self.rating_matrix.append(new_user_row)
        transposed = pd.DataFrame(new_user_row).transpose()
        new_rating_matrix = pd.concat([self.rating_matrix, transposed])
        print(f"New user {user_id} added to the rating matrix.")
        return new_rating_matrix

    def infer(self, rating_matrix, current_user=226):
        # try it out
        similar_user_indices = self.similar_users(current_user, rating_matrix)
        print(f"{similar_user_indices=}")

        # try it out
        recommended = self.recommend_item(current_user, similar_user_indices, rating_matrix)
        return recommended

    def similar_users(self, user_id, matrix, k=3):
        # create a df of just the current user
        user = matrix[matrix.index == user_id]

        # and a df of all other users
        other_users = matrix[matrix.index != user_id]

        # calc cosine similarity between user and each other user
        similarities = cosine_similarity(user, other_users)[0].tolist()

        # create list of indices of these users
        indices = other_users.index.tolist()

        # create key/values pairs of user index and their similarity
        index_similarity = dict(zip(indices, similarities))

        # sort by similarity
        index_similarity_sorted = sorted(index_similarity.items(), key=operator.itemgetter(1))
        index_similarity_sorted.reverse()

        # grab k users off the top
        top_users_similarities = index_similarity_sorted[:k]
        users = [u[0] for u in top_users_similarities]

        return users

    def recommend_item(self, user_index, similar_user_indices, matrix, items=3):
        # load vectors for similar users
        similar_users = matrix[matrix.index.isin(similar_user_indices)]
        # calc avg ratings across the 3 similar users
        similar_users = similar_users.mean(axis=0)
        # convert to dataframe so its easy to sort and filter
        similar_users_df = pd.DataFrame(similar_users, columns=['mean'])

        # load vector for the current user
        user_df = matrix[matrix.index == user_index]
        # transpose it so its easier to filter
        user_df_transposed = user_df.transpose()
        # rename the column as 'rating'
        user_df_transposed.columns = ['rate']
        # remove any rows without a 0 value. Anime not watched yet
        user_df_transposed = user_df_transposed[user_df_transposed['rate'] == 0]
        # generate a list of animes the user has not seen
        animes_unseen = user_df_transposed.index.tolist()

        # filter avg ratings of similar users for only anime the current user has not seen
        similar_users_df_filtered = similar_users_df[similar_users_df.index.isin(animes_unseen)]
        # order the dataframe
        similar_users_df_ordered = similar_users_df.sort_values(by=['mean'], ascending=False)
        # grab the top n anime
        top_n_anime = similar_users_df_ordered.head(items)
        top_n_anime_indices = top_n_anime.index.tolist()
        # lookup these anime in the other dataframe to find names
        # anime_information = self.animes[self.animes['anime_id'].isin(top_n_anime_indices)]
        anime_information = self.cosmetics[self.cosmetics['brand_id'].isin(top_n_anime_indices)]

        return anime_information  # items

    def get_filter_list(self, product_name) -> list[str]:
        product_list = product_name.split(',')

        # Usage example:
        new_user_id = 99999
        new_anime_ratings = {204: 5, 506: 4, 393: 3}
        new_matrix = self.add_new_user_ratings(new_user_id, new_anime_ratings)

        recommended = self.infer(rating_matrix=new_matrix, current_user=new_user_id)

        to_recommend = recommended['brand'].to_list()

        return to_recommend


collabo_filter = CollaborationFilter()