import streamlit as st
import requests
import base64
import os
import urllib
import tempfile
import shutil
import json
from PIL import Image
from io import BytesIO
import imageio
import numpy as np

API_KEY1 = "U9G6xp4v74uIP48rcsZQitAY"
SECRET_KEY1 = "p57VMSmabFcTpIkZCkTSxVpLvZq2jZa8"

API_KEY2 = "7flOtk0XlLN7LNmUrSKHLYfI"
SECRET_KEY2 = "gKZ8rpIW8G5ylQ17YdkyL5xuMpIQfnst"

# 用户数据文件路径
USERS_FILE = 'users.json'


# 从文件中加载用户数据
def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# 将用户数据保存到文件中
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)


# 创建一个会话状态变量，用于存储当前登录用户的信息
session_state = st.session_state

# 初始化会话状态
if 'logged_in_user' not in st.session_state:
    st.session_state['logged_in_user'] = None


def upload_text(api_key, secret_key, text):
    url = "https://aip.baidubce.com/rest/2.0/solution/v1/text_censor/v2/user_defined"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "text": text,
        "type": "1",  # 1表示自定义敏感词，2表示自定义敏感句子
        "custom_dict": '{"敏感词1": "替换词1", "敏感词2": "替换词2"}'
    }
    params = {"access_token": get_access_token(api_key, secret_key)}

    # 调用文本检测API
    response = requests.post(url, data=data, params=params, headers=headers)
    result = response.json()
    return result


def get_file_content_as_base64(file_path, urlencoded=False):
    with open(file_path, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf8")
        if urlencoded:
            content = urllib.parse.quote_plus(content)
    return content


def get_access_token(api_key, secret_key):
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": api_key,
        "client_secret": secret_key
    }
    response = requests.post(url, params=params)
    result = response.json()

    if "error" in result:
        st.error(f"Error: {result['error']}")
        return None

    return result["access_token"]


def upload_image(image_path):
    url = "https://aip.baidubce.com/rest/2.0/solution/v1/img_censor/v2/user_defined?access_token=" + get_access_token(
        API_KEY2, SECRET_KEY2)

    image = get_file_content_as_base64(image_path, True)
    payload = "image=" + str(image)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }

    response = requests.post(url, headers=headers, data=payload)
    result = response.json()
    return result


def upload_video(video_path):
    frame_directory = "frames"
    if not os.path.exists(frame_directory):
        os.makedirs(frame_directory)

    # 打开视频文件
    reader = imageio.get_reader(video_path)
    fps = reader.get_meta_data()['fps']
    frame_interval = int(fps / 2)

    count = 0
    results = []

    for frame in reader:
        if count % frame_interval == 0:
            frame_path = os.path.join(frame_directory, f"frame{count:03d}.jpg")
            imageio.imwrite(frame_path, frame)
            frame_result = upload_image(frame_path)
            results.append(frame_result)
        count += 1

    reader.close()

    # 根据业务逻辑进一步处理检测结果

    shutil.rmtree(frame_directory)
    return results


# 登录页面
def login_page(registered_users):
    st.title("用户登录")
    st.write("### Welcome to the Bad Information Detection System")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    login_button = st.button("Log In")

    if login_button:
        if username in registered_users and registered_users[username] == password:
            st.session_state.logged_in_user = username
            st.success("Login successful!")
        else:
            st.error("Invalid username or password.")


# 注册页面
def register_page(registered_users):
    st.title("用户注册")
    st.write("### Welcome to the Bad Information Detection System")
    new_username = st.text_input("Choose a username", key="register_username")
    new_password = st.text_input("Set a password", type="password", key="register_password")
    register_button = st.button("Register")

    if register_button:
        if new_username in registered_users:
            st.error("This username is already taken. Please choose another one.")
        elif new_username and new_password:
            registered_users[new_username] = new_password
            save_users(registered_users)
            st.success(f"User {new_username} registered successfully!")
        else:
            st.error("Username and password cannot be empty.")


def main_page():
    st.title("不良信息检测系统")

    # 文本检测
    st.header("文本检测")
    text_input = st.text_area("输入文本:")
    if st.button("检测文本"):
        result = upload_text(API_KEY1, SECRET_KEY1, text_input)
        if result.get("conclusion") == "不合规":
            st.error("检测为不良文本!")
        else:
            st.success("文本正常")
        st.write(result)

    # 图像检测
    st.header("图像检测")
    uploaded_image = st.file_uploader("上传图像", type=["jpg", "png", "jpeg"])
    display_image = st.checkbox("显示图像")
    if uploaded_image is not None:
        # 创建一个临时文件夹
        temp_folder = tempfile.mkdtemp()
        # 获取上传的文件名
        image_filename = os.path.join(temp_folder, uploaded_image.name)
        # 将上传的图片数据写入临时文件
        with open(image_filename, "wb") as f:
            f.write(uploaded_image.read())

        # 显示上传的图像     #这里也要加一个按钮看是否要显示
        # st.image(Image.open(image_filename), caption="Uploaded Image", use_column_width=True)

        if uploaded_image is not None and display_image:
            # 显示上传的图像
            st.image(Image.open(image_filename), caption="Uploaded Image", use_column_width=True)

        st.markdown("### 图像检测结果:")
        result = upload_image(image_filename)
        if result.get("conclusion") == "不合规":
            st.error("检测为不良图像!")
        else:
            st.success("图像正常")
        st.write(result)
        # 清理临时文件夹
        shutil.rmtree(temp_folder)

    # 视频检测
    st.header("视频检测")
    uploaded_video = st.file_uploader("上传视频", type=["mp4"])
    display_video = st.checkbox("显示视频")
    if uploaded_video is not None:
        # 创建一个临时文件夹
        temp_folder = tempfile.mkdtemp()
        # 获取上传的文件名
        video_filename = os.path.join(temp_folder, uploaded_video.name)
        # 将上传的视频数据写入临时文件
        with open(video_filename, "wb") as f:
            f.write(uploaded_video.read())

        # 显示上传的视频  #这里要看加一个按钮是否要显示
        if display_video:
            video_file = open(video_filename, "rb").read()
            video_bytes = BytesIO(video_file)
            st.video(video_bytes, format="video/mp4", start_time=0)

        st.markdown("### 视频检测结果:")
        # 调用视频检测函数
        results = upload_video(video_filename)

        # 检查每一帧的检测结果
        for count, result in enumerate(results):
            if result.get("conclusion") == "不合规":
                st.error("视频中检测到不良图像!")
                st.write(result)
                break
            else:
                st.success("视频正常")

        # 清理临时文件夹
        shutil.rmtree(temp_folder)

# Rest of the code remains the same...

# 切换页面
def switch_page(registered_users):
    if st.session_state.logged_in_user:
        main_page()
    else:
        selected_page = st.sidebar.selectbox("Select Page", ["Login", "Register"])
        if selected_page == "Login":
            login_page(registered_users)
        else:
            register_page(registered_users)

# 加载用户数据
registered_users = load_users()

# 根据用户的选择显示页面
switch_page(registered_users)
