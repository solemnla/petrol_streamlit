import os
import pandas as pd
import streamlit as st

# 文件路径
file_dir = st.text_input('请输入数据文件夹的路径：（读取文件夹下operation_records.csv）', value='~/Downloads/petrolstock')  # 请将此路径替换为你的CSV文件路径

# Display the title of the app
st.title('出库操作')

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
selected_IDs = st.multiselect(f'选择需要出库的ID:', available_IDs)

# 选择出库的ID及数量
st.write('选择出库（数量请填写正数）：')
output_df = pd.DataFrame(columns=operation_records.columns)

pre_defined_data = available_values.loc[available_values['入库ID'].isin(selected_IDs), ['品名','库区','罐号','库区罐号','入库ID', '实际量']]
output_df = pd.concat([output_df, pre_defined_data], ignore_index=True)

output_df['operation'] = '出库'

output_selection = st.data_editor(output_df, height=200, num_rows="dynamic", disabled=output_df.columns[-4:])

st.write(f'出库总数：{sum(output_selection["实际量"]):.3f}')

# 分配出库ID
id_dict = {}
for contract in operation_records.loc[operation_records['operation']=='出库']['合同号']:
    if contract in id_dict:
        id_dict[contract] += 1
    else:
        id_dict[contract] = 1

check_table = output_selection[['库区罐号','入库ID', '实际量']].merge(available_values.rename(columns={'实际量':'存量'}), on=['库区罐号','入库ID'])
if sum(check_table['实际量'] > check_table['存量']) > 0:
    st.error('出库数量大于存量！')
elif output_selection[['库区罐号', '合同号', '实际量']].isnull().values.any():
    st.error('库区罐号，合同号和实际量不能为空！')
else:
    if st.button('出库！'):
        if not output_selection.empty:
            for index, new_row in output_selection.iterrows():
                # 计算 出库ID
                if new_row['合同号'] == 'None':
                    st.error('合同号不能为空！')
                    continue
                if new_row['合同号'] in id_dict:
                    same_contract_count = id_dict[new_row['合同号']]
                    output_selection.loc[index, '出库ID'] = f"{new_row['合同号']}_{same_contract_count + 1}"
                    id_dict[new_row['合同号']] += 1
                else:
                    output_selection.loc[index, '出库ID'] = f"{new_row['合同号']}_1"
                    id_dict[new_row['合同号']] = 1

            # 保存数据
            output_selection['实际量'] = -output_selection['实际量']
            current_time = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            output_selection['operation_time'] = current_time
            
            # 更新operation_records.csv
            operation_records = pd.concat([operation_records, output_selection], ignore_index = True)
            operation_records.to_csv(os.path.join(file_dir, 'operation_records.csv'), encoding="GBK", index=False)
            
            # 显示成功信息
            st.success(f'新行已添加并更新至{os.path.join(file_dir, 'operation_records.csv')}！')

            # 显示更新后的数据
            st.subheader('更新的出库数据')
            st.write(output_selection)
        else:
            st.info('没有新的行需要更新。')
