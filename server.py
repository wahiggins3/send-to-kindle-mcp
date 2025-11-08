#!/usr/bin/env python3
"""
Send to Kindle MCP Server

A FastMCP server that converts text/markdown documents to EPUB format
and sends them to Kindle e-readers via email.
"""

import os
import re
import smtplib
import sys
import tempfile
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path
from typing import Optional, List, Tuple

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


def parse_markdown_sections(content: str) -> List[Tuple[str, str, int]]:
    """
    Parse markdown content and split into sections based on headings.
    
    Returns a list of tuples: (heading_text, section_content, heading_level)
    Sections without headings get heading_text as empty string.
    """
    lines = content.split('\n')
    sections = []
    current_section = []
    current_heading = ""
    current_level = 0
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for ATX-style headings (# ## ### etc.)
        atx_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if atx_match:
            # Save previous section if it has content
            if current_section or current_heading:
                sections.append((current_heading, '\n'.join(current_section), current_level))
            # Start new section
            current_level = len(atx_match.group(1))
            current_heading = atx_match.group(2).strip()
            current_section = []
        # Check for Setext-style headings (underlined with === or ---)
        elif i + 1 < len(lines) and line.strip():
            next_line = lines[i + 1].strip()
            if re.match(r'^={3,}$', next_line):
                # H1 style - current line is heading
                if current_section or current_heading:
                    sections.append((current_heading, '\n'.join(current_section), current_level))
                current_heading = line.strip()
                current_level = 1
                current_section = []
                i += 1  # Skip the underline line
            elif re.match(r'^-{3,}$', next_line):
                # H2 style - current line is heading
                if current_section or current_heading:
                    sections.append((current_heading, '\n'.join(current_section), current_level))
                current_heading = line.strip()
                current_level = 2
                current_section = []
                i += 1  # Skip the underline line
            else:
                current_section.append(line)
        else:
            if line.strip() or current_section:  # Preserve empty lines within sections
                current_section.append(line)
        
        i += 1
    
    # Add final section
    if current_section or current_heading:
        sections.append((current_heading, '\n'.join(current_section), current_level))
    
    # If no headings found, create one section with all content
    if not sections:
        sections.append(("", content, 0))
    
    return sections


def create_epub(title: str, content: str, author: str = "Claude") -> bytes:
    """
    Convert text/markdown content to EPUB format with proper chapter structure.
    
    The function automatically detects markdown headings (H1, H2, etc.) and creates
    separate chapters for each major section, making navigation easier on Kindle.

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

    # Parse content into sections based on headings
    sections = parse_markdown_sections(content)
    logger.info(f"Parsed content into {len(sections)} sections")

    # Add CSS for better formatting
    css = '''
        body {
            font-family: Georgia, serif;
            line-height: 1.6;
            margin: 1em;
            padding: 1em;
        }
        h1 {
            font-family: Arial, sans-serif;
            font-size: 1.8em;
            margin-top: 1.5em;
            margin-bottom: 0.8em;
            border-bottom: 2px solid #333;
            padding-bottom: 0.3em;
        }
        h2 {
            font-family: Arial, sans-serif;
            font-size: 1.5em;
            margin-top: 1.3em;
            margin-bottom: 0.6em;
            border-bottom: 1px solid #666;
            padding-bottom: 0.2em;
        }
        h3 {
            font-family: Arial, sans-serif;
            font-size: 1.2em;
            margin-top: 1em;
            margin-bottom: 0.5em;
        }
        h4, h5, h6 {
            font-family: Arial, sans-serif;
            margin-top: 0.8em;
            margin-bottom: 0.4em;
        }
        code {
            font-family: 'Courier New', monospace;
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
        }
        pre {
            background-color: #f4f4f4;
            padding: 1em;
            overflow-x: auto;
            border-left: 3px solid #ccc;
            margin: 1em 0;
        }
        blockquote {
            border-left: 3px solid #ccc;
            margin-left: 0;
            padding-left: 1em;
            color: #666;
            font-style: italic;
        }
        p {
            margin: 0.8em 0;
        }
    '''

    style = epub.EpubItem(
        uid="style",
        file_name="style.css",
        media_type="text/css",
        content=css
    )
    book.add_item(style)

    # Create chapters from sections
    chapters = []
    toc_items = []
    chapter_num = 0
    
    for heading, section_content, heading_level in sections:
        # Skip empty sections
        if not section_content.strip() and not heading:
            continue
        
        chapter_num += 1
        
        # Determine chapter title
        if heading:
            chapter_title = heading
        elif chapter_num == 1:
            chapter_title = title  # Use document title for first section if no heading
        else:
            chapter_title = f"Section {chapter_num}"
        
        # Convert section markdown to HTML
        # If this section has a heading, we need to include it in the markdown
        if heading and heading_level > 0:
            # Reconstruct the heading in markdown format
            heading_md = '#' * heading_level + ' ' + heading
            full_content = heading_md + '\n\n' + section_content
        else:
            full_content = section_content
        
        html_content = markdown.markdown(
            full_content,
            extensions=['extra', 'codehilite', 'nl2br', 'sane_lists']
        )
        
        # Create chapter file
        file_name = f'chapter_{chapter_num:03d}.xhtml'
        chapter = epub.EpubHtml(
            title=chapter_title,
            file_name=file_name,
            lang='en'
        )
        
        chapter.content = f'<html><head><link rel="stylesheet" href="style.css"/></head><body>{html_content}</body></html>'
        chapter.add_item(style)
        
        book.add_item(chapter)
        chapters.append(chapter)
        
        # Add to TOC - for simplicity, add all chapters as top-level items
        # EPUB readers will handle the hierarchy based on heading levels in content
        toc_items.append(chapter)
    
    # If no chapters were created, create a default one
    if not chapters:
        chapter = epub.EpubHtml(
            title=title,
            file_name='content.xhtml',
            lang='en'
        )
        html_content = markdown.markdown(
            content,
            extensions=['extra', 'codehilite', 'nl2br', 'sane_lists']
        )
        chapter.content = f'<html><head><link rel="stylesheet" href="style.css"/></head><body>{html_content}</body></html>'
        chapter.add_item(style)
        book.add_item(chapter)
        chapters.append(chapter)
        toc_items = [chapter]

    # Define Table of Contents
    book.toc = tuple(toc_items) if toc_items else tuple(chapters)

    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Define spine (nav first, then all chapters)
    book.spine = ['nav'] + chapters

    # Write to bytes
    with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as tmp_file:
        epub.write_epub(tmp_file.name, book)
        tmp_path = tmp_file.name

    with open(tmp_path, 'rb') as f:
        epub_bytes = f.read()

    # Clean up temp file
    os.unlink(tmp_path)

    logger.info(f"Created EPUB with {len(chapters)} chapters")
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
    author: Optional[str] = None
) -> str:
    """
    Convert content to EPUB and send it to your Kindle e-reader.

    This tool takes text or markdown content, converts it to a properly
    formatted EPUB file with chapter navigation, and emails it to your 
    registered Kindle address. The document will automatically appear 
    in your Kindle library.

    IMPORTANT: Before calling this tool, you should:
    1. Ask the user for a title for the document (if not already provided)
    2. Ask the user for the author name (if not already provided)
    
    The tool automatically creates chapters from markdown headings (H1, H2, etc.),
    making it easy to navigate longer documents on Kindle.

    Args:
        content: The document content (supports markdown formatting with headings)
        title: The title for the document (REQUIRED - ask user if not provided)
        author: The author name (optional - defaults to AUTHOR_NAME env var, then "Claude")

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
        
        # Get author from environment variable first, then parameter, then default
        # This ensures the configured author name is used unless explicitly overridden
        env_author = os.getenv("AUTHOR_NAME")
        if env_author:
            author_name = env_author
            logger.info(f"Using author from AUTHOR_NAME env var: {author_name}")
        elif author and author.lower() not in ["claude", "anthropic", "claude / anthropic"]:
            # Only use parameter if it's not a default Claude name
            author_name = author
            logger.info(f"Using author from parameter: {author_name}")
        else:
            # Fallback to env var or default
            author_name = env_author or "Claude"
            logger.info(f"Using default author: {author_name}")

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
        epub_data = create_epub(title, content, author_name)
        logger.info(f"EPUB created successfully ({len(epub_data)} bytes)")

        # Prepare email with Kindle-friendly filename
        # Create a clean, short filename that displays well on Kindle
        # Remove special characters, convert to lowercase, use hyphens
        safe_title = title.lower()  # Start with lowercase
        safe_title = re.sub(r'[^\w\s-]', '', safe_title)  # Remove special chars except spaces and hyphens
        safe_title = re.sub(r'[_\s]+', '-', safe_title)  # Replace spaces and underscores with hyphens
        safe_title = re.sub(r'-+', '-', safe_title)  # Replace multiple hyphens with single
        safe_title = safe_title.strip('-')  # Remove leading/trailing hyphens
        
        # Limit filename length (Kindle displays better with shorter names)
        # Keep it under 40 chars for better readability (leaves room for .epub)
        if len(safe_title) > 40:
            # Try to truncate at a word boundary (hyphen)
            truncated = safe_title[:40]
            last_hyphen = truncated.rfind('-')
            if last_hyphen > 20:  # Only use hyphen break if it's not too short
                safe_title = truncated[:last_hyphen]
            else:
                safe_title = truncated.rstrip('-')
        
        safe_filename = f"{safe_title}.epub" if safe_title else "document.epub"
        logger.info(f"Generated filename: {safe_filename}")
        subject = f"Document: {title}"
        body = f"Attached document: {title}\nAuthor: {author_name}\n\nSent via Send to Kindle MCP Server"

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
