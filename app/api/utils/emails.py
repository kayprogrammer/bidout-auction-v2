from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .threads import EmailThread
from app.core.config import settings
from app.db.managers.accounts import otp_manager


async def sort_email(db, user, type):
    template = "welcome.html"
    subject = "Account verified"

    data = {"template": template, "subject": subject}

    # Sort different templates and subject for respective email types
    if type == "activate":
        template = "email-activation.html"
        subject = "Activate your account"
        otp = (await otp_manager.create(db, {"user_id": user.id})).code
        data = {"template": template, "subject": subject, "otp": otp}

    elif type == "reset":
        template = "password-reset.html"
        subject = "Reset your password"
        otp = (await otp_manager.create(db, {"user_id": user.id})).code
        data = {"template": template, "subject": subject, "otp": otp}

    elif type == "reset-success":
        template = "password-reset-success.html"
        subject = "Password reset successfully"
        data = {"template": template, "subject": subject}

    return data


async def send_email(request, db, user, type):
    template_env = request.app.ctx.template_env
    email_data = await sort_email(db, user, type)
    template = email_data["template"]
    subject = email_data["subject"]

    context = {"name": user.first_name}
    otp = email_data.get("otp")
    if otp:
        context["otp"] = otp

    # Render the email template using Sanic-Jinja2
    template = template_env.get_template(template)
    html = template.render(context)

    # Create a message with the HTML content
    message = MIMEMultipart()
    message["From"] = settings.MAIL_SENDER_EMAIL
    message["To"] = user.email
    message["Subject"] = subject
    message.attach(MIMEText(html, "html"))

    # Send email in background
    EmailThread(message).start()
