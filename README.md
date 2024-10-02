# 葫芦侠自动签到Python脚本

首先安装必要的`requests`模块

```bash
pip install requests
```

   或者

```bash
pip3 install requests
```


修改config.json文件，再运行signin.py即可

配置文件说明
```json5
{
  "isEmailEnabled": true,    // 是否开启邮件提醒
  "encryption_type": "ssl",
  "sender_email": "your_email@example.com",
  "sender_password": "your_password",
  "receiver_email": "recipient@example.com",
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "subject": "HuluXia 签到提醒信息",
  
  // 葫芦侠手机号密码列表
  "accounts": [
    {
      "phone": "1234567890",
      "password": "password1"
    },
    {
      "phone": "0987654321",
      "password": "password2"
    }
  ]
}
```

后续可以使用Linux定时任务在云服务器中每天自动签到，可以参考文章[https://blog.fivk.cn/archives/6537.html](https://blog.fivk.cn/archives/6537.html)。
