import os
import pandas as pd
import streamlit as st

# 文件路径
file_dir = st.text_input('请输入数据文件夹的路径：（读取文件夹下operation_records.csv）', value='~/Downloads/petrolstock')  # 请将此路径替换为你的CSV文件路径

# Display the title of the app
st.title('转移操作')

# Load the data into a pandas DataFrame
operation_records = pd.read_csv(os.path.join(file_dir, 'operation_records.csv'), encoding="GBK")

# Let the user select a column to filter by
filter_column = st.selectbox('用于筛选的列：', operation_records.columns, index=4)

# Get unique values from the selected column. Let the user select one or more categories to filter the DataFrame
unique_values = operation_records[filter_column].unique()
selected_values = st.multiselect(f'在{filter_column}中筛选:', unique_values)

# Filter the DataFrame
if selected_values:
    filtered_df = operation_records[operation_records[filter_column].isin(selected_values)]
else:
    filtered_df = operation_records

# Display the filtered DataFrame
st.write('所有记录：')
st.dataframe(filtered_df)

# Display the unique IDs with remaining values greater than 0
available_values = filtered_df.groupby(['品名','库区','罐号','库区罐号','入库ID'])['实际量'].sum().reset_index()
available_values = available_values[available_values['实际量'] > 0]
st.write('剩余值大于0的条目：')
st.dataframe(available_values)

# 选择转出的ID及数量
st.write('选择转出（数量请填写正数，一转多时分多条记录）：')
output_selection = st.data_editor(pd.DataFrame(columns=operation_records.columns), height=200, num_rows="dynamic", disabled=operation_records.columns[-3:])

output_selection[['计划量','实际量']] = output_selection[['计划量','实际量']].astype(float)

if output_selection[['库区罐号', '实际量', '入库ID']].isnull().values.any():
    st.error('库区罐号、实际量、入库ID不能为空！')

check_table = output_selection[['库区罐号','入库ID', '实际量']].merge(available_values.rename(columns={'实际量':'存量'}), on=['库区罐号','入库ID'])
if sum(check_table['实际量'] > check_table['存量']) > 0:
    st.error('出库数量大于存量！')

output_selection['operation'] = '转出'

st.write('选择移至：（多转一时分多条记录）')
transfer_selection = output_selection.copy()
output_selection[['计划量','实际量']] = -output_selection[['计划量','实际量']]

transfer_selection['operation'] = '转入'
transfer_selection[['库区','罐号','库区罐号']] = pd.NA
transfer_selection = st.data_editor(transfer_selection, disabled=list(operation_records.columns[-4:])+['计划量', '实际量'])

if transfer_selection[['库区罐号']].isnull().values.any():
    st.error('库区罐号不能为空！')

if st.button('生成转移表'):
    transfer_table = pd.concat([output_selection, transfer_selection], ignore_index=True)
    
    current_time = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    transfer_table['operation_time'] = current_time
    st.write('转移表：')
    st.session_state.final_table = st.data_editor(transfer_table, height=400)

if st.button('确认转移'):
    if 'final_table' not in st.session_state:
        st.error("请先生成转移表")
    else:
        final_table = st.session_state.final_table
        # 更新operation_records.csv
        operation_records = pd.concat([operation_records, final_table], ignore_index = True)
        operation_records.to_csv(os.path.join(file_dir, 'operation_records.csv'), encoding="GBK", index=False)
        
        # 显示成功信息
        st.success(f'新行已添加并更新至{os.path.join(file_dir, 'operation_records.csv')}！')