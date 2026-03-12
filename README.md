# camsnap-mcp

An MCP (Model Context Protocol) server for **camsnap** — control and analyze your IP/RTSP cameras directly from Claude Desktop, Cursor, or any MCP-compatible client.

> **Note:** This MCP server is a wrapper around the [camsnap](https://github.com/steipete/camsnap) project.

---

## Repository Structure

```
camsnap-mcp/
├── pyproject.toml
└── src/
    └── camsnap_mcp/
        ├── __init__.py
        └── server.py
```

---

## Prerequisites

Before using this MCP server, you must have `camsnap` installed and configured on your system.

1. **Install camsnap**: Follow the instructions at [steipete/camsnap](https://github.com/steipete/camsnap) to install the binary and its dependencies (like FFmpeg).
2. **Configure cameras**: Ensure you have a valid configuration file (usually `~/.camsnap.yaml`). You can verify your setup by running `camsnap list` in your terminal.

---

## Installation

Add the following to your MCP client configuration (e.g., `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "camsnap": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/mamorett/camsnap-mcp",
        "camsnap-mcp"
      ]
    }
  }
}
```

> `uvx` will automatically download and isolate the Python server. No manual `pip install` required.

---

## Available Tools

This MCP server exposes the following tools:

| Tool | Description |
|---|---|
| `list_cameras` | Lists all cameras configured in your `~/.camsnap.yaml` file. |
| `capture_snap` | Captures a frame from a camera and saves it to a file in `/tmp`. Returns the file path. |

---

## Local Development

If you want to run or modify the server locally:

```bash
git clone https://github.com/mamorett/camsnap-mcp
cd camsnap-mcp
pip install -e "."
camsnap-mcp
```
