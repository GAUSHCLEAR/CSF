import numpy as np
import cv2
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from scipy.optimize import curve_fit


def strip_image(target_size, contrast, T, angle, avg_value):
    # 计算初始图像大小
    size = target_size *(np.sin(np.abs(angle/180*np.pi))+np.cos(np.abs(angle/180*np.pi)))
    size = int(size)
    # 生成灰度值数组
    x = np.arange(size)
    gray_values = avg_value + np.cos(2*np.pi*x/T)*contrast*avg_value
    # 创建初始图像矩阵
    image = np.tile(gray_values, (size, 1))
    # 旋转图像
    center = (size // 2, size // 2)
    scale = 1.0
    # 获取旋转矩阵
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, scale)
    # 旋转图像
    rotated_image = cv2.warpAffine(image, rotation_matrix, (size, size))
    # 裁剪图像
    start_x = (rotated_image.shape[1] - target_size) // 2
    start_y = (rotated_image.shape[0] - target_size) // 2
    
    cropped_image = rotated_image[start_y:start_y + target_size, start_x:start_x + target_size]
    background = np.ones((target_size, target_size)) * 128
    return cropped_image, background

def text_image(size, text, font_size,
               blur_core=51, blur_radius=25):
    # 创建黑色背景图像
    image = Image.new('L', (size, size), 0)

    # 字符串和字体设置
    font_path = "NotoSansSC-ExtraBold.ttf"
    # font_path = 'digital-7.ttf'
    font = ImageFont.truetype(font_path, font_size)


    # 获取文本尺寸
    draw = ImageDraw.Draw(image)
    
    x = size // 2
    y = int(size // 2 * 0.9)

    # 绘制文本
    draw.text((x, y), text, font=font, fill=255, anchor='mm')

    image = np.array(image)

    # 对图像应用高斯模糊，模糊半径为10
    blurred_image = cv2.GaussianBlur(image, (blur_core, blur_core), blur_radius)

    return blurred_image/blurred_image.max()

def generate_csf_image(size,T,contrast,angle,avg_value,text,blur_core,blur_radius):
    front_image, background_image=strip_image(
        size, 
        contrast=contrast, 
        T=T, 
        angle=angle, 
        avg_value=avg_value)
    text_img = text_image(size, text, font_size=int(size*0.95),
        blur_core=blur_core, blur_radius=blur_radius)
    image = front_image*text_img+background_image*(1-text_img)
    # print(f"size: {size}, T: {T}, contrast: {contrast:.2f}, angle: {angle}")
    return image

def calculate_T_in_pix(spatial_frequency,distance_in_meter,dpi):
    # mm_per_degree = 1000 * distance_in_meter * np.tan(2 * np.pi / 360)
    # T_in_mm = (1 / spatial_frequency) * mm_per_degree
    # T_in_pixel = T_in_mm * dpi / 25.4
    theta = np.deg2rad(1/spatial_frequency)
    T_in_mm = 1000 * distance_in_meter * np.tan(theta)
    T_in_pixel = T_in_mm * dpi / 25.4
    return int(T_in_pixel)
def calculate_size_in_pix(size_in_mm,dpi):
    size_in_pixel = size_in_mm * dpi / 25.4
    return int(size_in_pixel)

def estimate_contrast_sensitivity(x_values, cs_values,x_low_bound=-0.1,x_high_bound=10):
    """
    估计CS(x)=0.5时的x值。
    
    参数:
    x_values: 输入的x值列表或数组
    cs_values: 对应的CS值列表或数组
    
    返回:
    estimated_x: CS(x)=0.5时估计的x值
    """
    
    # 定义sigmoid函数
    def sigmoid(x, x0, k):
        return 1 / (1 + np.exp(-k*(x-x0)))
    
    # 将输入转换为numpy数组
    # x = np.array(x_values)
    # y = np.array(cs_values)

    x=np.append(x_values,[-0.5,-0.4,-0.3,-0.2,-0.1,0,2.5,2.6,2.7,2.8,2.9,3])
    y=np.append(cs_values,[1,1,1,1,1,1, 0,0,0,0,0,0])
    if len(x)<3 or len(y)<3:
        # print("数据点太少，无法拟合。")
        return None,None 

    # 初始参数猜测
    p0 = [np.median(x), 1]
    
    try:
        # 使用curve_fit进行拟合
        popt, _ = curve_fit(sigmoid, x, y, p0, method='lm', maxfev=10000)
    except:
        # print("拟合失败，请检查输入数据。")
        return None,None 
    
    # 解析拟合参数
    x0, k = popt
    
    # 计算CS(x)=0.5时的x值
    estimated_x = x0 - np.log(1/0.5 - 1)/k
    CI = np.abs(np.log(1/0.05 -1)/k)
    if np.isnan(estimated_x) or estimated_x < x_low_bound or estimated_x > x_high_bound:
        # print('估计的x值超出范围。')
        return None,None 
    return estimated_x,CI 