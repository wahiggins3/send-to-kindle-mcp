# Send to Kindle MCP Server

A Model Context Protocol (MCP) server that allows Claude Desktop to send documents directly to your Kindle e-reader. Convert text or markdown content into beautifully formatted EPUB files and deliver them instantly to your Kindle library.

## Features

- 📚 Convert text and markdown to EPUB format
- 📧 Send documents directly to Kindle via email
- 🎨 Properly formatted with CSS styling for optimal reading
- ⚡ Fast and easy integration with Claude Desktop
- 🔒 Secure email configuration with environment variables

## Prerequisites

- Python 3.10 or higher
- A Kindle e-reader or Kindle app
- An email account with SMTP access (Gmail recommended)
- Your Kindle email address (found in Amazon account settings)

## Installation

### 1. Clone or download this repository

```bash
cd ~/path/to/your/projects
git clone <repository-url> send-to-kindle-mcp
cd send-to-kindle-mcp
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### 3. Configure your credentials

Copy the example environment file and fill in your details:

```bash
cp .env.example .env
```

Edit `.env` with your information:

```env
# For Gmail users:
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # See note below

# Your Kindle email address
KINDLE_EMAIL=your-kindle@kindle.com

# Sender email (usually same as SMTP_USER)
FROM_EMAIL=your-email@gmail.com
```

**Important Notes:**

- **Gmail Users**: You must use an [App Password](https://support.google.com/accounts/answer/185833), not your regular Gmail password
- **Kindle Email**: Find this in your Amazon account under "Manage Your Content and Devices" → "Preferences" → "Personal Document Settings"
- **Approved Senders**: Make sure to add your sending email address to your Kindle's approved email list in Amazon settings

### 4. Configure Claude Desktop

Add the server to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "send-to-kindle": {
      "command": "/path/to/send-to-kindle-mcp/venv/bin/python",
      "args": ["/path/to/send-to-kindle-mcp/server.py"],
      "env": {
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "your-email@gmail.com",
        "SMTP_PASSWORD": "your-app-password",
        "KINDLE_EMAIL": "your-kindle@kindle.com",
        "FROM_EMAIL": "your-email@gmail.com"
      }
    }
  }
}
```

Replace `/path/to/send-to-kindle-mcp` with the actual path to this directory.

### 5. Restart Claude Desktop

Quit and restart Claude Desktop for the changes to take effect.

## Usage

Once configured, you can ask Claude to send documents to your Kindle:

```
"Please send this research paper to my Kindle"
"Create a summary of this conversation and send it to my Kindle as 'Meeting Notes'"
"Convert this markdown document to EPUB and send to Kindle"
```

Claude will use the `send_to_kindle` tool to:
1. Convert your content to a properly formatted EPUB
2. Email it to your Kindle address
3. Confirm successful delivery

The document will appear in your Kindle library within a few minutes.

## Troubleshooting

### Email not sending

- Verify your SMTP credentials are correct
- For Gmail, ensure you're using an App Password, not your regular password
- Check that less secure app access is not required (modern Gmail uses App Passwords instead)

### Document not appearing on Kindle

- Verify your Kindle email address is correct
- Check your Amazon approved email list includes your sending address
- Look in your Amazon "Personal Documents" section to see if it was received
- Check your spam folder

### Import errors

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -e .
```

## Development

To run the server standalone for testing:

```bash
source venv/bin/activate
python server.py
```

## Security Notes

- Never commit your `.env` file or expose your credentials
- Use App Passwords for email services that support them
- Keep your Kindle approved sender list limited to trusted addresses

## License

MIT License - feel free to modify and distribute as needed.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.
