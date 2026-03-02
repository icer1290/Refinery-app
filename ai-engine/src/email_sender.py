"""
邮件发送模块
提供 SMTP 邮件发送功能，支持 HTML 邮件
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from datetime import datetime
from email.header import Header
from email.utils import formataddr


class EmailSender:
    """
    邮件发送器
    
    使用 SMTP 协议发送 HTML 邮件，支持 Gmail 等常用邮箱服务
    """
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_pass: Optional[str] = None,
        use_tls: bool = True
    ):
        """
        初始化邮件发送器
        
        Args:
            smtp_host: SMTP 服务器地址，默认从环境变量 SMTP_HOST 读取
            smtp_port: SMTP 端口，默认从环境变量 SMTP_PORT 读取或 587
            smtp_user: SMTP 用户名/邮箱，默认从环境变量 SMTP_USER 读取
            smtp_pass: SMTP 密码/授权码，默认从环境变量 SMTP_PASS 读取
            use_tls: 是否使用 TLS 加密，默认 True
        """
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER")
        self.smtp_pass = smtp_pass or os.getenv("SMTP_PASS")
        self.use_tls = use_tls
        
        if not self.smtp_user:
            raise ValueError("SMTP 用户名未配置，请设置 SMTP_USER 环境变量")
        if not self.smtp_pass:
            raise ValueError("SMTP 密码未配置，请设置 SMTP_PASS 环境变量")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_name: Optional[str] = None
    ) -> bool:
        """
        发送 HTML 邮件
        
        Args:
            to_email: 收件人邮箱地址
            subject: 邮件主题
            html_content: HTML 格式的邮件内容
            from_name: 发件人显示名称，默认使用邮箱用户名
            
        Returns:
            bool: 发送成功返回 True，否则返回 False
        """
        try:
            # 1. 确保发件人名称经过正确编码
            display_name = from_name or '科技新闻日报'

            # 2. 使用 formataddr 来构建标准的发件人格式
            from_header = formataddr((Header(display_name, 'utf-8').encode(), self.smtp_user))

            # 创建邮件消息
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = from_header
            msg['To'] = to_email
            
            from email.utils import formatdate
            msg['Date'] = formatdate(localtime=True)

            # 添加 HTML 内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 连接 SMTP 服务器并发送
            print(f"  正在连接 SMTP 服务器: {self.smtp_host}:{self.smtp_port}")
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=ssl.create_default_context())
                
                print(f"  正在登录 SMTP 服务器...")
                server.login(self.smtp_user, self.smtp_pass)
                
                print(f"  正在发送邮件到: {to_email}")
                server.send_message(msg)
            
            print(f"  ✓ 邮件发送成功")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"  ✗ SMTP 认证失败: {e}")
            print(f"    请检查 SMTP_USER 和 SMTP_PASS 配置")
            return False
        except smtplib.SMTPException as e:
            print(f"  ✗ SMTP 错误: {e}")
            return False
        except Exception as e:
            print(f"  ✗ 发送邮件失败: {e}")
            return False
    
    def send_newsletter(
        self,
        to_email: str,
        html_content: str,
        date_str: Optional[str] = None
    ) -> bool:
        """
        发送科技新闻日报
        
        Args:
            to_email: 收件人邮箱地址
            html_content: HTML 格式的邮件内容
            date_str: 日期字符串，用于邮件主题，默认使用今日日期
            
        Returns:
            bool: 发送成功返回 True，否则返回 False
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y年%m月%d日")
        
        subject = f"📰 科技新闻日报 - {date_str}"
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            from_name="科技新闻日报"
        )


# 全局邮件发送器实例
_email_sender: Optional[EmailSender] = None


def get_email_sender() -> EmailSender:
    """
    获取全局邮件发送器实例（单例模式）
    
    Returns:
        EmailSender: 邮件发送器实例
    """
    global _email_sender
    if _email_sender is None:
        _email_sender = EmailSender()
    return _email_sender


def send_newsletter(
    to_email: str,
    html_content: str,
    date_str: Optional[str] = None
) -> bool:
    """
    便捷函数：发送科技新闻日报
    
    Args:
        to_email: 收件人邮箱地址
        html_content: HTML 格式的邮件内容
        date_str: 日期字符串，默认使用今日日期
        
    Returns:
        bool: 发送成功返回 True，否则返回 False
    """
    sender = get_email_sender()
    return sender.send_newsletter(to_email, html_content, date_str)


# 测试代码
if __name__ == "__main__":
    # 加载环境变量
    from dotenv import load_dotenv
    load_dotenv()
    
    # 测试邮件发送
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>测试邮件</title>
    </head>
    <body>
        <h1>邮件发送测试</h1>
        <p>这是一封测试邮件，用于验证 SMTP 配置是否正确。</p>
        <p>发送时间: {}</p>
    </body>
    </html>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # 发送到配置的发件人邮箱（测试）
    sender = get_email_sender()
    result = sender.send_email(
        to_email=sender.smtp_user,
        subject="【测试】科技新闻日报 - SMTP 配置测试",
        html_content=test_html
    )
    
    if result:
        print("\n✓ 测试邮件发送成功！")
    else:
        print("\n✗ 测试邮件发送失败，请检查配置")
