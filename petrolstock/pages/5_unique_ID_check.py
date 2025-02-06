import os
import pandas as pd
import streamlit as st

# 文件路径
filepath = st.text_input('请输入入库数据CSV文件路径：', value='petrolstock/operation_records.csv')  # 请将此路径替换为你的CSV文件路径

# Display the title of the app
st.title('条目检查')

# Load the data into a pandas DataFrame
df = pd.read_csv(filepath, encoding="GBK")

# Let the user select a column to filter by
filter_column = st.selectbox('Select a column to filter by:', df.columns, index=13)

# Get unique values from the selected column
unique_values = df[filter_column].unique()

# Let the user select one or more categories to filter the DataFrame
selected_values = st.multiselect(f'Select values in {filter_column}:', unique_values)

# Filter the DataFrame based on the user's selection
if selected_values:
    filtered_df = df[df[filter_column].isin(selected_values)]
else:
    filtered_df = df

# Display the filtered DataFrame
st.write('Filtered DataFrame:')
st.dataframe(filtered_df)
