import streamlit as st
import pandas as pd
import altair as alt


filename = "New_Query_2026_10_26_16_39_54.csv"
data = pd.read_csv(filename)

st.title("Email Filter")

chart = (
    alt.Chart(data)
    .mark_bar()
    .encode(
        y=alt.Y(
            "emailFrom:N",
            title="Email From",
            sort="-x",
            axis=alt.Axis(labelLimit=0, labelOverlap=False),
        ),
        x=alt.X("sum(unread_count):Q", title="Count"),
        yOffset="status:N",
        color=alt.Color(
            "status:N",
            title="Status",
            scale=alt.Scale(domain=["read", "unread"], range=["green", "red"]),
            legend=alt.Legend(orient="top"),
        ),
        tooltip=["emailFrom", "status", "unread_count"],
    )
    .properties(height=alt.Step(14))
)

with st.container(height=600):
    st.altair_chart(chart, width="stretch")
