# /// script
# dependencies = [
#   "mcp",
# ]
# ///

import subprocess
import os
import shutil
import datetime
import time
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Camsnap Manager")

def run_executable_stream(args: list[str], is_snap: bool = False) -> str:
    camsnap_bin = shutil.which("camsnap") or "camsnap"
    
    try:
        # Esegui completamente isolato con subprocess.run
        result = subprocess.run(
            [camsnap_bin] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=45
        )
        
        clean_stdout = result.stdout.strip()
        clean_stderr = result.stderr.strip()
        
        if result.returncode == 0:
            return clean_stdout or "Operazione completata."
        else:
            return f"Errore {result.returncode}\nLOG: {clean_stderr}\nOUT: {clean_stdout}"
            
    except subprocess.TimeoutExpired:
        return "Errore: Timeout (45s) durante la comunicazione con la camera."
    except Exception as e:
        return f"Errore critico: {str(e)}"

@mcp.tool()
def list_cameras() -> str:
    """Elenca le telecamere configurate."""
    return run_executable_stream(["list"], is_snap=False)

@mcp.tool()
def capture_snap(camera_name: str) -> str:
    """Cattura un frame."""
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"
    
    res = run_executable_stream(["snap", camera_name, "--out", target_path], is_snap=True)
    
    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
        file_size = os.path.getsize(target_path)
        return f"Snapshot creato con successo: {target_path} ({file_size} bytes)"
    
    return f"Cattura fallita. Dettagli tecnici:\n{res}"

if __name__ == "__main__":
    mcp.run()