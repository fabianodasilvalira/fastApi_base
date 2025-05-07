# app/core/email_utils.py
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os

from app.core.config import settings

# Configuração da conexão com o servidor de e-mail
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    MAIL_DEBUG=settings.MAIL_DEBUG,
    TEMPLATE_FOLDER=settings.MAIL_TEMPLATE_FOLDER # Aponta para a pasta de templates
)

# Configuração do ambiente Jinja2 para carregar templates HTML
# O caminho para a pasta de templates é relativo à raiz do projeto ou absoluto
# settings.MAIL_TEMPLATE_FOLDER deve ser o caminho absoluto para /app/templates/email
if settings.MAIL_TEMPLATE_FOLDER and os.path.exists(settings.MAIL_TEMPLATE_FOLDER):
    env = Environment(
        loader=FileSystemLoader(settings.MAIL_TEMPLATE_FOLDER),
        autoescape=select_autoescape(['html', 'xml'])
    )
else:
    env = None
    print(f"Atenção: Pasta de templates de e-mail não encontrada em {settings.MAIL_TEMPLATE_FOLDER}. E-mails HTML podem não funcionar.")

async def send_email(
    email_to: EmailStr,
    subject: str = "",
    html_template: Optional[str] = None,
    template_body: Optional[Dict[str, Any]] = None,
    plain_text_body: Optional[str] = None
) -> None:
    """
    Envia um e-mail.

    Args:
        email_to: Destinatário do e-mail.
        subject: Assunto do e-mail.
        html_template: Nome do arquivo de template HTML (ex: "verification.html").
        template_body: Dicionário com variáveis para o template HTML.
        plain_text_body: Corpo do e-mail em texto plano (usado se html_template não for fornecido).
    """
    if not settings.MAIL_SERVER or not settings.MAIL_FROM:
        print("Configurações de e-mail (MAIL_SERVER, MAIL_FROM) não definidas. E-mail não enviado.")
        # Em um ambiente de produção, você pode querer levantar um erro aqui ou logar criticamente.
        return

    message_data = {
        "subject": subject,
        "recipients": [email_to],
    }

    if html_template and env and template_body:
        template = env.get_template(html_template)
        html_content = template.render(template_body)
        message_data["body"] = html_content
        message_data["subtype"] = MessageType.html
    elif plain_text_body:
        message_data["body"] = plain_text_body
        message_data["subtype"] = MessageType.plain
    else:
        print("Corpo do e-mail (HTML ou texto plano) não fornecido. E-mail não enviado.")
        return

    message = MessageSchema(**message_data)

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        print(f"E-mail enviado para {email_to} com assunto '{subject}'")
    except Exception as e:
        print(f"Erro ao enviar e-mail para {email_to}: {e}")
        # Adicionar logging mais robusto aqui em produção

async def send_email_verification_email(
    email_to: EmailStr,
    username: str,
    token: str
) -> None:
    """Envia e-mail de verificação de conta."""
    subject = f"{settings.MAIL_FROM_NAME} - Verificação de E-mail"
    verification_link = f"{settings.APP_BASE_URL}/users/verify-email/{token}"
    
    template_body = {
        "title": "Verifique seu E-mail",
        "username": username,
        "verification_link": verification_link,
        "app_name": settings.MAIL_FROM_NAME
    }
    # Opcionalmente, crie um arquivo verification.html em app/templates/email/
    # await send_email(email_to, subject, html_template="verification.html", template_body=template_body)
    # Por enquanto, enviaremos em texto plano se o template não existir
    plain_text_body = (
        f"Olá {username},\n\n" 
        f"Obrigado por se registrar no {settings.MAIL_FROM_NAME}.\n"
        f"Por favor, clique no link a seguir para verificar seu endereço de e-mail:\n"
        f"{verification_link}\n\n"
        f"Se você não se registrou, por favor ignore este e-mail.\n\n"
        f"Atenciosamente,\n{settings.MAIL_FROM_NAME}"
    )
    await send_email(email_to, subject, plain_text_body=plain_text_body, html_template="verification_email.html", template_body=template_body)

async def send_password_reset_email(
    email_to: EmailStr,
    username: str,
    token: str
) -> None:
    """Envia e-mail de redefinição de senha."""
    subject = f"{settings.MAIL_FROM_NAME} - Redefinição de Senha"
    reset_link = f"{settings.APP_BASE_URL}/users/reset-password/{token}"
    
    template_body = {
        "title": "Redefinir sua Senha",
        "username": username,
        "reset_link": reset_link,
        "app_name": settings.MAIL_FROM_NAME,
        "valid_hours": settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
    }
    # Opcionalmente, crie um arquivo password_reset.html em app/templates/email/
    # await send_email(email_to, subject, html_template="password_reset.html", template_body=template_body)
    # Por enquanto, enviaremos em texto plano se o template não existir
    plain_text_body = (
        f"Olá {username},\n\n"
        f"Recebemos uma solicitação para redefinir sua senha no {settings.MAIL_FROM_NAME}.\n"
        f"Por favor, clique no link a seguir para criar uma nova senha:\n"
        f"{reset_link}\n\n"
        f"Este link é válido por {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hora(s).\n"
        f"Se você não solicitou uma redefinição de senha, por favor ignore este e-mail.\n\n"
        f"Atenciosamente,\n{settings.MAIL_FROM_NAME}"
    )
    await send_email(email_to, subject, plain_text_body=plain_text_body, html_template="password_reset_email.html", template_body=template_body)

# Funções para gerar tokens seguros (podem ficar em security.py ou aqui)
def generate_secure_token(length: int = 32) -> str:
    """Gera um token URL-safe seguro."""
    return secrets.token_urlsafe(length)

# Comentários em português:
# - `conf`: Configuração para `fastapi-mail` usando as definições de `settings`.
# - `env`: Ambiente Jinja2 para carregar templates HTML de e-mail da pasta especificada em `settings.MAIL_TEMPLATE_FOLDER`.
# - `send_email`: Função genérica para enviar e-mails. Pode usar templates HTML ou texto plano.
# - `send_email_verification_email`: Envia um e-mail específico para verificação de conta.
# - `send_password_reset_email`: Envia um e-mail específico para redefinição de senha.
# - `generate_secure_token`: Gera um token aleatório seguro para ser usado em links de verificação/reset.
# - As funções de envio de e-mail verificam se as configurações essenciais do servidor de e-mail estão presentes.
# - É importante criar os templates HTML (`verification_email.html`, `password_reset_email.html`) na pasta `app/templates/email/` para e-mails formatados.

