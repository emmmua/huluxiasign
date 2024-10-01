import hashlib
import json
import re
import smtplib
import time
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests


def get_response(url, method='GET', headers=None, data=None):
    """
    通用的请求函数，用于发送 GET 或 POST 请求。

    :param url: 请求的 URL 地址
    :param method: 请求的方法（GET 或 POST）
    :param headers: 请求头，默认为 None
    :param data: POST 请求时的数据，默认为 None
    :return: 响应的文本内容，如果请求失败返回 None
    """
    if headers is None:
        headers = {}

    try:
        # 根据请求方法发送请求
        if method.upper() == 'POST':
            response = requests.post(url, headers=headers, data=data)
        else:
            response = requests.get(url, headers=headers)

        # 如果响应状态码不是 200，会引发 HTTPError
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"请求错误: {e}")
        return None


def get_categoryid_list(url):
    """
    获取分类 ID 列表。

    :param url: 分类列表的 URL
    :return: 分类 ID 列表的响应内容
    """
    headers = {
        "Host": "floor.huluxia.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    }
    return get_response(url, headers=headers)


def send_sign_post(url, post_data):
    """
    发送签到请求的 POST 请求。

    :param url: 签到的 URL
    :param post_data: 要发送的 POST 数据
    :return: 签到响应的文本内容
    """
    headers = {
        "Connection": "close",
        "Accept-Encoding": "gzip",
        "Host": "floor.huluxia.com",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "okhttp/3.8.1"
    }
    return get_response(url, method='POST', headers=headers, data=post_data.encode('utf-8'))


def get_login_sign(account, password):
    """
    获取登录时的签名并进行登录。

    :param account: 用户名（手机号）
    :param password: 密码
    :return: 登录成功后返回的登录密钥，失败返回 None
    """
    # 对密码进行 MD5 加密
    password_encode = hashlib.md5(password.encode()).hexdigest()
    # 构造用于生成签名的字符串
    encode_text = f"account{account}device_code[d]7f659db3-9ffb-41ec-80c3-fbf0db5691a9password{password_encode}voice_codefa1c28a5b62e79c3e63d9030b6142e4b"
    # 计算账号签名
    account_sign = hashlib.md5(encode_text.encode()).hexdigest().upper()

    # 登录请求的 URL
    url = "http://floor.huluxia.com/account/login/ANDROID/4.1.8?platform=2&gkey=000000&app_version=4.2.1.7&versioncode=371&market_id=tool_huluxia&_key=&device_code=%5Bd%5D7f659db3-9ffb-41ec-80c3-fbf0db5691a9&phone_brand_type=UN"

    # 登录请求的数据
    data = {
        "account": account,
        "login_type": "2",
        "password": password_encode,
        "sign": account_sign
    }

    # 请求头
    headers = {
        "Host": "floor.huluxia.com",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "okhttp/3.8.1"
    }

    # 发送登录请求
    response_login = get_response(url, method='POST', headers=headers, data=data)
    if response_login:
        login_json = json.loads(response_login)
        # 检查登录状态
        if login_json.get('status') == 1:
            login_info = login_json['user']
            print(
                f"——{'—' * 20}\n当前状态: 登陆成功\n用户ID: {login_info['userID']}\n用户名: {login_info['nick']}\n——{'—' * 20}")
            return login_json['_key']
    return None


def process_run(loginkey):
    """
    根据登录密钥执行签到操作。

    :param loginkey: 登录成功后返回的登录密钥
    """
    url = "http://floor.huluxia.com/category/list/ANDROID/2.0"
    # 获取分类列表数据
    getiddata = get_categoryid_list(url)
    if getiddata is None:
        return

    # 使用正则表达式提取分类 ID 和标题
    categoryids = re.findall(r'"categoryID":(.*?),', getiddata)
    titles = re.findall(r'"title":"(.*?)",', getiddata)
    print(f"板块数量: {len(categoryids)}")

    sign_counts = 0  # 成功签到的数量
    for title, categoryid in zip(titles, categoryids):
        timestamp = str(int(time.time() * 1000))  # 当前时间戳
        encode_text = f"cat_id{categoryid}time{timestamp}fa1c28a5b62e79c3e63d9030b6142e4b"
        md5_encode = hashlib.md5(encode_text.encode()).hexdigest().upper()  # 签名
        post_data = f"sign={md5_encode}"  # POST 数据

        # 签到请求的 URL
        sign_url = f"http://floor.huluxia.com/user/signin/ANDROID/4.1.8?platform=2&gkey=000000&app_version=4.2.1.7&versioncode=371&market_id=tool_huluxia&_key={loginkey}&phone_brand_type=UN&cat_id={categoryid}&time={timestamp}"
        signdata = send_sign_post(sign_url, post_data)

        if signdata:
            signjson = json.loads(signdata)
            # 检查签到状态
            if signjson.get('status') == 1:
                sign_counts += 1  # 成功签到计数

    print(f"——{'—' * 20}\n签到成功：{sign_counts}个板块\n——{'—' * 20}")


def read_accounts(file_path):
    """
    从文件中读取账号信息。

    :param file_path: 包含账号和密码的文件路径
    :return: 账号和密码的字典
    """
    accounts = {}
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()  # 去除行首尾空格
            if line:  # 确保行不为空
                username, password = line.split(':', 1)  # 分割账号和密码
                accounts[username] = password  # 存入字典
    return accounts


def send_email(success_accounts, failed_accounts, config):
    """
    发送邮件通知。

    :param success_accounts: 签到成功的账号列表
    :param failed_accounts: 签到失败的账号列表
    :param config: 邮件配置信息
    """

    # 获取配置信息
    sender_email = config['sender_email']
    sender_password = config['sender_password']
    receiver_email = config['receiver_email']
    smtp_server = config['smtp_server']
    smtp_port = config['smtp_port']
    encryption_type = config['encryption_type']
    subject = config['subject'] + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    # 邮件内容处理
    success_message = "签到成功的账号："
    failed_message = "签到失败的账号："

    if success_accounts:
        success_message += "\n" + "\n".join(f"- {account}" for account in success_accounts)
    if failed_accounts:
        failed_message += "\n" + "\n".join(f"- {account}" for account in failed_accounts)

    body = f"{success_message}\n{failed_message}"

    # 创建邮件对象
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # 发送邮件
    try:
        if encryption_type == 'ssl':
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
        elif encryption_type == 'tls':
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # 启动 TLS 加密
                server.login(sender_email, sender_password)
                server.send_message(msg)
        else:
            print("无效的加密类型。请使用 'ssl' 或 'tls'。")
        print("邮件发送成功！")
    except smtplib.SMTPAuthenticationError:
        print("身份验证失败。请检查你的邮箱和密码。")
    except smtplib.SMTPException as e:
        print(f"SMTP错误发生：{e}")
    except Exception as e:
        print(f"发生错误：{e}")


if __name__ == "__main__":

    # 签到成功账号列表
    success_accounts = []

    # 失败的账号列表
    failed_accounts = []

    # 获取当前脚本所在的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, 'config.json')

    # 打开 config.json 文件
    with open(config_path, encoding='utf-8') as config_file:
        config = json.load(config_file)

    # 遍历账号信息并登录签到
    for accounts in config['accounts']:
        account = accounts['phone']
        password = accounts['password']
        print(f"正在登录账号：{account}")
        loginkey = get_login_sign(account, password)  # 登录并获取登录密钥

        # 如果登录失败添加到失败记录后续邮箱提醒
        if not loginkey:
            print(f"登录失败：{account}，请检查账号密码是否正确")
            failed_accounts.append(account)
            continue

        if loginkey:
            success_accounts.append(account)
            process_run(loginkey)  # 执行签到

    if config['isEmailEnabled']:
        print("正在发送通知邮箱")
        send_email(success_accounts, failed_accounts, config)  # 发送邮件提醒
