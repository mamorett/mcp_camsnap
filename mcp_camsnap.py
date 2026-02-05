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

def get_dynamic_env():
    """Ricostruisce l'ambiente basandosi sulla posizione reale di brew."""
    env = os.environ.copy()
    
    # 1. Trova dove risiede brew (l'unico punto di partenza)
    brew_bin = shutil.which("brew")
    
    # 2. Se brew è nel PATH, estraiamo le sue variabili (PATH, LD_LIBRARY_PATH, etc.)
    # Se non è nel PATH, proviamo a cercarlo nei path standard di Linux/macOS
    if not brew_bin:
        for path in ["/home/linuxbrew/.linuxbrew/bin/brew", "/opt/homebrew/bin/brew", "/usr/local/bin/brew"]:
            if os.path.exists(path):
                brew_bin = path
                break

    if brew_bin:
        try:
            # Eseguiamo 'brew shellenv' per ottenere le variabili necessarie
            output = subprocess.check_output([brew_bin, "shellenv"], text=True)
            for line in output.splitlines():
                if line.startswith("export "):
                    # Trasformiamo 'export NAME="value"' in NAME: value
                    parts = line.replace("export ", "").split("=", 1)
                    if len(parts) == 2:
                        name = parts[0]
                        value = parts[1].strip('"').strip(';')
                        # Aggiorniamo il PATH invece di sovrascriverlo
                        if name == "PATH":
                            env["PATH"] = f"{value}:{env.get('PATH', '')}"
                        else:
                            env[name] = value
        except Exception:
            pass # Se brew shellenv fallisce, proseguiamo col PATH ereditato

    return env

def run_executable(args: list[str]) -> str:
    env = get_dynamic_env()
    
    # Cerchiamo camsnap nel PATH arricchito
    camsnap_bin = shutil.which("camsnap", path=env.get("PATH"))
    
    if not camsnap_bin:
        return "Errore: 'camsnap' non trovato. Verifica che sia nel PATH o installato via Brew."

    try:
        # Eseguiamo il comando ereditando l'ambiente dinamico
        result = subprocess.run(
            [camsnap_bin] + args,
            capture_output=True,
            text=True,
            env=env,
            timeout=40
        )
        
        if result.returncode == 0:
            return result.stdout.strip() or "Comando completato (nessun output)."
        else:
            return f"Errore {result.returncode}:\n{result.stderr}\n{result.stdout}"
            
    except subprocess.TimeoutExpired:
        return "Errore: Timeout (40s)."
    except Exception as e:
        return f"Errore critico: {str(e)}"

@mcp.tool()
def list_cameras() -> str:
    """Elenca le telecamere configurate."""
    return run_executable(["list"])

@mcp.tool()
def capture_snap(camera_name: str) -> str:
    """Cattura un frame con timestamp in /tmp."""
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"
    res = run_executable(["snap", camera_name, "--out", target_path])
    return f"Risultato: {res}" if "Errore" in res else f"Snapshot: {target_path}"

if __name__ == "__main__":
    mcp.run()