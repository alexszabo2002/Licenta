import streamlit as st
import pandas as pd
import openpyxl
import os

import firebase.firebase_funcs as fb


def get_uploaded_file_name(uploaded_file):
    try:
        if uploaded_file is not None:
            file_name = uploaded_file.name
            if file_name.endswith(".csv"):
                file_name = file_name.split(".csv")[0]
            elif file_name.endswith(".xlsx"):
                file_name = file_name.split(".xlsx")[0]
            return file_name
        else:
            return None
    except Exception as e:
        st.error(f"Error getting file name: {e}")
        return None
    

def load_data(uploaded_file):
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
        except:
            df = pd.read_excel(io=uploaded_file, engine='openpyxl')
        st.write(df)    
    else:
        st.warning("Something went wrong while uploading the file.")
        st.stop()
    return df


def classify_columns(df):
    numerical_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
    temporal_columns = df.select_dtypes(include=['datetime64[ns]']).columns.tolist()
    return numerical_columns, categorical_columns, temporal_columns


def process_data(uploaded_file):
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
        except:
            df = pd.read_excel(io=uploaded_file, engine='openpyxl')

        with st.expander("Initial DataFrame"):
            st.write(df)
        
        with st.expander("Fill Missing Values"):

            missing_value_options = {}

            numerical_columns, categorical_columns, temporal_columns = classify_columns(df)

            for col in categorical_columns:
                unique_values = df[col].dropna().unique().tolist()
                missing_value_options[col] = st.selectbox(
                    f"How to fill missing values for categorical column '{col}'?",
                    options=['None', 'Other'] + unique_values,
                    key=f"categorical_{col}"
                )

            for col in numerical_columns:
                missing_value_options[col] = st.selectbox(
                    f"How to fill missing values for numerical column '{col}'?",
                    options=['None', 'Mean', 'Min', 'Max'],
                    key=f"numerical_{col}"
                )

            for col in temporal_columns:
                missing_value_options[col] = st.selectbox(
                    f"How to fill missing values for datetime column '{col}'?",
                    options=['None', 'Earliest', 'Latest'],
                    key=f"temporal_{col}"
                )

            df_filled = df.copy()

            for col, option in missing_value_options.items():
                if option != 'None':
                    if col in numerical_columns:
                        if option == 'Mean':
                            df_filled[col].fillna(df[col].mean(), inplace=True)
                        elif option == 'Min':
                            df_filled[col].fillna(df[col].min(), inplace=True)
                        elif option == 'Max':
                            df_filled[col].fillna(df[col].max(), inplace=True)
                    elif col in categorical_columns:
                        if option == 'Other':
                            df_filled[col].fillna('Other', inplace=True)
                        else:
                            df_filled[col].fillna(option, inplace=True)
                    elif col in temporal_columns:
                        if option == 'Earliest':
                            df_filled[col].fillna(df[col].min(), inplace=True)
                        elif option == 'Latest':
                            df_filled[col].fillna(df[col].max(), inplace=True)

        st.write("DataFrame after filling missing values")
        st.write(df_filled)

        return df, df_filled
    else:
        st.stop()


def save_dataframe_button(df, file_name):
    if st.button("Save DataFrame to Firebase"):
        user_id = 'alexszabo'
        url = fb.save_dataframe_to_firebase(df, user_id, file_name)
        st.success(f"DataFrame saved to Firebase: {url}")


def chart(df, chart_type, x_axis, y_axis, agg_func=None):
    if x_axis == y_axis:
        st.warning("The same variable cannot be selected for both the x-axis and y-axis.")
        return None

    if not x_axis or not y_axis:
        st.warning("Please select all options.")
        return None

    if chart_type == 'Bar Chart':
        if agg_func is None:
            st.warning("Aggregation function must be selected for Bar Chart.")
            return None

        if agg_func == 'Count':
            grouped_df = df.groupby(x_axis)[y_axis].count().reset_index()
        elif agg_func == 'Sum':
            grouped_df = df.groupby(x_axis)[y_axis].sum().reset_index()
        elif agg_func == 'Mean':
            grouped_df = df.groupby(x_axis)[y_axis].mean().reset_index()
        elif agg_func == 'Std':
            grouped_df = df.groupby(x_axis)[y_axis].std().reset_index()

        chart = st.bar_chart(grouped_df.set_index(x_axis))

    elif chart_type == 'Line Chart':
        if agg_func is None:
            st.warning("Aggregation function must be selected for Line Chart.")
            return None

        if agg_func == 'Count':
            grouped_df = df.groupby(x_axis)[y_axis].count().reset_index()
        elif agg_func == 'Sum':
            grouped_df = df.groupby(x_axis)[y_axis].sum().reset_index()
        elif agg_func == 'Mean':
            grouped_df = df.groupby(x_axis)[y_axis].mean().reset_index()
        elif agg_func == 'Std':
            grouped_df = df.groupby(x_axis)[y_axis].std().reset_index()

        chart = st.line_chart(grouped_df.set_index(x_axis))

    elif chart_type == 'Scatter Chart':
        chart = st.scatter_chart(df[[x_axis, y_axis]].set_index(x_axis))

    return chart


def set_chart_filters(numerical_columns, categorical_columns, temporal_columns):
    chart_type = st.selectbox(label="What chart would you like to display?",
                              options=('Bar Chart', 'Line Chart', 'Scatter Chart'))

    if chart_type == 'Bar Chart':
        x_axis = st.selectbox(label="Which is the targeted column for the x-axis?",
                               options=categorical_columns)
        y_axis = st.selectbox(label="Which is the targeted column for the y-axis?",
                              options=numerical_columns)
        agg_function = st.selectbox(label="Select aggregation function:",
                                    options=('Count', 'Sum', 'Mean', 'Std'))

    elif chart_type == 'Line Chart':
        x_axis = st.selectbox(label="Which is the targeted column for the x-axis?",
                              options=temporal_columns)
        y_axis = st.selectbox(label="Which is the targeted column for the y-axis?",
                              options=numerical_columns)
        agg_function = st.selectbox(label="Select aggregation function:",
                                    options=('Count', 'Sum', 'Mean', 'Std'))

    elif chart_type == 'Scatter Chart':
        x_axis = st.selectbox(label="Which is the targeted column for the x-axis?",
                              options=numerical_columns)
        y_axis = st.selectbox(label="Which is the targeted column for the y-axis?",
                              options=numerical_columns)
        agg_function = None

    return chart_type, x_axis, y_axis, agg_function


def images_to_firebase_loader():
    local_upload_folder = "temp_uploads"

    if not os.path.exists(local_upload_folder):
        os.makedirs(local_upload_folder)

    st.subheader("Upload Local Images to Firebase")

    uploaded_files = st.file_uploader("Choose images to upload", type=["png"], accept_multiple_files=True)

    if uploaded_files:
        st.write(f"Selected {len(uploaded_files)} file(s)")

    if st.button("Upload All Images"):
        user_id = 'alexszabo'
        for uploaded_file in uploaded_files:
            with open(os.path.join(local_upload_folder, uploaded_file.name), "wb") as f:
                f.write(uploaded_file.getbuffer())
            fb.save_image_to_firebase(os.path.join(local_upload_folder, uploaded_file.name), user_id)
        st.success("All images uploaded to Firebase")
