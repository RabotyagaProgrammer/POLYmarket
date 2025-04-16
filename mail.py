import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to_email, otp):
    # Настройки SMTP-сервера (Mail.ru)
    smtp_server = "smtp.mail.ru"
    smtp_port = 587  # Используем порт с TLS
    sender_email = "polymarker@mail.ru"  # Замените на вашу почту
    sender_password = "27Sd8m1465DhqAHKBBD1"      # Замените на ваш пароль или пароль приложения

    # Создание сообщения
    subject = "Код подтверждения для входа"
    body = f"Ваш код подтверждения: {otp}. Пожалуйста, не сообщайте его никому."

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # Отправка письма
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Шифрование соединения
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, message.as_string())
        print("Письмо успешно отправлено!")
    except Exception as e:
        print(f"Ошибка при отправке письма: {e}")