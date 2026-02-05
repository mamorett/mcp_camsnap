# /// script
# dependencies = [
#   "mcp",
# ]
# ///

import subprocess
import os
import time
import shutil
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Camsnap Manager")

def get_env():
    env = os.environ.copy()
    brew_paths = ["/home/linuxbrew/.linuxbrew/bin", "/opt/homebrew/bin", os.path.expanduser("~/.local/bin")]
    env["PATH"] = ":".join(brew_paths) + ":" + env.get("PATH", "")
    return env

@mcp.tool()
def list_cameras() -> str:
    """Elenca le telecamere configurate."""
    env = get_env()
    cmd = [shutil.which("camsnap", path=env["PATH"]) or "camsnap", "list"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=20)
        return res.stdout.strip() if res.returncode == 0 else f"Errore: {res.stderr}"
    except Exception as e:
        return f"Errore: {str(e)}"

@mcp.tool()
def capture_snap(camera_name: str) -> str:
    """Cattura un frame usando esecuzione isolata per evitare il segnale killed."""
    import datetime
    env = get_env()
    bin_path = shutil.which("camsnap", path=env["PATH"]) or "camsnap"
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"
    
    try:
        # LANCIO ISOLATO:
        # 1. Spediamo STDERR e STDOUT a DEVNULL per non intasare i buffer MCP
        # 2. start_new_session=True isola il processo da segnali mandati all'editor
        process = subprocess.Popen(
            [bin_path, "snap", camera_name, "--out", target_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            start_new_session=True 
        )
        
        # Aspettiamo che finisca (timeout generoso)
        for _ in range(30): # 30 secondi max
            if process.poll() is not None:
                break
            time.sleep(1)
        else:
            process.kill()
            return "Errore: FFmpeg è rimasto appeso troppo a lungo (Timeout 30s)."

        # Verifica finale sul file
        if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            return f"Snapshot OK! Percorso: {target_path}"
        else:
            return f"Errore: Il comando è finito (Code {process.returncode}) ma il file non è stato creato. Verifica con 'camsnap doctor'."

    except Exception as e:
        return f"Errore critico durante lo snapshot: {str(e)}"

if __name__ == "__main__":
    mcp.run()