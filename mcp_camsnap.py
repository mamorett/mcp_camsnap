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
    
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["DISPLAY"] = "" 
    env["XDG_RUNTIME_DIR"] = "/tmp"
    
    # OPZIONI FFMPEG per connessioni RTSP più veloci/stabili
    env["FFREPORT"] = "file=/tmp/ffmpeg_report.log:level=32"

    try:
        process = subprocess.Popen(
            [camsnap_bin] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        try:
            # TIMEOUT AUMENTATO: 60s invece di 45s per RTSP lenti
            stdout, stderr = process.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            return "Errore: Timeout (60s) - la camera non risponde abbastanza velocemente"
        
        clean_stdout = stdout.strip()
        clean_stderr = stderr.strip()
        
        if process.returncode == 0:
            return clean_stdout or "Operazione completata."
        else:
            return f"Errore {process.returncode}\nSTDERR:\n{clean_stderr}\n\nSTDOUT:\n{clean_stdout}"
            
    except Exception as e:
        return f"Errore critico: {str(e)}"

@mcp.tool()
def list_cameras() -> str:
    """Elenca le telecamere configurate."""
    return run_executable_stream(["list"], is_snap=False)

@mcp.tool()
def capture_snap(camera_name: str, timeout_override: int = 30) -> str:
    """
    Cattura un frame (Headless Mode).
    
    Args:
        camera_name: Nome della camera
        timeout_override: Timeout in secondi per lo snap (default 30)
    """
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"
    
    # Aggiungi opzioni di timeout per camsnap/ffmpeg
    args = ["snap", camera_name, "--out", target_path, "--timeout", str(timeout_override)]
    
    res = run_executable_stream(args, is_snap=True)
    
    # Aspetta che il file sia scritto completamente
    time.sleep(0.5)
    
    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
        file_size = os.path.getsize(target_path)
        return f"Snapshot creato con successo: {target_path} (dimensione: {file_size} bytes)"
    
    return f"Cattura fallita. Dettagli tecnici:\n{res}"

@mcp.tool()
def capture_snap_fast(camera_name: str) -> str:
    """
    Cattura veloce con opzioni RTSP ottimizzate per camere lente.
    Usa questo se capture_snap normale fallisce con 'signal: killed'.
    """
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"
    
    # Opzioni aggressive per RTSP
    args = [
        "snap", camera_name, 
        "--out", target_path,
        "--timeout", "45",
        "--rtsp-transport", "tcp",  # TCP invece di UDP (più affidabile)
        "--no-audio"  # Ignora audio per velocizzare
    ]
    
    res = run_executable_stream(args, is_snap=True)
    
    time.sleep(0.5)
    
    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
        file_size = os.path.getsize(target_path)
        return f"✓ Snapshot creato: {target_path} ({file_size} bytes)"
    
    return f"✗ Cattura fallita:\n{res}"

if __name__ == "__main__":
    mcp.run()