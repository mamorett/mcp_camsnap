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

def get_enhanced_env():
    """Ricostruisce un ambiente che include i percorsi comuni di Linuxbrew e local bin."""
    env = os.environ.copy()
    
    # Percorsi probabili per Linuxbrew e installazioni locali
    extra_paths = [
        os.path.expanduser("~/.local/bin"),
        "/home/linuxbrew/.linuxbrew/bin",
        "/opt/homebrew/bin",
    ]
    
    current_path = env.get("PATH", "")
    # Uniamo i percorsi extra a quello attuale, filtrando quelli che non esistono
    valid_extras = [p for p in extra_paths if os.path.isdir(p)]
    env["PATH"] = ":".join(valid_extras + [current_path])
    
    return env

def run_executable(args: list[str]) -> str:
    env = get_enhanced_env()
    
    # Cerchiamo il binario nel PATH aggiornato
    camsnap_bin = shutil.which("camsnap", path=env["PATH"])
    
    if not camsnap_bin:
        return "Errore: comando 'camsnap' non trovato. Assicurati che sia installato e nel PATH."

    try:
        process = subprocess.Popen(
            [camsnap_bin] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        stdout, stderr = process.communicate(timeout=30)
        
        if process.returncode == 0:
            return stdout.strip() or "Operazione completata."
        else:
            # Uniamo stdout e stderr per dare all'AI più contesto sul fallimento
            return f"Errore (Codice {process.returncode}):\n{stderr}\n{stdout}"
            
    except subprocess.TimeoutExpired:
        process.kill()
        return "Errore: Il processo ha superato il timeout di 30 secondi."
    except Exception as e:
        return f"Errore critico: {str(e)}"

@mcp.tool()
def list_cameras() -> str:
    """Elenca le telecamere configurate in camsnap."""
    return run_executable(["list"])

@mcp.tool()
def capture_snap(camera_name: str) -> str:
    """Cattura un frame e lo salva in /tmp con timestamp."""
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"
    result = run_executable(["snap", camera_name, "--out", target_path])
    
    if "Errore" in result:
        return result
    return f"Snapshot salvato con successo: {target_path}"

@mcp.tool()
def check_status() -> str:
    """Esegue la diagnostica di camsnap (FFmpeg, connettività, config)."""
    return run_executable(["doctor", "--probe"])

if __name__ == "__main__":
    mcp.run()