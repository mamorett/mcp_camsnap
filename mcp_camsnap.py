# /// script
# dependencies = [
#   "mcp",
# ]
# ///

import subprocess
import os
import datetime
import shutil
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Camsnap Manager")

def get_env():
    """Ricostruisce l'ambiente includendo i path di Brew in modo dinamico."""
    env = os.environ.copy()
    brew_paths = ["/home/linuxbrew/.linuxbrew/bin", "/opt/homebrew/bin", os.path.expanduser("~/.local/bin")]
    env["PATH"] = ":".join(brew_paths) + ":" + env.get("PATH", "")
    return env

def run_command(args: list[str], timeout: int = 40):
    """Esegue il comando gestendo i buffer per evitare il crash di FFmpeg."""
    env = get_env()
    camsnap_bin = shutil.which("camsnap", path=env["PATH"]) or "camsnap"
    
    try:
        # Usiamo subprocess.run con capture_output. 
        # Per evitare che i log di FFmpeg (stderr) intasino tutto, 
        # aumentiamo il timeout e leggiamo solo alla fine.
        result = subprocess.run(
            [camsnap_bin] + args,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout
        )
        return result
    except subprocess.TimeoutExpired as e:
        return e
    except Exception as e:
        return str(e)

@mcp.tool()
def list_cameras() -> str:
    """Elenca le telecamere configurate."""
    res = run_command(["list"])
    if isinstance(res, str): return res
    return res.stdout.strip() if res.returncode == 0 else f"Errore: {res.stderr}"

@mcp.tool()
def capture_snap(camera_name: str) -> str:
    """Cattura un frame dalla telecamera specificata."""
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"
    
    # Eseguiamo lo snap. Aumentiamo il timeout perché FFmpeg su RTSP può essere lento.
    res = run_command(["snap", camera_name, "--out", target_path], timeout=60)
    
    if os.path.exists(target_path):
        return f"Snapshot salvato: {target_path}"
    
    # Se il file non esiste, riportiamo l'errore per il debug
    if hasattr(res, 'stderr'):
        return f"Fallito. Errore FFmpeg:\n{res.stderr}"
    return f"Errore sconosciuto: {str(res)}"

if __name__ == "__main__":
    mcp.run()