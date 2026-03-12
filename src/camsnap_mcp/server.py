import asyncio
import os
import shutil
import datetime
import subprocess
from mcp.server.fastmcp import FastMCP, Image
from PIL import Image as PILImage

import tempfile

# Initialize FastMCP server
mcp = FastMCP("Camsnap Manager")

# Global config path from environment variable
CAMSNAP_CONFIG = os.environ.get("CAMSNAP_CONFIG")

def get_temp_dir() -> str:
    """
    Returns a safe temporary directory that is accessible by the MCP server sandbox.
    Uses CAMSNAP_TMP_DIR env var if set, otherwise defaults to ~/.camsnap/tmp.
    """
    tmp_dir = os.environ.get("CAMSNAP_TMP_DIR", os.path.expanduser("~/.camsnap/tmp"))
    os.makedirs(tmp_dir, exist_ok=True)
    return tmp_dir

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

RESIZE_MAX = os.environ.get("CAMSNAP_RESIZE_MAX")

@mcp.tool()
async def capture_snap(camera_name: str) -> Image:
    camsnap_bin = shutil.which("camsnap") or "camsnap"
    
    with tempfile.NamedTemporaryFile(dir=get_temp_dir(), prefix="snap_img_", suffix=".jpg", delete=False) as tmp_file:
        target_path = tmp_file.name

    cmd_args = get_base_args() + ["snap", camera_name, "--out", target_path]

    try:
        process = await asyncio.create_subprocess_exec(
            camsnap_bin, *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=45)

        if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            if RESIZE_MAX:
                try:
                    max_size = int(RESIZE_MAX)
                    with PILImage.open(target_path) as img:
                        img.thumbnail((max_size, max_size))
                        
                        buffer = io.BytesIO()
                        # quality=85 è un ottimo compromesso tra peso e dettaglio
                        img.save(buffer, format="JPEG", quality=85, optimize=True)
                        data = buffer.getvalue()
                except Exception as resize_err:
                    # Se il resize fallisce, mandiamo l'originale come fallback
                    with open(target_path, "rb") as f:
                        data = f.read()
            else:
                # Nessuna variabile settata: mandiamo il file originale
                with open(target_path, "rb") as f:
                    data = f.read()

            try:
                os.remove(target_path)
            except OSError:
                pass
                
            return Image(data=data, format="jpeg")
        else:
            error_output = stderr.decode().strip()
            raise RuntimeError(f"File vuoto. Stderr: {error_output}")
            
    except Exception as e:
        raise RuntimeError(f"Errore durante la cattura: {str(e)}")

@mcp.tool()
async def capture_clip(camera_name: str, duration: int = 10) -> str:
    """
    Records a short MP4 video clip from a camera and saves it to a temporary file.
    Returns the absolute path to the saved MP4 file.
    """
    camsnap_bin = shutil.which("camsnap") or "camsnap"
    
    with tempfile.NamedTemporaryFile(dir=get_temp_dir(), prefix="clip_", suffix=".mp4", delete=False) as tmp_file:
        target_path = tmp_file.name
    
    cmd_args = get_base_args() + ["clip", camera_name, "--dur", f"{duration}s", "--out", target_path]

    try:
        process = await asyncio.create_subprocess_exec(
            camsnap_bin, *cmd_args,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        # Add 15 seconds buffer to the requested duration for timeout
        await asyncio.wait_for(process.wait(), timeout=duration + 15)

        if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            return f"Clip saved successfully: {target_path}"
        else:
            raise RuntimeError(f"Error: Camsnap finished but the file {target_path} is missing or empty.")
            
    except asyncio.TimeoutError:
        raise RuntimeError(f"Error: Timeout while recording clip of '{camera_name}' (duration: {duration}s).")
    except Exception as e:
        raise RuntimeError(f"Async critical error: {str(e)}")


def main():
    mcp.run()

if __name__ == "__main__":
    main()