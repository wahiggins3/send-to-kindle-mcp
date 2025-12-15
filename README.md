# Send to Kindle MCP Server

A Model Context Protocol (MCP) server that allows AI assistants to send documents directly to your Kindle e-reader. Convert text or markdown content into beautifully formatted EPUB files and deliver them instantly to your Kindle library.

## Deployment Options

This MCP server can be deployed in two ways:

- **🖥️ Local Installation**: Run on your machine with Claude Desktop (stdio transport)
- **☁️ Cloud Deployment**: Host on Google Cloud Run for access from anywhere (HTTP transport)
  - ✨ **New!** Works with Claude.ai web interface via custom connectors
  - 🌍 Accessible from any device with a browser
  - 💰 Scales to zero when idle (minimal cost)

> **Recommended:** Deploy to the cloud and connect via Claude.ai web for the best experience! See our comprehensive [Cloud Deployment Guide](DEPLOYMENT.md) for step-by-step instructions.

## Features

- 📚 Convert text and markdown to EPUB format
- 📧 Send documents directly to Kindle via email
- 📖 Automatic chapter creation from markdown headings (H1, H2, etc.)
- 🎨 Properly formatted with CSS styling for optimal reading
- ⚡ Fast and easy integration with Claude Desktop
- 🔒 Secure email configuration with environment variables
- 👤 Customizable author name via environment variable

## Prerequisites

### For Local Installation
- Python 3.10 or higher
- Claude Desktop application

### For Cloud Deployment
- Google Cloud Platform account (or see [DEPLOYMENT.md](DEPLOYMENT.md) for other options)
- Google Cloud SDK (gcloud CLI)

### For Both
- A Kindle e-reader or Kindle app
- An email account with SMTP access (Gmail recommended)
- Your Kindle email address (found in Amazon account settings)

## Installation

Choose your installation method:

- **For cloud deployment**: See the [Cloud Deployment Guide](DEPLOYMENT.md)
- **For local installation**: Continue below

### Local Installation

#### 1. Clone or download this repository

```bash
cd ~/path/to/your/projects
git clone <repository-url> send-to-kindle-mcp
cd send-to-kindle-mcp
```

#### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

#### 3. Configure your credentials

**Option A: Create a `.env` file (for local testing)**

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

# Author name (optional - defaults to "Claude" if not set)
AUTHOR_NAME=Your Name
```

**Note**: The `.env` file is useful for local testing (e.g., using `test_smtp.py`), but **Claude Desktop does NOT automatically load `.env` files**. You must also set these values in the Claude Desktop config file (see step 4).

**Important Notes:**

- **Gmail Users**: You must use an [App Password](https://support.google.com/accounts/answer/185833), not your regular Gmail password
- **Kindle Email**: Find this in your Amazon account under "Manage Your Content and Devices" → "Preferences" → "Personal Document Settings"
- **Approved Senders**: Make sure to add your sending email address to your Kindle's approved email list in Amazon settings

#### 4. Configure Claude Desktop

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
        "FROM_EMAIL": "your-email@gmail.com",
        "AUTHOR_NAME": "Your Name"
      }
    }
  }
}
```

**Replace the following:**
- `/path/to/send-to-kindle-mcp` with the actual path to this directory
- All placeholder values in the `env` section with your actual credentials

**Note**: If you created a `.env` file in step 3, you can copy those same values into the `env` section above. The values must be set here for Claude Desktop to use them.

#### 5. Restart Claude Desktop

Quit and restart Claude Desktop for the changes to take effect.

## Connecting to Claude.ai Web Interface (Beta)

Claude.ai now supports connecting to remote MCP servers via custom connectors (beta feature):

1. Go to **Claude.ai** → **Settings** → **Connectors**
2. Click **"Add custom connector"**
3. Enter your cloud server URL: `https://your-service-url.run.app/mcp`
4. Click **"Configure"** and follow the prompts
5. Your send-to-kindle MCP server will now be available in Claude.ai web!

This allows you to use the send-to-kindle feature directly from the Claude web interface, without needing Claude Desktop.

## Usage

Once configured (either in Claude Desktop or Claude.ai web), you can ask Claude to send documents to your Kindle:

```
"Please send this research paper to my Kindle"
"Create a summary of this conversation and send it to my Kindle as 'Meeting Notes'"
"Convert this markdown document to EPUB and send to Kindle"
```

Claude will use the `send_to_kindle` tool to:
1. Ask you for a title and author (if not provided)
2. Convert your content to a properly formatted EPUB with chapter navigation
3. Email it to your Kindle address
4. Confirm successful delivery

**Chapter Navigation**: The tool automatically detects markdown headings (H1, H2, etc.) and creates separate chapters for each major section. This makes it easy to navigate longer documents on your Kindle using the table of contents.

The document will appear in your Kindle library within a few minutes.

## Troubleshooting

### Viewing Error Logs

The server logs detailed information to help debug issues. To view logs in Claude Desktop:

**macOS**: 
- Open Console.app (Applications → Utilities → Console)
- Filter by "Claude" or search for "send-to-kindle"
- Look for log messages with timestamps

**Windows**:
- Check the Claude Desktop logs in `%APPDATA%\Claude\logs\`
- Or view logs in the Windows Event Viewer

The logs will show:
- Connection attempts to SMTP servers
- Authentication steps and errors
- Detailed error messages with troubleshooting hints
- Configuration validation issues

### Email not sending

- **Most common issue**: Environment variables not set in Claude Desktop config file. Remember: `.env` files are NOT automatically loaded by Claude Desktop. You must set all variables in the `claude_desktop_config.json` file.
- Verify your SMTP credentials are correct in the Claude Desktop config file
- For Gmail, ensure you're using an App Password, not your regular password
- Test your connection using `python test_smtp.py` to verify credentials work
- Check the logs (see above) for specific error messages
- Restart Claude Desktop after making config changes

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

### Testing SMTP Connection

Test your SMTP configuration independently of Claude Desktop:

```bash
source venv/bin/activate
python test_smtp.py
```

This will verify your credentials and connection work correctly before using with Claude Desktop.

### Running the Server Standalone

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
