# MSBuild MCP Server

A lightweight MCP (Model Context Protocol) server for automating MSBuild projects and solutions builds. It dynamically locates MSBuild and provides customizable build configuration options.

## Features

- **Dynamic MSBuild Discovery**: Automatically detects the MSBuild executable, ensuring compatibility with various Visual Studio installations.
- **Customizable Build Settings**: Easily configure build options such as configuration, platform, verbosity level, parallel build CPU count, NuGet restore, and additional command-line arguments through LLM-driven tool invocation.
- **Clear Error Reporting**: Filters and presents concise, relevant error messages upon build failures.
- **MCP Client Compatibility**: Supports seamless integration with popular MCP clients such as VSCode, Cursor, Windsurf, and more. Configuration snippets for these clients are provided in the documentation.
- **Cross-Language Support**: Supports MSBuild-compatible projects, including .sln, .csproj, and .vcxproj files, enabling builds for languages like C#, C++, and more across Windows platforms.

## Prerequisites

Ensure the following prerequisites are installed:

- Python 3.11 or higher
- Visual Studio or Visual Studio Build Tools (for MSBuild)
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) (recommended)

## Registering the MCP Server

Ensure `uv` is installed.

In the MCP settings of your AI tools (e.g., Cursor, Windsurf, Claude Desktop, etc.), add the following configuration:

```json
{
  "mcpServers": {
    "msbuild-mcp-server": {
      "command": "uvx",
      "args": [
        "msbuild-mcp-server@latest"
      ]
    }
  }
}
```

Place this snippet in your client configuration file:
- [**VSCode**](https://code.visualstudio.com/docs/copilot/chat/mcp-servers): `.vscode/mcp.json`
- **Cursor**: `~/.cursor/mcp.json` or `<project-root>/.cursor/mcp.json`
- **Windsurf**: `~/.codeium/windsurf/mcp_config.json`

Restart your tool to ensure that the `msbuild-mcp-server` and its provided tools are properly registered.

# Agent Prompt Examples

AI agents can trigger builds using natural language like:

- **Basic Project Build**  
  > *"Build this solution at `C:/Path/To/Project.sln` using `Release|x64`."*

- **Unreal Engine Build**  
  > *"Build the solution located at `C:/Projects/MyGame/MyGame.sln` using `Development Editor|Win64`."*

## License

This project is licensed under the MIT License.

