# /// script
# dependencies = [
#   "mcp",
# ]
# ///

import subprocess
import os
import datetime
import shutil
import time
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Camsnap Manager")

def get_clean_env():
    """Ricostruisce l'ambiente dinamico interpellando 'brew' se presente."""
    env = os.environ.copy()
    
    # Cerchiamo l'eseguibile brew ovunque sia nel sistema
    brew_bin = shutil.which("brew")
    if not brew_bin:
        # Check percorsi comuni solo come fallback per trovare il binario brew
        for p in ["/home/linuxbrew/.linuxbrew/bin/brew", "/opt/homebrew/bin/brew", "/usr/local/bin/brew"]:
            if os.path.exists(p):
                brew_bin = p
                break

    if brew_bin:
        try:
            # Recuperiamo le variabili d'ambiente reali di Homebrew (PATH, LD_LIBRARY_PATH, etc.)
            output = subprocess.check_output([brew_bin, "shellenv"], text=True)
            for line in output.splitlines():
                if line.startswith("export "):
                    parts = line.replace("export ", "").split("=", 1)
                    if len(parts) == 2:
                        name = parts[0]
                        value = parts[1].strip('"').strip(';')
                        if name == "PATH":
                            env["PATH"] = f"{value}:{env.get('PATH', '')}"
                        else:
                            env[name] = value
        except:
            pass
    return env

def run_isolated_cmd(args: list[str], silence: bool = True):
    """Esegue il comando isolando gli stream per prevenire il segnale 'killed'."""
    env = get_clean_env()
    camsnap_bin = shutil.which("camsnap", path=env.get("PATH"))
    
    if not camsnap_bin:
        return None, "Errore: 'camsnap' non trovato nel sistema."

    try:
        # Se silence=True, mandiamo tutto a DEVNULL per evitare saturazione buffer
        # Questo previene il crash di FFmpeg in ambienti con pipe limitate
        out_target = subprocess.DEVNULL if silence else subprocess.PIPE
        err_target = subprocess.DEVNULL if silence else subprocess.PIPE

        process = subprocess.Popen(
            [camsnap_bin] + args,
            stdout=out_target,
            stderr=err_target,
            text=True,
            env=env,
            start_new_session=True # Isola il processo da segnali dell'editor
        )
        
        # Gestione timeout manuale per monitorare il processo
        start_time = time.time()
        while time.time() - start_time < 45:
            if process.poll() is not None:
                break
            time.sleep(0.5)
        else:
            process.kill()
            return None, "Timeout: Il processo ha impiegato più di 45 secondi."

        if silence:
            return process.returncode, ""
        else:
            stdout, stderr = process.communicate()
            return process.returncode, stdout if process.returncode == 0 else stderr

    except Exception as e:
        return None, str(e)

@mcp.tool()
def list_cameras() -> str:
    """Elenca le telecamere configurate (Stream-Safe)."""
    code, output = run_isolated_cmd(["list"], silence=False)
    if code == 0:
        return output if output.strip() else "Lista camere vuota (verifica config)."
    return f"Errore list: {output}"

@mcp.tool()
def capture_snap(camera_name: str) -> str:
    """Cattura un frame (Zero-Output Mode per stabilità)."""
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"
    
    # Usiamo il silenzio assoluto durante la cattura per proteggere FFmpeg
    code, err = run_isolated_cmd(["snap", camera_name, "--out", target_path], silence=True)
    
    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
        return f"Snapshot OK: {target_path}"
    
    return f"Errore cattura (Code {code}): {err}. Verifica con camsnap doctor."

if __name__ == "__main__":
    mcp.run()