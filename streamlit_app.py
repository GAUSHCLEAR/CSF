import io
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import pandas as pd
import time 
import warnings
warnings.filterwarnings("ignore")

from data_processing import (
    generate_csf_image,
    calculate_size_in_pix,
    calculate_T_in_pix,
    estimate_contrast_sensitivity
    )
from gui_processing import (
    set_dpi_gui,set_distance_gui,set_image_gui,
    set_spacial_frequency_gui,
    set_contrast_gui,
    show_csf_image)

text_choose_from = ['2', '3', '4', '6','9']
angle_choose_from = [-60, -45, -30, 30, 45, 60]

st.set_page_config(page_title="视觉敏感度测试", page_icon="😵‍💫", layout="wide", initial_sidebar_state='expanded')

setting_gui=st.container()

if 'expand_state' not in st.session_state:
    st.session_state['expand_state']=True

with setting_gui.expander("设置参数", expanded=st.session_state['expand_state']):
    with st.form(key="setting"):
        setting_dpi = st.container()
        setting_distance = st.container()
        setting_image = st.container()
        setting_spacial_frequency = st.container()
        setting_contrast = st.container()
        dpi = set_dpi_gui(setting_dpi)
        distance_in_meter = set_distance_gui(setting_distance)
        size,avg_value,blur_core,blur_radius=set_image_gui(setting_image,dpi)    
        T_list_in_pix,T_list_in_cycle_per_deg=set_spacial_frequency_gui(setting_spacial_frequency,distance_in_meter,dpi)    
        logCS_min,logCS_max,logCS_list,contract_list=set_contrast_gui(setting_contrast)
        # text = '●'
        
        setting_done_submit = st.form_submit_button("开始测试")
    if setting_done_submit:
        st.session_state['expand_state']=False 

        text_list=[[text_choose_from[np.random.randint(0, len(text_choose_from))] for i in range(len(T_list_in_pix))]
                     for j in range(len(logCS_list))]
        angle_list = [
            [angle_choose_from[np.random.randint(0, len(angle_choose_from))]  for i in range(len(T_list_in_pix))]
            for j in range(len(logCS_list))
        ]
             
        st.session_state['parameters'] = {
            'dpi': dpi,
            'distance_in_meter': distance_in_meter,
            'size': size,
            'avg_value': avg_value,
            'blur_core': blur_core,
            'blur_radius': blur_radius,
            'T_list_in_pix': T_list_in_pix,
            'T_list_in_cycle_per_deg': T_list_in_cycle_per_deg,
            'logCS_min': logCS_min,
            'logCS_max': logCS_max,
            'logCS_list': logCS_list,
            'contract_list': contract_list,
            'text_list': text_list,
            'angle_list': angle_list
            # 'text_list": str(np.random.randint(0, 10))
        }
        st.session_state['result'] = pd.DataFrame(
            columns=['spacial_frequency', 'CSF(logCS)', 'std_err'])
        

if 'parameters' in st.session_state:
    text_string_list=",".join(text_choose_from)
    st.markdown(f"""
                ## 请站到{st.session_state.parameters['distance_in_meter']:.2f}米远处       
                ## 请输入图片中的数字
                ## 可选（{text_string_list}）
                ## 如果看不清输入0
                ## 可以使用tab键切换至下一个输入框 """)
    
    for T_idx in range(len(st.session_state.parameters['T_list_in_pix'])):
        for logCS_idx in range(len(st.session_state.parameters['logCS_list'])): 
            T = st.session_state.parameters['T_list_in_pix'][T_idx]
            T_in_degree = st.session_state.parameters['T_list_in_cycle_per_deg'][T_idx]
            contrast = st.session_state.parameters['contract_list'][logCS_idx]
            logCS=st.session_state.parameters['logCS_list'][logCS_idx]
            angle = st.session_state.parameters['angle_list'][logCS_idx][T_idx]
            text = st.session_state.parameters['text_list'][logCS_idx][T_idx]
            
            show_block= st.container(border=True)
            col1, col2 = show_block.columns([4, 1])

            show_csf_image(
                size, dpi, T, contrast, angle, avg_value, text, blur_core, blur_radius,col1)
            col2.markdown(f"* 空间频率：{T_in_degree:.2f} CPD \n* 对比度logCS：{logCS:.3f}")
            answer_text=col2.text_input(
                '输入答案', 
                value='0',
                max_chars=1,
                key=f'{T_idx}_{logCS_idx}')
            
            st.session_state[f'y_{T_idx}_{logCS_idx}']=1 if (answer_text == text) else 0
            answer_check=(st.session_state[f'y_{T_idx}_{logCS_idx}']==1)
            answer_color='green' if answer_check else 'red'
            answer_string='正确' if answer_check else '错误'
            col2.markdown(f"结果： <font color='{answer_color}'>{answer_string}</font>",unsafe_allow_html=True)
        x_values=st.session_state.parameters['logCS_list']
        y_values=[st.session_state[f'y_{T_idx}_{logCS_idx}'] for logCS_idx in range(len(x_values))]
        x_values=np.append(x_values,[0,0.1,3])
        y_values=np.append(y_values,[1,1,0])
        estimated_x, ci = estimate_contrast_sensitivity(x_values, y_values)
        if estimated_x is not None:
            result_str=f"空间频率：{T_in_degree:.2f} CPD, 对比敏感度logCS：{estimated_x:.3f} ± {ci:.3f}"
        else:
            result_str=f"空间频率：{T_in_degree:.2f} CPD, 对比敏感度logCS：无法计算"
        st.markdown(result_str)
    ## calculate the result
    result_df=pd.DataFrame(
            columns=['spacial_frequency', 'CSF(logCS)', 'std_err'])
    for T_idx in range(len(st.session_state.parameters['T_list_in_pix'])):
        T_in_degree = st.session_state.parameters['T_list_in_cycle_per_deg'][T_idx]

        x_values=st.session_state.parameters['logCS_list']
        y_values=[st.session_state[f'y_{T_idx}_{logCS_idx}'] for logCS_idx in range(len(x_values))]
        x_values=np.array(x_values)
        y_values=np.array(y_values)
        estimated_x, ci = estimate_contrast_sensitivity(x_values, y_values)
        x_values=st.session_state.parameters['logCS_list']
        y_values=[st.session_state[f'y_{T_idx}_{logCS_idx}'] for logCS_idx in range(len(x_values))]
        x_values=np.append(x_values,[0,0.1,3])
        y_values=np.append(y_values,[1,1,0])
        estimated_x, ci = estimate_contrast_sensitivity(x_values, y_values)
        if estimated_x is not None:
            result_df.loc[len(result_df)]=[
                T_in_degree, estimated_x, ci]
        else:
            result_df.loc[len(result_df)]=[
                T_in_degree, np.nan, np.nan]
    st.markdown("## 结果")
    st.dataframe(result_df)
    time_stamp = time.strftime("%Y%m%d-%H%M")
    st.download_button(
        label="下载结果",
        data=result_df.to_csv(index=False).encode(),
        file_name=f"CSF_{time_stamp}.csv",
        mime="text/csv",
    )