Ankore Fresh - Email Setup Guide

1) Using Gmail (recommended for small-scale / dev with App Passwords)

- Enable 2-Step Verification on the Gmail account.
- Create an App Password (select "Mail" + appropriate device) and copy the 16-character password.
- In your `.env` (copy from `.env.example`) set:
  - EMAIL_HOST=smtp.gmail.com
  - EMAIL_PORT=587
  - EMAIL_USE_TLS=True
  - EMAIL_HOST_USER=your@gmail.com
  - EMAIL_HOST_PASSWORD=<app-password>
  - DEFAULT_FROM_EMAIL=your@gmail.com
  - SITE_URL=http://127.0.0.1:8000

2) Development alternative (no SMTP required)

- Use console backend to print emails to the terminal. In your `.env` or `ankore/settings.py` for dev set:
  - EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

3) Using a mail provider (recommended for staging/production)

- Services: SendGrid, Mailgun, Amazon SES, Mailtrap (testing)
- Set the provider's SMTP host/port/user/password in the `.env` variables above.

4) Test sending

- Run Django management command (after activating virtualenv):

```bash
python manage.py send_test_email user@example.com
```

- Or test via Django shell:

```bash
python manage.py shell -c "from users.models import User; from users.email_service import send_welcome_email; u=User.objects.get(email='user@example.com'); print(send_welcome_email(u))"
```

5) Troubleshooting

- `535 5.7.8 Username and Password not accepted` — means the SMTP credentials are invalid. For Gmail create an App Password.
- Check `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS` match your SMTP provider's docs.
- For production use a proper transactional email service and verify sending domains.
