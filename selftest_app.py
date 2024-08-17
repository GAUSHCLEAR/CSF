import io
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

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

angle_to_str_dict={
        0:'↕',45:'⤡',-45:'⤢',-90:'↔'}
def check_answer(answer,angle,angle_to_str={
        0:'↕',45:'⤡',-45:'⤢',-90:'↔'}):
    if angle_to_str[angle]==answer:
        return 1
    else:
        return 0
            
with st.sidebar:
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
        text = '●'
        
        setting_done_submit = st.form_submit_button("提交")
    if setting_done_submit:
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
            'text': text
        }

max_test_num = 10
if 'logCS' not in st.session_state:
    st.session_state.logCS = (logCS_min+logCS_max)/2
if 'parameters' in st.session_state:
    T_idx = 0 
    # for T_idx in range(len(T_list_in_pix)):
    chooseID=np.random.randint(T_idx,len(T_list_in_pix),2)
    T = T_list_in_pix[T_idx]
    T_in_degree = T_list_in_cycle_per_deg[T_idx]

    if 'x_list' not in st.session_state:
        st.session_state.x_list=[logCS_min,logCS_max]
    if 'y_list' not in st.session_state:
        st.session_state.y_list=[1,0]

    # for i in range(max_test_num):
    angle = np.random.randint(-90, 89) // 45 * 45
    print(f"空间频率：{T:.2f}")
    # print(f"对比度：{st.session_state.logCS:.2f}")
    print(f"角度：{angle}°")
    show_csf_image(size, dpi, T, 10**(-st.session_state.logCS), angle, avg_value, text, blur_core, blur_radius,st)

    col1,col2,col3,col4 = st.columns(4)
    answer_vertical = col1.button('↕')
    answer_left = col2.button('⤡')
    answer_right = col3.button('⤢')
    answer_horizontal = col4.button('↔')

    current_x=st.session_state.logCS
    
    def next_test(angle,direction):
        current_y = 1 if angle_to_str_dict[angle] ==direction else 0
        x_threshold,ci = estimate_contrast_sensitivity(st.session_state.x_list,st.session_state.y_list,logCS_min,logCS_max)
        st.session_state.x_list.append(current_x)
        st.session_state.y_list.append(current_y)
        if x_threshold is not None:
            st.session_state.logCS = x_threshold
            

    if answer_vertical :
        next_test(angle,'↕')

    elif answer_left :
        next_test(angle,'⤡')

    elif answer_right :
        next_test(angle,'⤢')

    elif answer_horizontal :
        next_test(angle,'↔')

    else:
        pass 
    st.write(st.session_state.logCS)
    st.write(f"x_list: {st.session_state.x_list}, y_list: {st.session_state.y_list}")
    # st.session_state.x_list.append(current_x)
    # st.session_state.y_list.append(current_y)
    # st.write(f"x_list: {st.session_state.x_list}, y_list: {st.session_state.y_list}")
