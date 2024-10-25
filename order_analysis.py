import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
from io import StringIO
import itertools
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np


def main():
    st.title("Product Order Analysis Dashboard")

    # File Upload Section
    uploaded_file = st.file_uploader("Upload a CSV File for Analysis", type=["csv"])

    # Load Default Data or Uploaded File
    if uploaded_file is not None:
        # Load from uploaded file
        try:
            data = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Error reading the uploaded file: {str(e)}")
    else:
        # Provide an option to upload a CSV file if default file is not available
        st.info("Please upload a CSV file for analysis.")
        st.stop()

    # Validate Data Columns
    expected_columns = [
        "ID",
        "orderdate",
        "quantity",
        "shipcountrycode",
        "ref_total",
        "Vip",
    ]
    if not all(column in data.columns for column in expected_columns):
        missing_columns = [
            column for column in expected_columns if column not in data.columns
        ]
        st.error(
            f"The uploaded CSV file does not have the expected columns. Missing columns: {', '.join(missing_columns)}"
        )
        st.stop()

    # Data Preprocessing
    data["orderdate"] = pd.to_datetime(data["orderdate"], errors="coerce")
    data.dropna(subset=["orderdate"], inplace=True)
    data["quantity"] = (
        pd.to_numeric(data["quantity"], errors="coerce").fillna(0).astype(int)
    )
    data["ref_total"] = data["ref_total"].astype(
        str
    )  # Treat product references as strings

    # Sidebar Filters for Analysis
    st.sidebar.header("Filter Options")
    vip_filter = st.sidebar.selectbox(
        "Select Customer Type", ["All Customers", "VIP", "Non-VIP"]
    )
    date_range = st.sidebar.date_input(
        "Select Date Range", [data["orderdate"].min(), data["orderdate"].max()]
    )
    all_countries = ["All Countries"] + list(data["shipcountrycode"].unique())
    selected_countries = st.sidebar.multiselect(
        "Select Countries", all_countries, default="All Countries"
    )
    all_refs = ["All Refs"] + list(data["ref_total"].unique())
    selected_product_refs = st.sidebar.multiselect(
        "Select Product References", all_refs, default="All Refs"
    )

    # Applying Filters
    if "All Countries" in selected_countries:
        selected_countries = data["shipcountrycode"].unique()
    if "All Refs" in selected_product_refs:
        selected_product_refs = data["ref_total"].unique()

    filtered_data = data[
        (data["orderdate"] >= pd.to_datetime(date_range[0]))
        & (data["orderdate"] <= pd.to_datetime(date_range[1]))
        & (data["shipcountrycode"].isin(selected_countries))
        & (data["ref_total"].isin(selected_product_refs))
    ]

    # Apply VIP filter
    if vip_filter == "VIP":
        filtered_data = filtered_data[filtered_data["Vip"] == 1]
    elif vip_filter == "Non-VIP":
        filtered_data = filtered_data[filtered_data["Vip"] == 0]

    if filtered_data.empty:
        st.warning(
            "No data available for the selected filters. Please adjust your filters."
        )
        st.stop()
    else:
        # Dropdown for Analysis Selection
        analysis_option = st.selectbox(
            "Select Analysis Type", ["Product Analysis", "Country Analysis"]
        )
        if analysis_option == "Country Analysis":
            # Country Analysis Section
            st.header("Country Analysis")
            total_orders = filtered_data["ID"].nunique()
            unique_countries = filtered_data["shipcountrycode"].nunique()
            top_three_countries = (
                filtered_data["shipcountrycode"].value_counts().head(3)
            )

            st.metric("Total Orders", total_orders)
            st.metric("Unique Countries", unique_countries)

            st.write("Country Orders in Descending Order:")
            orders_by_country = (
                filtered_data["shipcountrycode"].value_counts().reset_index()
            )
            orders_by_country.columns = ["Country", "Number of Orders"]
            st.dataframe(orders_by_country)

            # Distribution of Orders by Country
            orders_by_country = (
                filtered_data["shipcountrycode"].value_counts().reset_index()
            )
            orders_by_country.columns = ["Country", "Number of Orders"]
            fig = px.bar(
                orders_by_country,
                x="Country",
                y="Number of Orders",
                title="Distribution of Orders by Country",
            )
            st.plotly_chart(fig)

        elif analysis_option == "Product Analysis":
            # Product Analysis Section
            st.header("Product Analysis")
            total_quantity_sold = filtered_data["quantity"].sum()
            average_order_size = filtered_data.groupby("ID")["quantity"].sum().mean()

            st.metric("Total Quantity Sold", total_quantity_sold)
            st.metric("Average Order Size", f"{average_order_size:.2f}")

            # Popular Products by Quantity
            popular_products = (
                filtered_data.groupby("ref_total")["quantity"]
                .sum()
                .sort_values(ascending=False)
                .reset_index()
                .head(10)
            )
            fig = px.bar(
                popular_products,
                x="ref_total",
                y="quantity",
                title="Top 10 Popular Products by Quantity",
                labels={
                    "ref_total": "Product Reference",
                    "quantity": "Total Quantity Sold",
                },
            )
            st.plotly_chart(fig)

            # Analysis of Product Reference Co-occurrences
            st.subheader("Product Reference Co-occurrence Analysis")
            order_groups = filtered_data.groupby("ID")["ref_total"].apply(list)
            cooccurrences = Counter()
            for group in order_groups:
                cooccurrences.update(itertools.combinations(sorted(group), 2))
            cooccurrence_df = pd.DataFrame(
                cooccurrences.items(), columns=["Product Pair", "Co-occurrence Count"]
            )
            cooccurrence_df = cooccurrence_df.sort_values(
                by="Co-occurrence Count", ascending=False
            )
            st.write("Product Reference Co-occurrences in Orders:")
            st.dataframe(cooccurrence_df)


if __name__ == "__main__":
    main()

