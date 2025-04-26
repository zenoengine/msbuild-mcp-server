# MSBuild MCP Server

A lightweight MCP (Model Context Protocol) server for automating MSBuild projects and solutions builds. It dynamically locates MSBuild using the `vswhere` Python package and provides customizable build configuration options.

## Features

- **Dynamic MSBuild Discovery**: Automatically detects the MSBuild executable using `vswhere`, ensuring compatibility with various Visual Studio installations.
- **Customizable Build Settings**: Easily configure build options such as configuration, platform, verbosity level, parallel build CPU count, NuGet restore, and additional command-line arguments.
- **Clear Error Reporting**: Filters and presents concise, relevant error messages upon build failures.
- **MCP Client Compatibility**: Integrates seamlessly with MCP clients, including VSCode, Cursor, Windsurf, and more.
- **Cross-Language Support**: Works with MSBuild-compatible projects (.sln, .csproj, .vcxproj).

## Prerequisites

Ensure the following prerequisites are installed:

- Python 3.11 or higher
- Visual Studio or Visual Studio Build Tools (for MSBuild)
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) (recommended)

## MCP Client Setup

Use the same configuration snippet for all MCP clients:

```json
{
  "mcpServers": {
    "msbuild-mcp-server": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "<path/to/cloned/msbuild-mcp-server>",
        "run",
        "server.py"
      ]
    }
  }
}
```

Place this snippet in your client configuration file:
- **VSCode**: `.vscode/settings.json`
- **Cursor**: `~/.cursor/mcp.json` or `<project-root>/.cursor/mcp.json`
- **Windsurf**: `~/.codeium/windsurf/mcp_config.json`

## License

This project is licensed under the MIT License.

