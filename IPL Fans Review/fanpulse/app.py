import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import plotly.express as px
from distutils.version import LooseVersion

# Import your scraper function
from scraper import scrape_tweets

st.set_page_config(
    page_title="FanPulse AI",
    layout="wide"
)

st.title("⚽ FanPulse AI")
st.subheader("AI-Powered Fan Engagement & Sentiment Analysis")

# Sidebar
st.sidebar.header("Search Settings")

keyword = st.sidebar.text_input(
    "Enter Team / Player / Topic",
    "IPL"
)

limit = st.sidebar.slider(
    "Number of Tweets",
    10,
    100,
    30
)

analyze = st.sidebar.button("Run Analysis")

if analyze:
    # 1. ADDED TRY-EXCEPT BLOCK FOR ERROR HANDLING
    try:
        with st.spinner("Collecting tweets and running AI model... This may take a minute."):
            df = scrape_tweets(keyword, limit)

        # 2. CHECK IF DATAFRAME IS EMPTY BEFORE RENDERING
        if df is not None and not df.empty:
            st.success("Analysis Completed!")

            # KPIs
            positive = len(df[df["Sentiment"] == "Positive"])
            negative = len(df[df["Sentiment"] == "Negative"])
            neutral = len(df[df["Sentiment"] == "Neutral"])

            avg_engagement = round(df["Engagement Score"].mean(), 2)

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Positive", positive)
            col2.metric("Negative", negative)
            col3.metric("Neutral", neutral)
            col4.metric("Avg Engagement", avg_engagement)

            # Data Table
            st.subheader("📄 Tweets Dataset")
            st.dataframe(df)

            # Sentiment Chart
            st.subheader("📊 Sentiment Distribution")
            sentiment_counts = df["Sentiment"].value_counts()

            # 3. ADDED CUSTOM COLORS TO CHART
            if not sentiment_counts.empty:
                fig = px.bar(
                    x=sentiment_counts.index,
                    y=sentiment_counts.values,
                    labels={"x": "Sentiment", "y": "Count"},
                    title="Fan Sentiment Analysis",
                    color=sentiment_counts.index,
                    color_discrete_map={
                        "Positive": "#28a745", # Green
                        "Neutral": "#6c757d",  # Gray
                        "Negative": "#dc3545"  # Red
                    }
                )
                st.plotly_chart(fig)

            # WordCloud
            st.subheader("☁ Trending Fan Discussions")
            text = " ".join(df["Tweet"].astype(str))

            if text.strip():
                wordcloud = WordCloud(
                    width=1000,
                    height=500,
                    background_color="white"
                ).generate(text)

                fig2, ax = plt.subplots()
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis("off")
                st.pyplot(fig2)

            # Top Positive Tweets
            st.subheader("🔥 Most Positive Tweets")
            top_positive = df[df["Sentiment"] == "Positive"]
            if not top_positive.empty:
                st.dataframe(
                    top_positive.sort_values(by="Confidence", ascending=False).head(5)
                )
            else:
                st.info("No positive tweets found in this batch.")

            # Top Negative Tweets
            st.subheader("⚠ Most Negative Tweets")
            top_negative = df[df["Sentiment"] == "Negative"]
            if not top_negative.empty:
                st.dataframe(
                    top_negative.sort_values(by="Confidence", ascending=False).head(5)
                )
            else:
                st.info("No negative tweets found in this batch.")

            # Download
            csv = df.to_csv(index=False)
            st.download_button(
                "⬇ Download Dataset",
                csv,
                # Makes the filename dynamic based on the search!
                file_name=f"fanpulse_{keyword.replace(' ', '_')}.csv", 
                mime="text/csv"
            )
        else:
            st.warning("No tweets were collected. Twitter might have shown a captcha or no results were found.")

    except Exception as e:
        # Prevents the app from crashing and shows the error safely in the UI
        st.error("An error occurred while connecting to Twitter or processing the data.")
        st.error(f"Details: {str(e)}")