import streamlit as st
import os
import pandas as pd
import plotly.express as px
from Senti import extract_video_id, analyze_sentiment, bar_chart, plot_sentiment
from YoutubeCommentScrapper import save_video_comments_to_csv, get_channel_info, youtube, get_channel_id, get_video_stats


def delete_non_matching_csv_files(directory_path, video_id):
    for file_name in os.listdir(directory_path):
        if not file_name.endswith('.csv'):
            continue
        if file_name == f'{video_id}_analysis.csv':
            continue
        os.remove(os.path.join(directory_path, file_name))


st.set_page_config(page_title='SentimentAnalysis', page_icon='LOGO.png')

st.sidebar.title("Sentiment Analysis")
st.sidebar.header("Enter YouTube Link")
youtube_link = st.sidebar.text_input("Link")

directory_path = os.getcwd()

if youtube_link:
    video_id = extract_video_id(youtube_link)
    channel_id = get_channel_id(video_id)

    if video_id:

        st.sidebar.write("Video ID:", video_id)

        # SAVE CSV
        csv_file = save_video_comments_to_csv(video_id)

        delete_non_matching_csv_files(directory_path, video_id)

        st.sidebar.success("Comments saved!")
        st.sidebar.download_button(
            label="Download Comments",
            data=open(csv_file, 'rb').read(),
            file_name=os.path.basename(csv_file),
            mime="text/csv"
        )

        # LOAD DATAFRAME
        df = pd.read_csv(csv_file)


        # CHANNEL INFO


        channel_info = get_channel_info(youtube, channel_id)

        col1, col2 = st.columns(2)

        with col1:
            st.image(channel_info['channel_logo_url'], width=200)

        with col2:
            st.title(channel_info['channel_title'])

        col3, col4, col5 = st.columns(3)

        col3.metric("Total Videos", channel_info['video_count'])
        col4.metric("Created On", channel_info['channel_created_date'][:10])
        col5.metric("Subscribers", channel_info["subscriber_count"])

        stats = get_video_stats(video_id)

        st.subheader("Video Stats")
        col6, col7, col8 = st.columns(3)

        col6.metric("Views", stats["viewCount"])
        col7.metric("Likes", stats["likeCount"])
        col8.metric("Comments", stats["commentCount"])

        st.video(youtube_link)


        # SENTIMENT


        results = analyze_sentiment(csv_file)

        col9, col10, col11 = st.columns(3)

        col9.metric("Positive", results['num_positive'])
        col10.metric("Negative", results['num_negative'])
        col11.metric("Neutral", results['num_neutral'])

        bar_chart(csv_file)
        plot_sentiment(csv_file)


        # FAKE DETECTION SECTION


        if "Fake_Detection" in df.columns:

            st.subheader("🚨 Fake Comment Analysis")

            fake_counts = df["Fake_Detection"].value_counts().reset_index()
            fake_counts.columns = ["Type", "Count"]

            colA, colB, colC = st.columns(3)

            colA.metric("Fake", (df["Fake_Detection"] == "Fake").sum())
            colB.metric("Real", (df["Fake_Detection"] == "Real").sum())
            colC.metric("Suspicious", (df["Fake_Detection"] == "Suspicious").sum())

            fig_fake = px.pie(
                fake_counts,
                names="Type",
                values="Count",
                title="Fake vs Real Distribution",
                color="Type",
                color_discrete_map={
                    "Fake": "red",
                    "Real": "green",
                    "Suspicious": "orange"
                }
            )

            st.plotly_chart(fig_fake)

        st.subheader("Channel Description")
        st.write(channel_info['channel_description'])

    else:
        st.error("Invalid YouTube link")