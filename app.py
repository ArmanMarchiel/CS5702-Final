import pandas as pd
import altair as alt
import streamlit as st
import os

# Construct the absolute path to the CSV file
csv_file_path = os.path.join(os.path.dirname(__file__), "movie_database.csv")

# Load the data with error handling
try:
    df = pd.read_csv(csv_file_path)
except FileNotFoundError:
    st.error(f"Error: Could not find the CSV file at {csv_file_path}.")
    st.stop()
except Exception as e:
    st.error(f"An error occurred while reading the CSV: {e}")
    st.stop()

# Data Cleaning and Transformation
def clean_currency(value):
    if isinstance(value, str):
        value = value.replace('$', '').replace(',', '')
        try:
            return float(value)
        except ValueError:
            return None  # Handle cases where conversion fails
    return value

numeric_cols = ["Budget", "Adjusted Budget", "Domestic Box Office", "Adjusted Domestic Box Office", "International Box Office", "Adjusted International Box Office", "Total P/L", "Adjusted Total P/L"]
for col in numeric_cols:
    df[col] = df[col].apply(clean_currency)

df['Release Date'] = pd.to_datetime(df['Release Date'])

# Corrected ROI calculation (using adjusted values)
df['ROI'] = ((df['Adjusted International Box Office'] / (df['Adjusted Budget'] * 2.5)) - 1) * 100

df['Year'] = df['Release Date'].dt.year

# Expand Cast
df['Cast'] = df['Cast'].str.strip('""').str.split(', ')
df_exploded = df.explode('Cast')
df_exploded['Cast'] = df_exploded['Cast'].str.strip()

# Streamlit App
st.set_page_config(layout="wide")  # Wider layout
st.title("Movie Data Dashboard")

# Filters
studio_filter = st.selectbox("Studio", ["All"] + list(df['Studio'].unique()))

# Filter franchises based on selected studio (only show if a studio is selected)
if studio_filter != "All":
    filtered_franchises = df[df['Studio'] == studio_filter]['Franchise'].unique()
    franchise_filter = st.selectbox("Franchise", ["All"] + list(filtered_franchises))
else:
    franchise_filter = st.selectbox("Franchise", ["All"] + list(df['Franchise'].unique()))

filtered_df = df.copy()

if studio_filter != "All":
    filtered_df = filtered_df[filtered_df['Studio'] == studio_filter]
if franchise_filter != "All":
    filtered_df = filtered_df[filtered_df['Franchise'] == franchise_filter]

# Containers
col1, col2, col3 = st.columns(3)

with col1:
    avg_roi = filtered_df['ROI'].mean()
    st.metric("Average ROI", f"{avg_roi:.2f}%")

with col2:
    actor_roi = df_exploded.groupby('Cast')['ROI'].mean().reset_index()
    actor_counts = df_exploded.groupby('Cast')['Movie Title'].count().reset_index()
    actor_roi = actor_roi.merge(actor_counts, on='Cast', how='left')
    actor_roi = actor_roi[actor_roi['Movie Title'] >= 2]
    top_5_actors = actor_roi.nlargest(5, 'ROI')
    top_5_actors['ROI'] = top_5_actors['ROI'].round(1)
    st.subheader("Top 5 ROI Actors", anchor=False)
    st.dataframe(top_5_actors)

with col3:
    actor_roi = df_exploded.groupby('Cast')['ROI'].mean().reset_index()
    actor_counts = df_exploded.groupby('Cast')['Movie Title'].count().reset_index()
    actor_roi = actor_roi.merge(actor_counts, on='Cast', how='left')
    actor_roi = actor_roi[actor_roi['Movie Title'] >= 2]
    bottom_5_actors = actor_roi.nsmallest(5, 'ROI')
    bottom_5_actors['ROI'] = bottom_5_actors['ROI'].round(1)
    st.subheader("Bottom 5 ROI Actors", anchor=False)
    st.dataframe(bottom_5_actors)


# Create calculated fields for millions (FOR ALTAIR VERSION 4)
filtered_df['AdjustedBudget_M'] = filtered_df['Adjusted Budget'] / 1000000
filtered_df['AdjustedInternationalBoxOffice_M'] = filtered_df['Adjusted International Box Office'] / 1000000

# Visualizations
scatter_plot = alt.Chart(filtered_df).mark_circle(size=60).encode(
    x=alt.X('Release Date:T', title="Release Date"),
    y=alt.Y('ROI:Q', title="ROI (%)"),
    color=alt.Color('Studio:N', title="Studio"),
    tooltip=[
        alt.Tooltip('Movie Title:N'),
        alt.Tooltip('Release Date:T'),
        alt.Tooltip('AdjustedBudget_M:Q', title="Adjusted Budget (M)", format="$.1f"),  # Use calculated field
        alt.Tooltip('AdjustedInternationalBoxOffice_M:Q', title="Adjusted International Box Office (M)", format="$.1f"),  # Use calculated field
        alt.Tooltip('ROI:Q', format=".1f")
    ]
).properties(
    title="ROI Over Time"
).interactive()

box_plot = alt.Chart(filtered_df).mark_boxplot().encode(
    x=alt.X('Studio:N', title="Studio", sort=alt.EncodingSortField(field="ROI", order="descending")),
    y=alt.Y('ROI:Q', title="ROI (%)"),
    color=alt.Color('Studio:N', title="Studio"),
    tooltip=alt.Tooltip('ROI:Q', format=".1f") # Added tooltip to boxplot
).properties(
    title="ROI Distribution by Studio"
).interactive()

if studio_filter != "All":
    box_plot = alt.Chart(filtered_df).mark_boxplot().encode(
        x=alt.X('Franchise:N', title="Franchise", sort=alt.EncodingSortField(field="ROI", order="descending")),
        y=alt.Y('ROI:Q', title="ROI (%)"),
        color=alt.Color('Franchise:N', title="Franchise"),
        tooltip=alt.Tooltip('ROI:Q', format=".1f") # Added tooltip to boxplot
    ).properties(
        title="ROI Distribution by Franchise"
    ).interactive()

st.altair_chart(scatter_plot, use_container_width=True)
st.altair_chart(box_plot, use_container_width=True)