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
    
    # Ambiente come il tuo originale
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["DISPLAY"] = "" 
    env["XDG_RUNTIME_DIR"] = "/tmp"

    try:
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
            # LOGGING DETTAGLIATO per capire il problema
            error_msg = f"=== ERRORE CAMSNAP ===\n"
            error_msg += f"Return Code: {process.returncode}\n"
            error_msg += f"Comando eseguito: {camsnap_bin} {' '.join(args)}\n\n"
            
            if clean_stderr:
                error_msg += f"=== STDERR ===\n{clean_stderr}\n\n"
            
            if clean_stdout:
                error_msg += f"=== STDOUT ===\n{clean_stdout}\n"
            
            return error_msg
            
    except Exception as e:
        return f"Errore critico: {str(e)}"

@mcp.tool()
def list_cameras() -> str:
    """Elenca le telecamere configurate."""
    return run_executable_stream(["list"], is_snap=False)

@mcp.tool()
def capture_snap(camera_name: str) -> str:
    """Cattura un frame (Headless Mode)."""
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"
    
    # Esegui lo snap
    res = run_executable_stream(["snap", camera_name, "--out", target_path], is_snap=True)
    
    # Aspetta un attimo per l'I/O
    time.sleep(0.3)
    
    # Controllo fisico sul file
    if os.path.exists(target_path):
        file_size = os.path.getsize(target_path)
        if file_size > 0:
            return f"✓ Snapshot creato: {target_path} ({file_size} bytes)\n\nLog comando:\n{res}"
        else:
            return f"✗ File creato ma vuoto (0 bytes)\n\nLog comando:\n{res}"
    else:
        return f"✗ File non creato\n\nLog comando:\n{res}"

@mcp.tool()
def test_snap_terminal_vs_mcp(camera_name: str) -> str:
    """Confronta lo snap da terminale vs MCP per debug."""
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Test 1: Esattamente come da terminale
    test1_path = f"/tmp/test_terminal_{now}.jpg"
    
    result = f"=== TEST SNAP TERMINAL vs MCP ===\n\n"
    result += f"Camera: {camera_name}\n"
    result += f"File output: {test1_path}\n\n"
    
    # Esegui il comando ESATTAMENTE come faresti da terminale
    camsnap_bin = shutil.which("camsnap")
    result += f"Binario: {camsnap_bin}\n\n"
    
    # NON usare env modificato, usa l'ambiente naturale
    try:
        process = subprocess.run(
            [camsnap_bin, "snap", camera_name, "--out", test1_path],
            capture_output=True,
            text=True,
            timeout=30,
            # USA L'AMBIENTE ORIGINALE senza modifiche
            env=None  
        )
        
        result += f"Return code: {process.returncode}\n"
        result += f"STDOUT:\n{process.stdout}\n"
        result += f"STDERR:\n{process.stderr}\n\n"
        
        if os.path.exists(test1_path):
            size = os.path.getsize(test1_path)
            result += f"✓ File creato: {size} bytes\n"
        else:
            result += f"✗ File NON creato\n"
            
    except Exception as e:
        result += f"Eccezione: {str(e)}\n"
    
    return result

if __name__ == "__main__":
    mcp.run()