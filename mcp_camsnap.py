import subprocess
import os
import shutil
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Camsnap Manager")

def run_executable_stream(args: list[str]) -> str:
    camsnap_bin = shutil.which("camsnap") or "camsnap"
    
    # Prepariamo l'esecuzione catturando stdout e stderr separatamente
    # e forzando l'assenza di buffering (PYTHONUNBUFFERED)
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    try:
        # Usiamo Popen per leggere in tempo reale ed evitare il deadlock dei buffer
        process = subprocess.Popen(
            [camsnap_bin] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Leggiamo tutto l'output disponibile
        stdout, stderr = process.communicate(timeout=30)
        
        # Pulizia dell'output: camsnap potrebbe usare caratteri speciali per le tabelle
        clean_stdout = stdout.strip()
        
        if process.returncode == 0:
            if not clean_stdout and stderr:
                # A volte i log utili finiscono in stderr anche se il codice è 0
                return f"Output (da stderr): {stderr.strip()}"
            return clean_stdout or "Comando eseguito, ma output vuoto."
        else:
            return f"Errore {process.returncode}\nLOG: {stderr}\nOUT: {stdout}"
            
    except subprocess.TimeoutExpired:
        process.kill()
        return "Errore: Timeout (il processo non rispondeva)."
    except Exception as e:
        return f"Errore critico: {str(e)}"

@mcp.tool()
def list_cameras() -> str:
    """Elenca le telecamere configurate."""
    # Proviamo a forzare un output semplice se camsnap lo supporta, 
    # altrimenti usiamo il metodo stream-safe
    return run_executable_stream(["list"])

@mcp.tool()
def capture_snap(camera_name: str) -> str:
    """Cattura un frame."""
    import datetime
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"
    
    # Eseguiamo il comando snap
    res = run_executable_stream(["snap", camera_name, "--out", target_path])
    
    if os.path.exists(target_path):
        return f"Snapshot creato con successo in: {target_path}"
    return f"Fallito. Log: {res}"