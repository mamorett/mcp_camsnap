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

def run_executable(args: list[str]) -> str:
    # Invece di ricostruire il PATH, usiamo quello che OpenCode eredita, 
    # ma cerchiamo il binario in modo dinamico.
    camsnap_bin = shutil.which("camsnap") or "camsnap"

    try:
        # Usiamo subprocess.run che è più atomico e gestisce meglio i buffer
        # Reindirizziamo stderr su stdout per vedere tutto in un unico flusso
        result = subprocess.run(
            [camsnap_bin] + args,
            capture_output=True,
            text=True,
            timeout=45 # FFmpeg può essere lento a negoziare l'RTSP
        )
        
        if result.returncode == 0:
            return result.stdout.strip() or "Successo."
        else:
            return f"Errore (Code {result.returncode}):\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
            
    except subprocess.TimeoutExpired as e:
        # Se va in timeout, restituiamo quello che ha catturato finora
        stdout = e.stdout.decode() if e.stdout else ""
        stderr = e.stderr.decode() if e.stderr else ""
        return f"Errore: Timeout scaduto.\nParziale STDOUT: {stdout}\nParziale STDERR: {stderr}"
    except Exception as e:
        return f"Errore imprevisto: {str(e)}"

@mcp.tool()
def list_cameras() -> str:
    """Elenca le telecamere configurate."""
    return run_executable(["list"])

@mcp.tool()
def capture_snap(camera_name: str) -> str:
    """Cattura un frame e lo salva in /tmp."""
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"
    
    # Eseguiamo il comando
    res = run_executable(["snap", camera_name, "--out", target_path])
    
    if os.path.exists(target_path):
        return f"Snapshot creato: {target_path}"
    return f"Fallito: {res}"

@mcp.tool()
def check_status() -> str:
    """Diagnostica lo stato del sistema."""
    return run_executable(["doctor", "--probe"])

if __name__ == "__main__":
    mcp.run()