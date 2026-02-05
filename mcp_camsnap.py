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
    camsnap_bin = shutil.which("camsnap") or "camsnap"
    
    # Specifica il percorso assoluto della tua config
    # Sostituisci con il percorso reale che vedi facendo 'ls ~/.config/camsnap/config.yaml'
    config_path = os.path.expanduser("~/.config/camsnap/config.yaml")
    
    # Inseriamo il flag --config come primo argomento
    full_args = ["--config", config_path] + args

    try:
        result = subprocess.run(
            [camsnap_bin] + full_args,
            capture_output=True,
            text=True,
            timeout=45,
            # Passiamo l'ambiente attuale per mantenere le variabili di sistema
            env=os.environ.copy() 
        )
        
        # Se l'output è vuoto ma il comando è riuscito, segnaliamolo
        output = result.stdout.strip()
        if result.returncode == 0:
            return output if output else "Comando eseguito, ma l'output è vuoto. Verifica il file config."
        else:
            return f"Errore (Code {result.returncode}):\n{result.stderr}"
            
    except Exception as e:
        return f"Errore critico: {str(e)}"

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