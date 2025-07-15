import os
from PIL import Image
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import secrets


def convert_heic_to_jpeg(heic_path):
    heic_path = heic_path
    jpeg_path = os.path.splitext(heic_path)[0] + '.jpg'
    try:
        with Image.open(heic_path) as img:
            img.convert("RGB").save(jpeg_path, "JPEG")
    except Exception as e:
        print(f"Failed to convert {heic_path} to JPEG: {e}")



def send_reset_code_email(username, code):
    message = Mail(
        from_email='contact@visiotech.me',
        to_emails='nick@visiotech.me',
        subject='Code de réinitialisation de mot de passe',
        html_content=f"""
        <p>Bonjour Nick,</p>
        <p>Une demande de réinitialisation de mot de passe a été faite pour l'utilisateur <strong>{username}</strong>.</p>
        <p>Code de validation : <strong>{code}</strong></p>
        <p>Veuillez transmettre ce code à l'utilisateur concerné. Ce code est valide pendant 1 heure.</p>
        <p>Cordialement,<br>Galerie Familiale</p>
        """
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'e-mail : {e}")
        return False

def generate_reset_code():
    return secrets.token_hex(3).upper()[:6]