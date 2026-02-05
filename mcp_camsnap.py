# /// script
# dependencies = [
#   "mcp",
# ]
# ///

import subprocess
import os
import shutil
import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Camsnap Manager")

def run_executable_stream(args: list[str], is_snap: bool = False) -> str:
    camsnap_bin = shutil.which("camsnap") or "camsnap"
    
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    try:
        # Per lo SNAP, ridirigiamo stderr a DEVNULL. 
        # I log di FFmpeg sono la causa del "signal: killed" nelle pipe MCP.
        stderr_target = subprocess.DEVNULL if is_snap else subprocess.PIPE
        
        process = subprocess.Popen(
            [camsnap_bin] + args,
            stdout=subprocess.PIPE,
            stderr=stderr_target,
            text=True,
            env=env
        )
        
        # Se è uno snap, leggiamo solo stdout (che sarà breve)
        # Se è una lista, leggiamo entrambi
        stdout, stderr = process.communicate(timeout=45)
        
        clean_stdout = stdout.strip()
        
        if process.returncode == 0:
            if not is_snap and not clean_stdout and stderr:
                return f"Output (da stderr): {stderr.strip()}"
            return clean_stdout or "Comando eseguito."
        else:
            error_msg = stderr.strip() if stderr else "Processo terminato forzatamente."
            return f"Errore {process.returncode}\nLOG: {error_msg}\nOUT: {clean_stdout}"
            
    except subprocess.TimeoutExpired:
        process.kill()
        return "Errore: Timeout (il processo non rispondeva)."
    except Exception as e:
        return f"Errore critico: {str(e)}"

@mcp.tool()
def list_cameras() -> str:
    """Elenca le telecamere configurate."""
    # Per la lista vogliamo vedere stderr in caso di errore
    return run_executable_stream(["list"], is_snap=False)

@mcp.tool()
def capture_snap(camera_name: str) -> str:
    """Cattura un frame salvandolo in /tmp con timestamp unico."""
    # Usiamo i microsecondi %f per evitare sovrascritture in caso di chiamate rapide
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"
    
    # Eseguiamo lo snap con is_snap=True per silenziare i log di FFmpeg
    res = run_executable_stream(["snap", camera_name, "--out", target_path], is_snap=True)
    
    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
        return f"Snapshot creato con successo: {target_path}"
    
    return f"Cattura fallita. Dettagli: {res}"

if __name__ == "__main__":
    mcp.run()