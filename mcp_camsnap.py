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

def run_simple(args):
    """Esecuzione diretta: se funziona nel terminale, deve funzionare qui."""
    # Cerchiamo camsnap nel PATH ereditato
    camsnap_bin = shutil.which("camsnap")
    
    # Se non lo trova, proviamo a chiedere a 'which' (fallback estremo)
    if not camsnap_bin:
        try:
            camsnap_bin = subprocess.check_output(["which", "camsnap"], text=True).strip()
        except:
            camsnap_bin = "camsnap"

    try:
        # Usiamo la forma più semplice di esecuzione possibile
        result = subprocess.run(
            [camsnap_bin] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return result.stdout.strip() or "OK (Nessun output)"
        else:
            return f"Errore {result.returncode}: {result.stderr}"
    except Exception as e:
        return f"Errore critico: {str(e)}"

@mcp.tool()
def list_cameras() -> str:
    """Lista delle telecamere."""
    return run_simple(["list"])

@mcp.tool()
def capture_snap(camera_name: str) -> str:
    """Cattura un frame in /tmp."""
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"
    
    res = run_simple(["snap", camera_name, "--out", target_path])
    
    if os.path.exists(target_path):
        return f"Snapshot OK: {target_path}"
    return f"Fallito: {res}"

if __name__ == "__main__":
    mcp.run()