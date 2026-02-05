# /// script
# dependencies = [
#   "mcp",
# ]
# ///

import subprocess
import os
import datetime
from typing import Optional
from mcp.server.fastmcp import FastMCP

# Inizializza il server MCP
mcp = FastMCP("Camsnap Manager")

def get_timestamped_path(camera_name: str, extension: str) -> str:
    """Genera un percorso univoco in /tmp: /tmp/cam_cucina_20231027_153045.jpg"""
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cam_{camera_name}_{now}.{extension}"
    return os.path.join("/tmp", filename)

def run_camsnap(args: list[str]) -> str:
    """Esegue il comando camsnap e cattura l'output."""
    try:
        # Assicuriamoci che l'ambiente abbia il PATH corretto se necessario
        result = subprocess.run(
            ["camsnap"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Errore camsnap: {e.stderr}"
    except FileNotFoundError:
        return "Errore: comando 'camsnap' non trovato nel sistema."

@mcp.tool()
def list_cameras() -> str:
    """Elenca tutte le telecamere configurate."""
    return run_camsnap(["list"])

@mcp.tool()
def capture_snap(camera_name: str) -> str:
    """
    Cattura un frame da una telecamera. 
    Il file viene salvato automaticamente in /tmp con timestamp.
    """
    target_path = get_timestamped_path(camera_name, "jpg")
    output = run_camsnap(["snap", camera_name, "--out", target_path])
    
    if "Errore" in output:
        return output
    return f"Snapshot catturato con successo.\nPercorso: {target_path}"

@mcp.tool()
def record_clip(camera_name: str, duration: str = "5s") -> str:
    """
    Registra un clip video (senza audio).
    Esempio durata: '5s', '10s'. Salvato in /tmp con timestamp.
    """
    target_path = get_timestamped_path(camera_name, "mp4")
    output = run_camsnap(["clip", camera_name, "--dur", duration, "--no-audio", "--out", target_path])
    
    if "Errore" in output:
        return output
    return f"Clip registrata ({duration}).\nPercorso: {target_path}"

@mcp.tool()
def check_status() -> str:
    """Verifica lo stato di ffmpeg e delle telecamere."""
    return run_camsnap(["doctor", "--probe"])

if __name__ == "__main__":
    mcp.run()
