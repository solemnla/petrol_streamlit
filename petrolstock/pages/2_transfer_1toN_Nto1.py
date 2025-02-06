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

# Select one or more IDs
available_IDs = available_values['入库ID'].unique()
selected_IDs = st.multiselect(f'选择需要转出的ID:', available_IDs)

# 选择转出的ID及数量
st.write('选择转出（数量请填写正数）：')
output_df = pd.DataFrame(columns=operation_records.columns)

pre_defined_data = available_values.loc[available_values['入库ID'].isin(selected_IDs), ['品名','库区','罐号','库区罐号','入库ID', '实际量']]
output_df = pd.concat([output_df, pre_defined_data], ignore_index=True)

output_df['operation'] = '转出'

output_selection = st.data_editor(output_df, height=200, num_rows="dynamic", disabled=output_df.columns[-4:])

st.write(f'转出总数：{sum(output_selection["实际量"]):.3f}')

# 选择转入的ID及数量
st.write('选择移至：')
transfer_selection = st.data_editor(pd.DataFrame(columns=['库区','罐号','库区罐号','计划量','实际量']), height=200, num_rows="dynamic")

transfer_selection["实际量"] = transfer_selection["实际量"].astype(float)
st.write(f'转入总数：{sum(transfer_selection["实际量"]):.3f}')

# 检查转出总数与转入总数是否相等（3位小数）
if round(sum(output_selection["实际量"]),3) != round(sum(transfer_selection["实际量"]),3):
    st.error('转出总数与转入总数不相等')
else:
    if (len(output_selection)>1) & (len(transfer_selection)>1):
        st.error('此选项不支持多批次转多罐操作')
    elif transfer_selection['库区罐号'].isnull().values.any():
        st.error('请填写库区罐号')
    else:
        if st.button('生成转移表'):
            if len(output_selection) == 1:
                # copy the row in output_selection n times
                output_selection = pd.concat([output_selection]*len(transfer_selection), ignore_index=True)
                output_selection['实际量'] = -transfer_selection['实际量']
            elif len(transfer_selection) == 1:
                # copy the row in transfer_selection n times
                transfer_selection = pd.concat([transfer_selection]*len(output_selection), ignore_index=True)
                transfer_selection['实际量'] = output_selection['实际量']
                output_selection['实际量'] = -output_selection['实际量']
                
            # add the output_selection to the transfer_selection
            transfer_table = output_selection.copy()
            transfer_table[['库区','罐号','库区罐号','计划量','实际量']] = transfer_selection[['库区','罐号','库区罐号','计划量','实际量']]
            transfer_table.loc[:,'operation'] = '转入'
            transfer_table = pd.concat([output_selection, transfer_table], ignore_index=True)
            
            current_time = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            transfer_table['operation_time'] = current_time
            st.write('转移表：')
            st.session_state.final_table = st.data_editor(transfer_table, height=400)

        # Use the session state to confirm transfer
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
