import streamlit as st

from authentication.auth import get_authenticator
from pages_funcs.data_analysis_funcs import get_uploaded_file_name, process_data, classify_columns, save_dataframe_button, set_chart_filters, chart, images_to_firebase_loader

authenticator = get_authenticator()

st.markdown("# Data Analysis")

uploaded_file = st.file_uploader(label="Upload a file", type=['csv','xlsx'], help="only csv or xlsx files are supported")

file_name = get_uploaded_file_name(uploaded_file)

df_init, df_filled = process_data(uploaded_file)

numerical_columns, categorical_columns, temporal_columns = classify_columns(df_filled)

save_dataframe_button(df_filled, file_name)

tab_statistics, tab_charts = st.tabs(["Descriptive Statistics", "Charts"])

with tab_statistics:
    st.write(df_filled.describe(include="all"))

with tab_charts:
    filters_col, display_col = st.columns([0.4, 0.6])

    with filters_col:
        chart_type, x_axis, y_axis, agg_function = set_chart_filters(numerical_columns, categorical_columns, temporal_columns)

    with display_col:
        fig = chart(df_filled, chart_type, x_axis, y_axis, agg_function)

    images_to_firebase_loader()
