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
    
    # Prepariamo un ambiente "headless" totale per FFmpeg
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    # Impediamo a FFmpeg di cercare interfacce grafiche o accelerazioni hardware 
    # che potrebbero essere bloccate dal sandbox dell'editor
    env["DISPLAY"] = "" 
    env["XDG_RUNTIME_DIR"] = "/tmp"

    try:
        # Per lo snap, isoliamo stderr ma non mandiamolo a DEVNULL, 
        # leggiamolo per capire PERCHÉ dà Errore 1.
        process = subprocess.Popen(
            [camsnap_bin] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        try:
            stdout, stderr = process.communicate(timeout=45)
        except subprocess.TimeoutExpired:
            process.kill()
            return "Errore: Timeout (45s) durante la comunicazione con la camera."
        
        clean_stdout = stdout.strip()
        clean_stderr = stderr.strip()
        
        if process.returncode == 0:
            return clean_stdout or "Operazione completata."
        else:
            # Qui catturiamo il vero motivo dell'Errore 1
            return f"Errore {process.returncode}\nLOG: {clean_stderr}\nOUT: {clean_stdout}"
            
    except Exception as e:
        return f"Errore critico: {str(e)}"

@mcp.tool()
def list_cameras() -> str:
    """Elenca le telecamere configurate."""
    return run_executable_stream(["list"], is_snap=False)

@mcp.tool()
def capture_snap(camera_name: str) -> str:
    """Cattura un frame (Headless Mode)."""
    # Timestamp univoco per evitare sovrascritture (Assioma rispettato)
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"
    
    res = run_executable_stream(["snap", camera_name, "--out", target_path], is_snap=True)
    
    # Controllo fisico sul file
    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
        return f"Snapshot creato con successo: {target_path}"
    
    return f"Cattura fallita. Dettagli tecnici:\n{res}"

if __name__ == "__main__":
    mcp.run()