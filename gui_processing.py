import streamlit as st
import io
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from data_processing import (
    generate_csf_image,
    calculate_size_in_pix,
    calculate_T_in_pix,
    estimate_contrast_sensitivity
    )

def set_dpi_gui(container):
    container.markdown("## 1.标定DPI")
    container.info('请使用直尺测量下方的蓝色测量线长度，然后输入实际长度。你可以调整像素数和蓝色测量线长度来标定屏幕实际的分辨率。')
    px_num=container.number_input('像素数', min_value=100, max_value=500, value=130, step=1)
    line_length=container.number_input('直尺测量线长度（mm）', min_value=1.0, max_value=100.0, value=50.0, step=0.1)
    container.markdown("### ↓测量下面这根蓝线↓")
    container.markdown(
        f"""
        <div style="width: {px_num}px; height: 10px; background-color: blue; margin: 10px 0;"></div>
        """,
        unsafe_allow_html=True
    )
    dpi = px_num / line_length * 25.4
    return dpi

def set_distance_gui(container):
    container.markdown("## 2.设置测量位置")
    distance_in_meter = container.number_input('距离（米）', min_value=0.1, max_value=10.0, value=5.0, step=0.1)  
    return distance_in_meter

def set_image_gui(container,dpi):
    container.markdown("## 3.设置图像参数")
    image_size = container.number_input('图像大小（mm）', min_value=100, max_value=1000, value=150, step=1)
    size=calculate_size_in_pix(image_size, dpi)
    avg_value = 127
    blur_core=size//20*2+1
    blur_radius = blur_core //2
    return size,avg_value,blur_core,blur_radius

def set_spacial_frequency_gui(container,distance_in_meter,dpi):
        container.markdown("## 4.设置空间频率")
        container.markdown("注意过高的空间频率或者过近的测量距离可能导致图像无法显示。")
        T_list_in_cycle_per_deg_text = container.text_input('空间频率（周期/度）', '6,12,18,24,30')
        T_list_in_cycle_per_deg = [float(T) for T in T_list_in_cycle_per_deg_text.split(',')]
        T_list_in_pix = [calculate_T_in_pix(T, distance_in_meter, dpi) for T in T_list_in_cycle_per_deg]
        # st.write(T_list_in_pix)
        # 选择出T_list_in_pix中>1的值，并提取T_list_in_cycle_per_deg中对应的值
        T_list_in_pix = [T for T in T_list_in_pix if T>1]
        
        # 选择出 T_list_in_pix 中 > 1 的值，并提取 T_list_in_cycle_per_deg 中对应的值
        filtered_T_list_in_pix = [T for T in T_list_in_pix if T > 1]
        filtered_T_list_in_cycle_per_deg = [T_list_in_cycle_per_deg[i] for i in range(len(T_list_in_pix)) if T_list_in_pix[i] > 1]
        container.markdown(f"可用的空间频率：{filtered_T_list_in_cycle_per_deg} 周期/度")  
        T_list_in_pix=filtered_T_list_in_pix
        T_list_in_cycle_per_deg=filtered_T_list_in_cycle_per_deg
        return T_list_in_pix,T_list_in_cycle_per_deg

    # 设置对比度列表
def set_contrast_gui(container):
    container.markdown("## 5.设置对比度")
    logCS_min = container.number_input('最小对比度（logCS）', min_value=0.0, max_value=2.0, value=0.0, step=0.1)
    logCS_max = container.number_input('最大对比度（logCS）', min_value=0.0, max_value=2.5, value=2.4, step=0.1)
    N_logCS = container.number_input('对比度数量', min_value=1, max_value=20 , value=10, step=1)
    logCS_list=np.linspace(logCS_min,logCS_max,N_logCS)
    contract_list = 10**(-logCS_list)
    return logCS_min,logCS_max,logCS_list,contract_list

def prepare_csf_image(size, dpi,
    T, contrast, angle, avg_value, text, blur_core, blur_radius):
    csf_image = generate_csf_image(size, T, contrast, angle, avg_value, text, blur_core, blur_radius)


    fig, ax = plt.subplots(figsize=(csf_image.shape[1] / dpi, csf_image.shape[0] / dpi), dpi=dpi)
    ax.imshow(csf_image, cmap='gray', vmin=0, vmax=255)
    ax.axis('off')

    # 保存图像到内存
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    buf.seek(0)
    image = Image.open(buf)
    image = image.resize((csf_image.shape[1], csf_image.shape[0]), Image.LANCZOS)
    return image 

def show_csf_image(size, dpi,
    T, contrast, angle, avg_value, text, blur_core, blur_radius,container):
    # csf_image = generate_csf_image(size, T, contrast, angle, avg_value, text, blur_core, blur_radius)


    # fig, ax = plt.subplots(figsize=(csf_image.shape[1] / dpi, csf_image.shape[0] / dpi), dpi=dpi)
    # ax.imshow(csf_image, cmap='gray', vmin=0, vmax=255)
    # ax.axis('off')

    # # 保存图像到内存
    # buf = io.BytesIO()
    # fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    # buf.seek(0)
    # image = Image.open(buf)
    # image = image.resize((csf_image.shape[1], csf_image.shape[0]), Image.LANCZOS)
    image=prepare_csf_image(size, dpi, T, contrast, angle, avg_value, text, blur_core, blur_radius)
    container.image(image, use_column_width=False) 