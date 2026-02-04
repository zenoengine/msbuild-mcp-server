import subprocess
import os
from fastmcp import FastMCP
from vswhere import get_latest_path
import xml.etree.ElementTree as ET
import json
from typing import Annotated
from pydantic import Field

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


def get_msbuild_configurations_and_platforms(project_path: str):
    """
    Extract available configurations and platforms from a given MSBuild project or solution file.
    Returns (configurations, platforms) as lists.
    """
    configs = set()
    plats = set()
    if project_path.endswith('.sln'):
        # Parse .sln file as text directly
        with open(project_path, encoding='utf-8') as f:
            for line in f:
                if 'GlobalSection(SolutionConfigurationPlatforms)' in line:
                    for config_line in f:
                        if 'EndGlobalSection' in config_line:
                            break
                        if '=' in config_line:
                            configplat = config_line.split('=')[0].strip()
                            if '|' in configplat:
                                config, plat = configplat.split('|', 1)
                                configs.add(config)
                                plats.add(plat)
    else:
        # Parse .csproj/.vcxproj files as XML
        try:
            tree = ET.parse(project_path)
            root = tree.getroot()
            ns = {'msbuild': 'http://schemas.microsoft.com/developer/msbuild/2003'}
            for pg in root.findall('.//msbuild:PropertyGroup', ns):
                cond = pg.attrib.get('Condition', '')
                if 'Configuration' in cond and 'Platform' in cond:
                    # Example: ' '$(Configuration)|$(Platform)' == 'Debug|x64' '
                    import re
                    m = re.search(r"'\$\(Configuration\)\|\$\(Platform\)'\s*==\s*'([^|]+)\|([^']+)'", cond)
                    if m:
                        configs.add(m.group(1))
                        plats.add(m.group(2))
        except Exception:
            pass
    return list(configs), list(plats)


@mcp.tool(
    name="build_msbuild_project",
    description="Build an MSBuild project or solution (.sln, .csproj, .vcxproj) file using MSBuild.",
    tags={"msbuild", "build", "visualstudio"}
)
def build_msbuild_project(
    project_path: Annotated[str, Field(description="Absolute path to the project or solution file to build.")],
    configuration: Annotated[str, Field(description="Build configuration (e.g., Debug, Release).")],
    platform: Annotated[str, Field(description="Target platform (e.g., x86, x64).")],
    verbosity: Annotated[str, Field(description="MSBuild output verbosity (quiet, minimal, normal, detailed, diagnostic).")]="minimal",
    max_cpu_count: Annotated[int, Field(description="Maximum number of CPUs for parallel build (default: None, uses automatic parallel build).")]=None,
    restore: Annotated[bool, Field(description="Whether to perform NuGet restore before build. Default is True.")]=True,
    additional_args: Annotated[str, Field(description="Additional MSBuild command-line arguments (as a string, separated by spaces).")]=""
) -> str:
    """
    Build an MSBuild project or solution (.sln, .csproj, .vcxproj) file using MSBuild

    Parameters:
    - project_path: Absolute path to the project or solution file to build.
    - configuration: Build configuration (e.g., Debug, Release). Default is "Debug".
    - platform: Target platform (e.g., x86, x64). Default is "x64".
    - verbosity: MSBuild output verbosity (quiet, minimal, normal, detailed, diagnostic). Default is "minimal".
    - max_cpu_count: Maximum number of CPUs for parallel build (default: None, if not specified, uses automatic parallel build).
    - restore: Whether to perform NuGet restore before build. Default is True.
    - additional_args: Additional MSBuild command-line arguments (as a string, separated by spaces). Default is "".

    Returns:
    - A string indicating the build result, including success or filtered error messages.

    This tool can be used to automate MSBuild project builds in various environments.
    """
    msbuild = find_msbuild()
    
    if not os.path.isfile(project_path):
        return (
            f"The specified project_path does not exist or is not a file: {project_path}\n"
            "Please provide the absolute path to the project or solution file to build."
        )

    # If configuration or platform is not specified, return the available options
    configs, plats = get_msbuild_configurations_and_platforms(project_path)
    if not configuration or not platform:
        if not configs or not plats:
            return "Could not extract available configurations or platforms from the project file. Please specify them manually."
        return json.dumps({
            "message": "Please select a configuration and platform from the available options.",
            "available_configurations": configs,
            "available_platforms": plats
        }, ensure_ascii=False)
    # If the provided configuration or platform is not in the supported list, return a message
    if configs and configuration not in configs:
        return json.dumps({
            "message": f"The configuration '{configuration}' is not supported by this project. Please select from the available options.",
            "available_configurations": configs
        }, ensure_ascii=False)
    if plats and platform not in plats:
        return json.dumps({
            "message": f"The platform '{platform}' is not supported by this project. Please select from the available options.",
            "available_platforms": plats
        }, ensure_ascii=False)

    cmd = [
        msbuild,
        project_path,
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
            return f"Build failed with errors.\nFiltered Errors:\n{filtered_errors}"
    except FileNotFoundError:
        return "MSBuild executable not found. Ensure MSBuild is installed and added to the PATH."

def main():
    """Entry point for the msbuild-mcp-server CLI."""
    mcp.run()

if __name__ == "__main__":
    main()