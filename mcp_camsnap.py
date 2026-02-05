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
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Camsnap Manager")

def run_executable_stream(args: list[str], is_snap: bool = False) -> str:
    camsnap_bin = shutil.which("camsnap") or "camsnap"
    
    # Ambiente più pulito e completo
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["DISPLAY"] = ""
    env["XDG_RUNTIME_DIR"] = "/tmp"
    
    # Aggiungi PATH esplicito nel caso il binario non sia trovato correttamente
    if "PATH" not in env:
        env["PATH"] = "/usr/local/bin:/usr/bin:/bin"
    
    # FFmpeg potrebbe aver bisogno di questi
    env["SDL_VIDEODRIVER"] = "dummy"
    env["LIBVA_DRIVER_NAME"] = "null"

    try:
        # Usa il path assoluto del binario
        camsnap_path = shutil.which("camsnap")
        if not camsnap_path:
            return "Errore: camsnap non trovato nel PATH"
        
        process = subprocess.Popen(
            [camsnap_path] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            # Aggiungi questi parametri per isolamento completo
            cwd="/tmp",  # Directory di lavoro sicura
            start_new_session=True  # Nuovo session ID
        )
        
        try:
            stdout, stderr = process.communicate(timeout=45)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            return "Errore: Timeout (45s) durante la comunicazione con la camera."
        
        clean_stdout = stdout.strip()
        clean_stderr = stderr.strip()
        
        if process.returncode == 0:
            return clean_stdout or "Operazione completata."
        else:
            # Log dettagliato per debug
            error_msg = f"Errore {process.returncode}\n"
            error_msg += f"Comando: {camsnap_path} {' '.join(args)}\n"
            if clean_stderr:
                error_msg += f"STDERR: {clean_stderr}\n"
            if clean_stdout:
                error_msg += f"STDOUT: {clean_stdout}"
            return error_msg
            
    except Exception as e:
        return f"Errore critico: {str(e)}\nComando tentato: {camsnap_path} {' '.join(args)}"

@mcp.tool()
def list_cameras() -> str:
    """Elenca le telecamere configurate."""
    return run_executable_stream(["list"], is_snap=False)

@mcp.tool()
def capture_snap(camera_name: str) -> str:
    """Cattura un frame (Headless Mode)."""
    # Assicurati che /tmp sia scrivibile
    tmp_dir = Path("/tmp")
    if not tmp_dir.is_dir() or not os.access(tmp_dir, os.W_OK):
        return "Errore: /tmp non accessibile in scrittura"
    
    # Timestamp univoco
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"
    
    # Verifica che la camera esista prima di tentare lo snap
    cameras_list = run_executable_stream(["list"], is_snap=False)
    if camera_name not in cameras_list:
        return f"Errore: Camera '{camera_name}' non trovata.\nCamere disponibili:\n{cameras_list}"
    
    res = run_executable_stream(["snap", camera_name, "--out", target_path], is_snap=True)
    
    # Controllo fisico sul file con delay per I/O
    time.sleep(0.5)  # Piccolo delay per assicurare che il file sia scritto
    
    if os.path.exists(target_path):
        file_size = os.path.getsize(target_path)
        if file_size > 0:
            return f"Snapshot creato con successo: {target_path} ({file_size} bytes)"
        else:
            return f"File creato ma vuoto (0 bytes). Log:\n{res}"
    
    return f"Cattura fallita - file non creato. Dettagli tecnici:\n{res}"

# Tool aggiuntivo per debug
@mcp.tool()
def debug_environment() -> str:
    """Mostra informazioni sull'ambiente di esecuzione per debug."""
    camsnap_path = shutil.which("camsnap")
    info = f"camsnap path: {camsnap_path}\n"
    info += f"User: {os.getenv('USER', 'unknown')}\n"
    info += f"Home: {os.getenv('HOME', 'unknown')}\n"
    info += f"/tmp writable: {os.access('/tmp', os.W_OK)}\n"
    
    # Testa un comando semplice
    if camsnap_path:
        try:
            result = subprocess.run(
                [camsnap_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            info += f"Version check: {result.stdout or result.stderr}"
        except Exception as e:
            info += f"Version check failed: {e}"
    
    return info

if __name__ == "__main__":
    mcp.run()