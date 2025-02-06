import os
import pandas as pd
import streamlit as st

# 文件路径
file_dir = st.text_input('请输入数据文件夹的路径：（读取文件夹下operation_records.csv）', value='petrolstock')  # 请将此路径替换为你的CSV文件路径

# Display the title of the app
st.title('混兑操作')

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
selected_IDs = st.multiselect(f'选择用于混兑的ID:', available_IDs)

# 选择转出的ID及数量
st.write('选择用于混兑的条目（数量请填写正数）：')
output_df = pd.DataFrame(columns=operation_records.columns)

pre_defined_data = available_values.loc[available_values['入库ID'].isin(selected_IDs), ['品名','库区','罐号','库区罐号','入库ID', '实际量']]
output_df = pd.concat([output_df, pre_defined_data], ignore_index=True)

output_df['operation'] = '用于混兑'

output_selection = st.data_editor(output_df, height=200, num_rows="dynamic", disabled=output_df.columns[-4:])

if len(output_selection) <= 1:
    st.error('请至少选择两个条目！')
if output_selection[['库区罐号', '实际量', '入库ID']].isnull().values.any():
    st.error('库区罐号、实际量、入库ID不能为空！')
check_table = output_selection[['库区罐号','入库ID', '实际量']].merge(available_values.rename(columns={'实际量':'存量'}), on=['库区罐号','入库ID'])
if sum(check_table['实际量'] > check_table['存量']) > 0:
    st.error('出库数量大于存量！')

st.write(f'用于混兑的总数：{sum(output_selection["实际量"]):.3f}')
st.write('选择混兑至：')

# 混兑data frame, with only one row, 实际量 default value is round(sum(output_selection["实际量"]), 3), 入库ID default value is '混兑'
n_mix = len(operation_records.loc[operation_records['operation'] == '混兑入库'])

mix_df = pd.DataFrame(columns=operation_records.columns)

new_entry = {col: None for col in mix_df.columns}
new_entry.update({
    '入库ID': f'混兑_{n_mix+1}',
    '实际量': round(sum(output_selection["实际量"]), 3),
    'operation': '混兑入库'
})
mix_df.loc[len(mix_df)] = new_entry

mixation_selection = st.data_editor(mix_df, height=100, disabled=mix_df.columns[-3:])

if mixation_selection[['库区罐号', '实际量', '入库ID']].isnull().values.any():
    st.error('库区罐号、实际量、入库ID不能为空！')

output_selection['实际量'] = -output_selection['实际量']
output_selection.loc[:, '出库ID'] = mixation_selection['入库ID'].values[0]

if st.button('生成混兑表'):
    mix_table = pd.concat([output_selection, mixation_selection], ignore_index=True)
    
    current_time = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    mix_table['operation_time'] = current_time
    st.write('转移表：')
    st.session_state.final_table = st.data_editor(mix_table, height=400)

if st.button('确认混兑'):
    if 'final_table' not in st.session_state:
        st.error("请先生成混兑表")
    else:
        final_table = st.session_state.final_table
        # 更新operation_records.csv
        operation_records = pd.concat([operation_records, final_table], ignore_index = True)
        operation_records.to_csv(os.path.join(file_dir, 'operation_records.csv'), encoding="GBK", index=False)
        
        # 显示成功信息
        st.success(f'新行已添加并更新至{os.path.join(file_dir, 'operation_records.csv')}！')