import requests
import json
import hashlib
import time
import re


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
    response_login = get_response(url, method='POST', headers=headers,data=data)
    if response_login:
        login_json = json.loads(response_login)
        # 检查登录状态
        if login_json.get('status') == 1:
            login_info = login_json['user']
            print(f"——{'—' * 20}\n当前状态: 登陆成功\n用户ID: {login_info['userID']}\n用户名: {login_info['nick']}\n——{'—' * 20}")
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


if __name__ == "__main__":
    file_path = 'accounts.txt'  # 替换为你的文件路径
    accounts = read_accounts(file_path)  # 读取账号信息
    for account, password in accounts.items():
        print(f"正在登录账号：{account}")
        loginkey = get_login_sign(account, password)  # 登录并获取登录密钥
        if loginkey:  # 如果登录成功
            process_run(loginkey)  # 执行签到
