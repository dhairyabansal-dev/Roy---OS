import email
import imaplib
import smtplib
from email.header import decode_header
from email.mime.text import MIMEText

import config
import llm
from agents.base import BaseAgent


class EmailAgent(BaseAgent):
    name = "Email Agent"
    description = "Reads, summarizes, and drafts emails"

    KEYWORDS = ["email", "inbox", "mail", "reply", "draft", "send message"]

    def can_handle(self, text: str) -> bool:
        t = text.lower()
        return any(k in t for k in self.KEYWORDS)

    def handle(self, text: str) -> str:
        t = text.lower()

        if not config.EMAIL_ADDRESS or not config.EMAIL_APP_PASSWORD:
            return (
                "Email isn't connected yet. Set EMAIL_ADDRESS and EMAIL_APP_PASSWORD "
                "as environment variables (use an app password, not your real password). "
                f"Safe diagnostic: {config.credential_presence()}"
            )

        if "unread" in t or "check" in t or "inbox" in t:
            return self._check_unread()
        if "draft" in t or "reply" in t or "write" in t:
            return self._draft_reply(text)

        return "Tell me what to do: 'check unread emails' or 'draft a reply to <name> about <topic>'."

    def _check_unread(self, limit: int = 5) -> str:
        try:
            imap = imaplib.IMAP4_SSL(config.EMAIL_IMAP_HOST)
            imap.login(config.EMAIL_ADDRESS, config.EMAIL_APP_PASSWORD)
            imap.select("INBOX")
            status, data = imap.search(None, "UNSEEN")
            ids = data[0].split()[-limit:]

            summaries = []
            for eid in ids:
                _, msg_data = imap.fetch(eid, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                subj = self._decode(msg.get("Subject", "(no subject)"))
                sender = self._decode(msg.get("From", "(unknown)"))
                summaries.append(f"From: {sender} | Subject: {subj}")

            imap.logout()
            if not summaries:
                return "No unread emails."
            return f"{len(summaries)} unread email(s):\n" + "\n".join(summaries)
        except Exception as e:
            return f"Couldn't check email: {e}"

    def _decode(self, header_value: str) -> str:
        """Decode MIME-encoded headers (e.g. '=?UTF-8?Q?...?=') into readable text."""
        if not header_value:
            return header_value
        parts = decode_header(header_value)
        decoded = ""
        for text, charset in parts:
            if isinstance(text, bytes):
                decoded += text.decode(charset or "utf-8", errors="replace")
            else:
                decoded += text
        return decoded

    def _draft_reply(self, text: str) -> str:
        draft = llm.chat(
            [{"role": "user", "content": text}],
            system=(
                "Write a short, professional email draft based on the user's "
                "request. Output only the email body, no explanation."
            ),
        )
        return f"Draft (not sent — review and say 'send it' to actually send):\n\n{draft}"

    def send(self, to_addr: str, subject: str, body: str) -> str:
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = config.EMAIL_ADDRESS
            msg["To"] = to_addr

            with smtplib.SMTP_SSL(config.EMAIL_SMTP_HOST, 465) as smtp:
                smtp.login(config.EMAIL_ADDRESS, config.EMAIL_APP_PASSWORD)
                smtp.send_message(msg)
            return f"Sent to {to_addr}."
        except Exception as e:
            return f"Failed to send: {e}"
