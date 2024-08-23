def verifyID():
    #TODO:verify id
    return True


import random
from twilio.rest import Client


def generate_otp(length=6):
    """Generates a random OTP with the given length."""
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])


import smtplib
from email.mime.text import MIMEText


def send_sms_via_email(phone_number, carrier_domain, message_body):
    # Your email credentials
    sender_email = 'yairby65@gmail.com'
    sender_password = 'yb65YB@_'

    # Construct the recipient's email address
    to_number = f"{phone_number}@{carrier_domain}"

    # Create the email message
    msg = MIMEText(message_body)
    msg['From'] = sender_email
    msg['To'] = to_number
    msg['Subject'] = 'SMS via Email'

    # Send the email via SMTP server
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_number, msg.as_string())

    print(f"Message sent to {to_number}")


# Example usage
if __name__ == "__main__":
    phone_number = '0549776922'  # Replace with the recipient's phone number
    carrier_domain = 'vtext.com'  # Replace with the carrier's gateway domain
    message_body = 'Hello, this is a test SMS sent via email.'

    send_sms_via_email(phone_number, carrier_domain, message_body)
