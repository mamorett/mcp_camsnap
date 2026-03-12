import asyncio
import os
import shutil
import datetime
import subprocess
from mcp.server.fastmcp import FastMCP, Image

# Initialize FastMCP server
mcp = FastMCP("Camsnap Manager")

# Global config path from environment variable
CAMSNAP_CONFIG = os.environ.get("CAMSNAP_CONFIG")

def get_base_args() -> list[str]:
    """Returns the base arguments for camsnap, including config if set."""
    args = []
    if CAMSNAP_CONFIG:
        args.extend(["--config", CAMSNAP_CONFIG])
    return args

def run_camsnap_sync(args: list[str]) -> str:
    """
    Executes a camsnap command synchronously and returns the output.
    """
    camsnap_bin = shutil.which("camsnap") or "camsnap"
    full_args = get_base_args() + args
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    try:
        process = subprocess.Popen(
            [camsnap_bin] + full_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        stdout, stderr = process.communicate(timeout=30)
        clean_stdout = stdout.strip()
        if process.returncode == 0:
            if not clean_stdout and stderr:
                return f"Output (from stderr): {stderr.strip()}"
            return clean_stdout or "Command executed, but output was empty."
        else:
            return f"Error {process.returncode}\nLOG: {stderr}\nOUT: {stdout}"
    except subprocess.TimeoutExpired:
        process.kill()
        return "Error: Timeout."
    except Exception as e:
        return f"Critical error: {str(e)}"

@mcp.tool()
def list_cameras() -> str:
    """
    Lists all cameras configured in the camsnap config file.
    """
    return run_camsnap_sync(["list"])

@mcp.tool()
async def capture_snap(camera_name: str) -> str:
    """
    Captures a frame from a camera and saves it to a temporary file.
    Returns the path to the saved image.
    """
    camsnap_bin = shutil.which("camsnap") or "camsnap"
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_path = f"/tmp/snap_{camera_name}_{now}.jpg"
    
    cmd_args = get_base_args() + ["snap", camera_name, "--out", target_path]

    try:
        process = await asyncio.create_subprocess_exec(
            camsnap_bin, *cmd_args,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await asyncio.wait_for(process.wait(), timeout=45)

        if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            return f"Snapshot saved successfully: {target_path}"
        else:
            return f"Error: Camsnap finished but the file {target_path} is missing or empty."
            
    except asyncio.TimeoutExpired:
        return f"Error: Timeout while taking snapshot of '{camera_name}'."
    except Exception as e:
        return f"Async critical error: {str(e)}"

@mcp.tool()
async def get_camera_snapshot_as_image(camera_name: str) -> Image:
    """
    Captures a frame from a camera and returns it as an inline image directly to the client.
    """
    camsnap_bin = shutil.which("camsnap") or "camsnap"
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_path = f"/tmp/snap_img_{camera_name}_{now}.jpg"
    
    cmd_args = get_base_args() + ["snap", camera_name, "--out", target_path]

    try:
        process = await asyncio.create_subprocess_exec(
            camsnap_bin, *cmd_args,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await asyncio.wait_for(process.wait(), timeout=45)

        if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            with open(target_path, "rb") as f:
                data = f.read()
            # Try to remove the file after reading since we return the binary
            try:
                os.remove(target_path)
            except OSError:
                pass
            return Image(data=data, format="jpeg")
        else:
            raise RuntimeError(f"Error: Camsnap finished but the file {target_path} is missing or empty.")
            
    except asyncio.TimeoutExpired:
        raise RuntimeError(f"Error: Timeout while taking snapshot of '{camera_name}'.")
    except Exception as e:
        raise RuntimeError(f"Async critical error: {str(e)}")

@mcp.resource("file:///tmp/vision_snap_{camera_name}.jpg")
def get_snap_resource(camera_name: str) -> bytes:
    """
    Exposes snapshots as MCP resources.
    """
    path = f"/tmp/vision_snap_{camera_name}.jpg"
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return b""

def main():
    mcp.run()

if __name__ == "__main__":
    main()
