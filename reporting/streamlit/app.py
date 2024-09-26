import streamlit as st
import duckdb
import pandas as pd
from google.cloud import secretmanager

# setup
project_id = 'btibert-ba882-fall24'
secret_id = 'mother_duck'   #<---------- this is the name of the secret you created
version_id = 'latest'

# db setup
db = 'awsblogs'
schema = "stage"
db_schema = f"{db}.{schema}"

# # instantiate the services 
sm = secretmanager.SecretManagerServiceClient()

# Build the resource name of the secret version
name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

# Access the secret version
response = sm.access_secret_version(request={"name": name})
md_token = response.payload.data.decode("UTF-8")

# initiate the MotherDuck connection through an access token through
md = duckdb.connect(f'md:?motherduck_token={md_token}') 



# Fetch data and cache based on the query
# @st.cache_data
# def fetch_data(query):
#     return md.sql(query).df()


# fetch the min/max post dates
sql = """
select 
    min(published) as min,
    max(published) as max,
from
    awsblogs.stage.posts
"""
date_range = md.sql(sql).df()
start_date = date_range['min'].to_list()[0]
end_date = date_range['max'].to_list()[0]


# Dashboard layout
st.title("AWS Blogs Dashboard")

# Sidebar filters
st.sidebar.header("Filters")
author_filter = st.sidebar.text_input("Search by Author")
date_filter = st.sidebar.date_input("Post Start Date", (start_date, end_date))


# # SQL Queries for the dashboard
# post_count_query = f"SELECT COUNT(*) AS post_count FROM {db_schema}.posts"
# author_count_query = "SELECT COUNT(DISTINCT name) AS author_count FROM authors"
# tag_count_query = "SELECT COUNT(DISTINCT term) AS tag_count FROM tags"
# latest_posts_query = "SELECT title, published, summary FROM posts ORDER BY published DESC LIMIT 5"

# # Sidebar filters
# st.sidebar.header("Filters")
# author_filter = st.sidebar.text_input("Search by Author")
# date_filter = st.sidebar.date_input("Filter by Date")

# # Fetch metrics
# post_count = fetch_data(post_count_query).iloc[0, 0]
# author_count = fetch_data(author_count_query).iloc[0, 0]
# tag_count = fetch_data(tag_count_query).iloc[0, 0]

# # Dashboard layout
# st.title("MotherDuck Data Warehouse Dashboard")

# # Overview Section
# st.header("Overview")
# col1, col2, col3 = st.columns(3)
# col1.metric("Total Posts", post_count)
# col2.metric("Total Authors", author_count)
# col3.metric("Total Tags", tag_count)

# # Display latest posts
# st.subheader("Latest Posts")
# latest_posts = fetch_data(latest_posts_query)
# st.write(latest_posts)

# # Post Details Section
# st.subheader("Post Details")
# if author_filter:
#     posts_by_author_query = f"SELECT * FROM posts WHERE id IN (SELECT post_id FROM authors WHERE name LIKE '%{author_filter}%')"
#     posts_by_author = fetch_data(posts_by_author_query)
#     st.write(posts_by_author)

# if date_filter:
#     posts_by_date_query = f"SELECT * FROM posts WHERE published >= '{date_filter}'"
#     posts_by_date = fetch_data(posts_by_date_query)
#     st.write(posts_by_date)

# # Display posts table
# st.subheader("Explore Posts")
# all_posts_query = "SELECT * FROM posts"
# all_posts = fetch_data(all_posts_query)
# st.write(all_posts)

# # Additional tables
# st.subheader("Authors")
# all_authors_query = "SELECT * FROM authors"
# all_authors = fetch_data(all_authors_query)
# st.write(all_authors)

# st.subheader("Tags")
# all_tags_query = "SELECT * FROM tags"
# all_tags = fetch_data(all_tags_query)
# st.write(all_tags)

# st.subheader("Images")
# all_images_query = "SELECT * FROM images"
# all_images = fetch_data(all_images_query)
# st.write(all_images)

# st.subheader("Links")
# all_links_query = "SELECT * FROM links"
# all_links = fetch_data(all_links_query)
# st.write(all_links)
