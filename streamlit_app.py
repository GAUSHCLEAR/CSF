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


with st.sidebar:
    st.markdown("## 1.标定DPI")
    st.info('请使用直尺测量下方的蓝色测量线长度，然后输入实际长度。你可以调整像素数和蓝色测量线长度来标定屏幕实际的分辨率。')
    px_num=st.number_input('像素数', min_value=100, max_value=500, value=130, step=1)
    line_length=st.number_input('直尺测量线长度（mm）', min_value=1.0, max_value=100.0, value=50.0, step=0.1)
    st.markdown("### ↓测量下面这根蓝线↓")
    st.markdown(
        f"""
        <div style="width: {px_num}px; height: 10px; background-color: blue; margin: 10px 0;"></div>
        """,
        unsafe_allow_html=True
    )
    dpi = px_num / line_length * 25.4
    st.markdown("## 2.设置测量位置")
    distance_in_meter = st.number_input('距离（米）', min_value=0.1, max_value=10.0, value=5.0, step=0.1)  
    
    st.markdown("## 3.设置图像参数")
    image_size = st.number_input('图像大小（mm）', min_value=100, max_value=1000, value=150, step=1)
    size=calculate_size_in_pix(image_size, dpi)
    avg_value = 127
    blur_core=size//20*2+1
    blur_radius = blur_core //2

    st.markdown(f"图像大小：{size}x{size}像素, DPI: {dpi:.2f}, 距离：{distance_in_meter}米, blur_core: {blur_core}, blur_radius: {blur_radius}")

    # 设置空间频率列表
    st.markdown("## 4.设置空间频率")
    st.markdown("注意过高的空间频率或者过近的测量距离可能导致图像无法显示。")
    T_list_in_cycle_per_deg_text = st.text_input('空间频率（周期/度）', '3,6,12,18,24')
    T_list_in_cycle_per_deg = [float(T) for T in T_list_in_cycle_per_deg_text.split(',')]
    T_list_in_pix = [calculate_T_in_pix(T, distance_in_meter, dpi) for T in T_list_in_cycle_per_deg]
    # st.write(T_list_in_pix)
    # 选择出T_list_in_pix中>1的值，并提取T_list_in_cycle_per_deg中对应的值
    T_list_in_pix = [T for T in T_list_in_pix if T>1]
    
    # 选择出 T_list_in_pix 中 > 1 的值，并提取 T_list_in_cycle_per_deg 中对应的值
    filtered_T_list_in_pix = [T for T in T_list_in_pix if T > 1]
    filtered_T_list_in_cycle_per_deg = [T_list_in_cycle_per_deg[i] for i in range(len(T_list_in_pix)) if T_list_in_pix[i] > 1]
    T_list_in_pix=filtered_T_list_in_pix
    T_list_in_cycle_per_deg=filtered_T_list_in_cycle_per_deg


    # 设置对比度列表
    st.markdown("## 5.设置对比度")
    logCS_min = st.number_input('最小对比度（logCS）', min_value=0.0, max_value=2.0, value=1.0, step=0.1)
    logCS_max = st.number_input('最大对比度（logCS）', min_value=0.0, max_value=2.5, value=2.4, step=0.1)
    N_logCS = st.number_input('对比度数量', min_value=1, max_value=20 , value=12, step=1)
    logCS_list=np.linspace(logCS_min,logCS_max,N_logCS)
    contract_list = 10**(-logCS_list)

    st.markdown("## 6.开始测量")
    st.markdown("请选择一个空间频率和对比度")
    cols = st.columns([1]*len(T_list_in_cycle_per_deg))
    for i in range(len(T_list_in_cycle_per_deg)):
        cols[i].markdown(f'### {int(T_list_in_cycle_per_deg[i])} CPD')
        for j in range(N_logCS):
            cols[i].button(f'{logCS_list[j]:.2f}', key=f'{i}_{j}')
            if st.session_state[f'{i}_{j}']:
                st.session_state['chooseID']=(i,j)

    angle = np.random.randint(-90, 89) // 45 * 45

if 'chooseID' in st.session_state :
    chooseID=st.session_state['chooseID']
    text = '●'
    # T = T_list[chooseID]
    T = T_list_in_pix[chooseID[0]]
    # contrast = contract_list[chooseID]
    contrast = contract_list[chooseID[1]]
    # angle = angle_list[chooseID]
    T_in_degree = T_list_in_cycle_per_deg[chooseID[0]]
    logCS = logCS_list[chooseID[1]]

    # st.markdown(f"空间频率：{T:.2f}, 对比度：{contrast:.2f}, 角度：{angle}°")
    
    csf_image = generate_csf_image(size, T, contrast, angle, avg_value, text, blur_core, blur_radius)

    fig, ax = plt.subplots(figsize=(csf_image.shape[1] / dpi, csf_image.shape[0] / dpi), dpi=dpi)
    ax.imshow(csf_image, cmap='gray', vmin=0, vmax=255)
    ax.axis('off')
    # st.session_state['chooseID']=None

    # 保存图像到内存
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    buf.seek(0)
    image = Image.open(buf)
    image = image.resize((csf_image.shape[1], csf_image.shape[0]), Image.LANCZOS)
    angle_to_str_dict={
        0:'↕',45:'⤡',-45:'⤢',-90:'↔'}

    st.image(image, use_column_width=False) 
    col1,col2,col3,col4=st.columns([1,1,1,1])
    answer_right = col1.button('正确')
    answer_wrong = col2.button('错误')
    answer_answer= col3.markdown(angle_to_str_dict[angle])
    answer_clear = col4.button('清空')

    if 'answer_vector' not in st.session_state:
        st.session_state['answer_vector'] = []
    if answer_right:
        answer_vec=[T_in_degree,logCS,1]
        st.session_state['answer_vector'].append(answer_vec)
    if answer_wrong:
        answer_vec=[T_in_degree,logCS,0]
        st.session_state['answer_vector'].append(answer_vec)
    if answer_clear:
        st.session_state['answer_vector'] = []
    if len(st.session_state['answer_vector'])>0:
        answer_dict={}
        answer_string = "|".join(str(x) for x in T_list_in_cycle_per_deg)
        answer_string = "|"+answer_string+"|"+'\n'
        answer_string += "|---"*len(T_list_in_cycle_per_deg)+"|"+'\n'
        for t in T_list_in_cycle_per_deg:
            t_x = [x[1] for x in st.session_state['answer_vector'] if x[0]==t]
            t_logCS = [x[2] for x in st.session_state['answer_vector'] if x[0]==t]
            t_x_threshold, CI  = estimate_contrast_sensitivity(
                x_values=t_x,
                cs_values=t_logCS,
                x_low_bound=logCS_min,
                x_high_bound=logCS_max)
            answer_dict[t]=t_x_threshold
            if t_x_threshold is not None:
                answer_string+=f"|{t_x_threshold:.3f}±{CI:.3f}"
            else:
                answer_string+="|"
        st.markdown(answer_string)
        st.markdown(st.session_state['answer_vector'])
