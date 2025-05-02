import subprocess
import os
from fastmcp import FastMCP
from vswhere import get_latest_path

# Create MCP server instance
mcp = FastMCP("MSBuild MCP Server")

# Replace the find_msbuild function to use the vswhere Python package
# and retrieve the latest MSBuild path dynamically.
def find_msbuild():
    """
    Use the vswhere Python package to locate the MSBuild executable.
    Returns the path to MSBuild if found, otherwise raises an exception.
    """
    msbuild_installation_path = get_latest_path(products='*')
    if not msbuild_installation_path:
        raise FileNotFoundError("MSBuild executable not found. Ensure Visual Studio is installed.")

    msbuild_path = os.path.join(msbuild_installation_path, "MSBuild", "Current", "Bin", "MSBuild.exe")
    if not os.path.exists(msbuild_path):
        raise FileNotFoundError(f"MSBuild executable not found at expected path: {msbuild_path}")

    return msbuild_path

@mcp.tool()
def build_msbuild_project(
    project_path: str,
    configuration: str = "Debug",
    platform: str = "x64",
    verbosity: str = "minimal",
    max_cpu_count: int = None,
    restore: bool = True,
    additional_args: str = ""
) -> str:
    """
    Build an MSBuild project or solution (.sln, .csproj, .vcxproj) file using MSBuild.

    This tool dynamically locates the MSBuild executable using the vswhere Python package.
    It supports flexible build configurations, including verbosity, platform, and additional arguments.

    Parameters:
    - project_path: Path to the project or solution file to build.
    - configuration: Build configuration (e.g., Debug, Release).
    - platform: Target platform (e.g., x86, x64).
    - verbosity: MSBuild output verbosity (quiet, minimal, normal, detailed, diagnostic).
    - max_cpu_count: Maximum number of CPUs for parallel build (None for default).
    - restore: Whether to perform NuGet restore before build.
    - additional_args: Additional MSBuild command-line arguments.

    Returns:
    - A string indicating the build result, including success or filtered error messages.

    Use this tool to automate the build process for MSBuild projects, ensuring compatibility with various configurations and environments.
    """
    msbuild = find_msbuild()
    cmd = [
        msbuild,
        project_path,  # Updated from sln_path to project_path
        f"/p:Configuration={configuration}",
        f"/p:Platform={platform}",
        f"/verbosity:{verbosity}"
    ]

    if max_cpu_count:
        cmd.append(f"/maxcpucount:{max_cpu_count}")
    else:
        cmd.append("/m")  # Default parallel build

    if restore:
        cmd.append("/restore")

    if additional_args:
        cmd.extend(additional_args.split())

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # Capture stderr separately
            text=True,
            encoding="utf-8"
        )


        if result.returncode == 0:
            return f"Build succeeded."
        else:
            # Filter error messages from both stdout and stderr
            error_lines_stdout = [line for line in result.stdout.splitlines() if "error" in line.lower()]
            error_lines_stderr = [line for line in result.stderr.splitlines() if "error" in line.lower()]
            filtered_errors = "\n".join(error_lines_stdout + error_lines_stderr)
            return f"Build failed with errors.\nFiltered Errors:\n{filtered_errors}\nFull Output:\n{result.stdout}\nErrors:\n{result.stderr}"
    except FileNotFoundError:
        return "MSBuild executable not found. Ensure MSBuild is installed and added to the PATH."

if __name__ == "__main__":
    # Run the server using stdio protocol
    mcp.run()