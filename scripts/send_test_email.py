import os
import sys
import json
import urllib.request
import urllib.error

def send_test_email():
    # 1. Try to load Resend API Key from apps/api/.env
    env_path = os.path.join(os.path.dirname(__file__), "..", "apps", "api", ".env")
    resend_key = None

    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("RESEND_API_KEY="):
                    resend_key = line.split("=", 1)[1].strip()
                    break

    if not resend_key:
        resend_key = os.getenv("RESEND_API_KEY")

    if not resend_key or resend_key == "re_your_key":
        print("❌ Error: RESEND_API_KEY is not set or is still a placeholder in apps/api/.env")
        sys.exit(1)

    print(f"🔑 Found Resend API Key: {resend_key[:8]}...")

    # 2. Get destination email
    if len(sys.argv) > 1:
        recipient = sys.argv[1]
    else:
        recipient = input("📬 Enter recipient email address: ").strip()

    if not recipient:
        print("❌ Error: Recipient email address cannot be empty.")
        sys.exit(1)

    # 3. Build payload
    # Note: If your Resend account is in Sandbox/Development mode,
    # you can only send emails to the email address associated with your Resend account.
    payload = {
        "from": "onboarding@resend.dev",
        "to": recipient,
        "subject": "Mediva Test Email",
        "html": """
        <div style="font-family: sans-serif; padding: 20px; background-color: #f9f9f9; border-radius: 8px;">
            <h2 style="color: #00f2fe;">Mediva Platform Verification</h2>
            <p>Hello,</p>
            <p>This is a test email sent from the <strong>Mediva</strong> healthcare platform to verify that your Resend SMTP / HTTP email integration is working correctly.</p>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;" />
            <p style="font-size: 12px; color: #888;">© 2026 Mediva Platform. All rights reserved.</p>
        </div>
        """
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=req_data,
        headers={
            "Authorization": f"Bearer {resend_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    print(f"🚀 Sending email to {recipient}...")
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            print("✅ Email sent successfully!")
            print(f"Response: {res_body}")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"❌ Failed to send email. HTTP Error Code: {e.code}")
        print(f"Details: {err_body}")
    except Exception as e:
        print(f"❌ Error occurred: {e}")

if __name__ == "__main__":
    send_test_email()
