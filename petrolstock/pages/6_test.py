import streamlit as st

import pandas as pd

# Sample data

data = {'入库ID': [1, 2, 3, 4], '实际量': [10, 0, 5, 15]}
filtered_df = pd.DataFrame(data)

# Display the unique IDs with remaining values greater than 0

available_values = filtered_df.groupby('入库ID')['实际量'].sum().reset_index()
available_values = available_values[available_values['实际量'] > 0]

# Create two columns

col1, col2 = st.columns(2)

# Display dataframe in the first column

with col1:
    st.write('剩余值大于0的条目：')
    st.dataframe(available_values)

# Initialize an empty list to store selected IDs

selected_IDs = []

# Display checkboxes in the second column

with col2:
    st.write('选择需要出库的ID：')
    for id in available_values['入库ID']:
        if st.checkbox(f'选择ID {id}', key=f'checkbox_{id}'):
            selected_IDs.append(id)

# Display selected IDs

st.write('Selected IDs:', selected_IDs)