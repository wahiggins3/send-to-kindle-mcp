#!/usr/bin/env python3
"""
Send to Kindle MCP Server

A FastMCP server that converts text/markdown documents to EPUB format
and sends them to Kindle e-readers via email.
"""

import os
import smtplib
import sys
import tempfile
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from ebooklib import epub
import markdown
from fastmcp import FastMCP

# Configure logging to stderr (visible in Claude Desktop logs)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("send-to-kindle")


def create_epub(title: str, content: str, author: str = "Claude") -> bytes:
    """
    Convert text/markdown content to EPUB format.

    Args:
        title: The title of the document
        content: The content (can be markdown or plain text)
        author: The author name (defaults to "Claude")

    Returns:
        bytes: The EPUB file content
    """
    book = epub.EpubBook()

    # Set metadata
    book.set_identifier(f"id-{title.replace(' ', '-').lower()}")
    book.set_title(title)
    book.set_language("en")
    book.add_author(author)

    # Convert markdown to HTML
    html_content = markdown.markdown(
        content,
        extensions=['extra', 'codehilite', 'nl2br', 'sane_lists']
    )

    # Create chapter
    chapter = epub.EpubHtml(
        title=title,
        file_name='content.xhtml',
        lang='en'
    )

    # Add CSS for better formatting
    css = '''
        body {
            font-family: Georgia, serif;
            line-height: 1.6;
            margin: 1em;
        }
        h1, h2, h3 {
            font-family: Arial, sans-serif;
            margin-top: 1em;
            margin-bottom: 0.5em;
        }
        code {
            font-family: 'Courier New', monospace;
            background-color: #f4f4f4;
            padding: 2px 4px;
        }
        pre {
            background-color: #f4f4f4;
            padding: 1em;
            overflow-x: auto;
        }
        blockquote {
            border-left: 3px solid #ccc;
            margin-left: 0;
            padding-left: 1em;
            color: #666;
        }
    '''

    style = epub.EpubItem(
        uid="style",
        file_name="style.css",
        media_type="text/css",
        content=css
    )
    book.add_item(style)

    chapter.content = f'<html><head><link rel="stylesheet" href="style.css"/></head><body>{html_content}</body></html>'
    chapter.add_item(style)

    # Add chapter to book
    book.add_item(chapter)

    # Define Table of Contents
    book.toc = (chapter,)

    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Define spine
    book.spine = ['nav', chapter]

    # Write to bytes
    with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as tmp_file:
        epub.write_epub(tmp_file.name, book)
        tmp_path = tmp_file.name

    with open(tmp_path, 'rb') as f:
        epub_bytes = f.read()

    # Clean up temp file
    os.unlink(tmp_path)

    return epub_bytes


def send_email_with_attachment(
    to_email: str,
    subject: str,
    body: str,
    attachment_data: bytes,
    attachment_name: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    from_email: str
) -> None:
    """
    Send an email with an attachment via SMTP.

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body text
        attachment_data: Binary data of the attachment
        attachment_name: Filename for the attachment
        smtp_host: SMTP server hostname
        smtp_port: SMTP server port
        smtp_user: SMTP username
        smtp_password: SMTP password
        from_email: Sender email address
    """
    logger.info(f"Preparing to send email to {to_email} via {smtp_host}:{smtp_port}")
    logger.debug(f"SMTP user: {smtp_user}, From: {from_email}")
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Add body
    msg.attach(MIMEText(body, 'plain'))

    # Add attachment
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment_data)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename={attachment_name}')
    msg.attach(part)

    # Send email with detailed error handling
    try:
        logger.info(f"Connecting to SMTP server {smtp_host}:{smtp_port}")
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            logger.info("Starting TLS encryption")
            server.starttls()
            
            logger.info(f"Attempting to authenticate as {smtp_user}")
            try:
                server.login(smtp_user, smtp_password)
                logger.info("Authentication successful")
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"SMTP Authentication failed: {e}")
                logger.error("Common causes:")
                logger.error("  - Using regular password instead of App Password (for Gmail)")
                logger.error("  - App Password not generated or incorrect")
                logger.error("  - 2FA not enabled (required for App Passwords)")
                logger.error("  - Username/email address incorrect")
                raise
            except smtplib.SMTPException as e:
                logger.error(f"SMTP error during login: {e}")
                raise
            
            logger.info(f"Sending email with attachment '{attachment_name}' ({len(attachment_data)} bytes)")
            server.send_message(msg)
            logger.info("Email sent successfully")
            
    except smtplib.SMTPConnectError as e:
        logger.error(f"Failed to connect to SMTP server: {e}")
        raise Exception(f"Could not connect to {smtp_host}:{smtp_port}. Check your SMTP_HOST and SMTP_PORT settings.")
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        raise Exception(f"SMTP authentication failed. For Gmail, ensure you're using an App Password, not your regular password. Error: {e}")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        raise Exception(f"SMTP error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}", exc_info=True)
        raise


@mcp.tool()
def send_to_kindle(
    content: str,
    title: str,
    author: Optional[str] = "Claude"
) -> str:
    """
    Convert content to EPUB and send it to your Kindle e-reader.

    This tool takes text or markdown content, converts it to a properly
    formatted EPUB file, and emails it to your registered Kindle address.
    The document will automatically appear in your Kindle library.

    Args:
        content: The document content (supports markdown formatting)
        title: The title for the document
        author: The author name (optional, defaults to "Claude")

    Returns:
        A success message or error description
    """
    try:
        logger.info("Starting send_to_kindle request")
        
        # Get configuration from environment
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port_str = os.getenv("SMTP_PORT", "587")
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        kindle_email = os.getenv("KINDLE_EMAIL")
        from_email = os.getenv("FROM_EMAIL", smtp_user)

        logger.debug(f"Configuration loaded - Host: {smtp_host}, Port: {smtp_port_str}, User: {smtp_user}, Kindle: {kindle_email}")

        # Validate configuration
        if not all([smtp_host, smtp_user, smtp_password, kindle_email]):
            missing = []
            if not smtp_host:
                missing.append("SMTP_HOST")
            if not smtp_user:
                missing.append("SMTP_USER")
            if not smtp_password:
                missing.append("SMTP_PASSWORD")
            if not kindle_email:
                missing.append("KINDLE_EMAIL")
            error_msg = f"Error: Missing email configuration. Please set: {', '.join(missing)}"
            logger.error(error_msg)
            return error_msg

        # Validate and convert port
        try:
            smtp_port = int(smtp_port_str)
        except ValueError:
            error_msg = f"Error: Invalid SMTP_PORT value '{smtp_port_str}'. Must be a number."
            logger.error(error_msg)
            return error_msg

        # Create EPUB
        logger.info(f"Creating EPUB for '{title}' (content length: {len(content)} chars)")
        epub_data = create_epub(title, content, author)
        logger.info(f"EPUB created successfully ({len(epub_data)} bytes)")

        # Prepare email
        safe_filename = f"{title.replace(' ', '_')}.epub"
        subject = f"Document: {title}"
        body = f"Attached document: {title}\nAuthor: {author}\n\nSent via Send to Kindle MCP Server"

        # Send email
        send_email_with_attachment(
            to_email=kindle_email,
            subject=subject,
            body=body,
            attachment_data=epub_data,
            attachment_name=safe_filename,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            from_email=from_email
        )

        success_msg = f"Successfully sent '{title}' to {kindle_email}. The document should appear in your Kindle library shortly."
        logger.info(success_msg)
        return success_msg

    except Exception as e:
        error_msg = f"Error sending to Kindle: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


if __name__ == "__main__":
    mcp.run()
