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
        # Per la list: cattura stdout normalmente
        if not is_snap:
            result = subprocess.run(
                [camsnap_bin] + args,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip() or "Nessun output"
            else:
                return f"Errore {result.returncode}: {result.stderr}"
        
        # Per lo snap: lascia stderr libero (ffmpeg ne ha bisogno)
        else:
            process = subprocess.Popen(
                [camsnap_bin] + args,
                stdout=subprocess.PIPE,
                stderr=None,  # NON catturare stderr - lascialo libero
                text=True
            )
            
            stdout, _ = process.communicate(timeout=45)
            
            if process.returncode == 0:
                return stdout.strip() or "Snap completato"
            else:
                return f"Errore {process.returncode} - processo terminato"
            
    except subprocess.TimeoutExpired:
        if is_snap:
            process.kill()
        return "Errore: Timeout"
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
    
    # Attendi che il file sia scritto
    time.sleep(1)
    
    if os.path.exists(target_path):
        file_size = os.path.getsize(target_path)
        if file_size > 0:
            return f"✓ Snapshot: {target_path} ({file_size} bytes)"
        else:
            return f"✗ File creato ma vuoto"
    
    return f"✗ File non creato. Log: {res}"

if __name__ == "__main__":
    mcp.run()