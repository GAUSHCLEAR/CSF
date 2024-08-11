import numpy as np
import cv2
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

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
    font = ImageFont.truetype(font_path, font_size)


    # 获取文本尺寸
    draw = ImageDraw.Draw(image)
    
    x = size // 2
    y = int(size // 2 )

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
    text_img = text_image(size, text, font_size=int(size*0.9),
        blur_core=blur_core, blur_radius=blur_radius)
    image = front_image*text_img+background_image*(1-text_img)
    print(f"size: {size}, T: {T}, contrast: {contrast:.2f}, angle: {angle}")
    return image