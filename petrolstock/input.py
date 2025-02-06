import os
import re
import pandas as pd
import streamlit as st

# 文件路径
file_dir = st.text_input('请输入数据文件夹的路径：（读取文件夹下inputs.csv及operation_records.csv）', value='petrolstock')  # 请将此路径替换为你的CSV文件路径

st.title('入库操作')
# 加载数据
input_storage = pd.read_csv(os.path.join(file_dir, 'inputs.csv'), encoding="GBK")

id_dict = {}
for contract in input_storage['合同号']:
    if contract in id_dict:
        id_dict[contract] += 1
    else:
        id_dict[contract] = 1

# 显示现有数据
st.subheader('已有入库数据')
st.dataframe(input_storage)

st.subheader('新增入库')
new_rows = st.data_editor(pd.DataFrame(columns=input_storage.columns), height=200, num_rows="dynamic", disabled=input_storage.columns[-1:])

if new_rows[['库区罐号', '合同号', '实际量']].isnull().values.any():
    st.error('库区罐号，合同号和实际量不能为空！')
else:
    if st.button('入库！'):
        if not new_rows.empty:
            for index, new_row in new_rows.iterrows():
                # 计算 入库ID
                if new_row['合同号'] == 'None':
                    st.error('合同号不能为空！')
                    continue
                if new_row['合同号'] in id_dict:
                    same_contract_count = id_dict[new_row['合同号']]
                    new_rows.loc[index, '入库ID'] = f"{new_row['合同号']}_{same_contract_count + 1}"
                    id_dict[new_row['合同号']] += 1
                else:
                    new_rows.loc[index, '入库ID'] = f"{new_row['合同号']}_1"
                    id_dict[new_row['合同号']] = 1

            # 保存数据
            current_time = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            # outpath = re.sub(r"(.*inputs)(_?\d+)?\.csv", r"\1" + f'_{current_time}.csv', filepath)
            outpath = os.path.join(file_dir, 'inputs.csv')
            
            data_input = pd.concat([input_storage, new_rows], ignore_index = True)
            data_input.to_csv(outpath, index=False, encoding="GBK")

            # 显示成功信息
            st.success(f'新行已添加并更新至{outpath}！')
            
            # 更新operation_records.csv
            operation_records = pd.read_csv(os.path.join(file_dir, 'operation_records.csv'), encoding="GBK")
            new_rows['出库ID'] = pd.NA
            new_rows['operation'] = '入库'
            new_rows['operation_time'] = current_time
            operation_records = pd.concat([operation_records, new_rows], ignore_index = True)
            operation_records.to_csv(os.path.join(file_dir, 'operation_records.csv'), encoding="GBK", index=False)

            # 显示更新后的数据
            st.subheader('更新后的数据')
            st.write(data_input)
        else:
            st.info('没有新的行需要更新。')