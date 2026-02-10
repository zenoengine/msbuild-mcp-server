import re
import subprocess
import sys
import os
import tempfile
from fastmcp import FastMCP
from vswhere import get_latest_path

if sys.platform == "win32":
    import winreg

mcp = FastMCP("MSBuild MCP Server")


def _get_build_environment():
    """
    Reconstruct the full system environment from the Windows registry.

    MCP stdio clients typically pass only a limited set of environment variables
    (PATH, TEMP, APPDATA, etc.), which causes MSBuild's .NET SDK resolution to
    fail or hang. This function reads the complete environment from the registry
    so that MSBuild can locate all required SDKs and tools.
    """
    if sys.platform != "win32":
        return None

    env = {}

    registry_keys = [
        (winreg.HKEY_LOCAL_MACHINE,
         r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
        (winreg.HKEY_CURRENT_USER,
         r"Environment"),
    ]

    for root_key, sub_key in registry_keys:
        try:
            with winreg.OpenKey(root_key, sub_key) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        i += 1
                        if name.upper() == "PATH":
                            existing = env.get("PATH", "")
                            env["PATH"] = (existing + ";" + value) if existing else value
                        else:
                            env[name] = value
                    except OSError:
                        break
        except OSError:
            continue

    if not env:
        return None

    result = os.environ.copy()
    result.update(env)

    def _expand(value, env_dict):
        upper_dict = {k.upper(): v for k, v in env_dict.items()}

        def _replace(m):
            var_name = m.group(1).upper()
            return upper_dict.get(var_name, m.group(0))

        return re.sub(r'%([^%]+)%', _replace, value)

    for _ in range(3):
        expanded = {k: _expand(v, result) for k, v in result.items()}
        if expanded == result:
            break
        result = expanded

    return result


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
    restore: bool = False,
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
        project_path,
        f"/p:Configuration={configuration}",
        f"/p:Platform={platform}",
        f"/verbosity:{verbosity}",
    ]

    if max_cpu_count:
        cmd.append(f"/maxcpucount:{max_cpu_count}")
    else:
        cmd.append("/m")

    cmd.append("/nodeReuse:false")

    if restore:
        cmd.append("/restore")

    if additional_args:
        cmd.extend(additional_args.split())

    build_env = _get_build_environment()

    stdout_file = tempfile.NamedTemporaryFile(
        mode='w+', suffix='_msbuild_stdout.txt', delete=False, encoding='utf-8'
    )
    stderr_file = tempfile.NamedTemporaryFile(
        mode='w+', suffix='_msbuild_stderr.txt', delete=False, encoding='utf-8'
    )

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=stdout_file,
            stderr=stderr_file,
            env=build_env,
        )

        proc.wait()
        stdout_file.close()
        stderr_file.close()

        with open(stdout_file.name, 'r', encoding='utf-8', errors='replace') as f:
            stdout = f.read()
        with open(stderr_file.name, 'r', encoding='utf-8', errors='replace') as f:
            stderr = f.read()

        if proc.returncode == 0:
            return f"Build succeeded."
        else:
            error_lines_stdout = [line for line in stdout.splitlines() if "error" in line.lower()]
            error_lines_stderr = [line for line in stderr.splitlines() if "error" in line.lower()]
            filtered_errors = "\n".join(error_lines_stdout + error_lines_stderr)
            return f"Build failed with errors.\nFiltered Errors:\n{filtered_errors}\nFull Output:\n{stdout}\nErrors:\n{stderr}"
    except FileNotFoundError:
        return "MSBuild executable not found. Ensure MSBuild is installed and added to the PATH."
    finally:
        for path in [stdout_file.name, stderr_file.name]:
            try:
                os.unlink(path)
            except OSError:
                pass


def main():
    """Entry point for the msbuild-mcp-server CLI."""
    mcp.run()


if __name__ == "__main__":
    main()
