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
2. **Configure cameras**: Ensure you have a valid configuration file. By default, `camsnap` looks for it in `$XDG_CONFIG_HOME/camsnap/config.yaml` or `~/.camsnap.yaml`. You can verify your setup by running `camsnap list` in your terminal.

### Custom Configuration & Temp Paths

- **`CAMSNAP_CONFIG`**: If your configuration file is in a non-standard location, you can specify it using this environment variable.
- **`CAMSNAP_TMP_DIR`**: By default, MCP saves local files (snapshots, clips) to `~/.camsnap/tmp`. Use this to override the path if your MCP client runs in a restricted sandbox.
- **`CAMSNAP_RESIZE_MAX`**: Set this to a pixel value (e.g., `1024` or `768`) to automatically resize captured snapshots. This is useful for reducing token usage in LLM prompts while maintaining enough detail for analysis. If not set, the original image size is returned.

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
        "git+https://github.com/mamorett/mcp_camsnap.git",
        "mcp-camsnap"
      ],
      "env": {
        "CAMSNAP_CONFIG": "/path/to/your/camsnap.yaml",
        "CAMSNAP_TMP_DIR": "/path/to/a/safe/tmp/dir",
        "CAMSNAP_RESIZE_MAX": "1024"
      }
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
| `capture_snap` | Captures a frame from a camera and returns it inline directly to the client as an image. |
| `capture_clip` | Records a short MP4 video clip from a camera for a specified duration to `~/.camsnap/tmp` and returns the absolute file path. |

---

## Local Development

If you want to run or modify the server locally:

```bash
git clone https://github.com/mamorett/mcp_camsnap
cd mcp_camsnap
pip install -e "."
mcp-camsnap
```
