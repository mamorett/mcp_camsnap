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

    try:
        process = subprocess.Popen(
            [camsnap_bin] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        stdout, stderr = process.communicate(timeout=45)
        
        clean_stdout = stdout.strip()
        clean_stderr = stderr.strip()
        
        if process.returncode == 0:
            return clean_stdout or "Operazione completata."
        else:
            return f"Errore {process.returncode}\nSTDERR:\n{clean_stderr}\nSTDOUT:\n{clean_stdout}"
            
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        return "Errore: Timeout (45s)"
    except Exception as e:
        return f"Errore critico: {str(e)}"

@mcp.tool()
def list_cameras() -> str:
    """Elenca le telecamere configurate."""
    return run_executable_stream(["list"], is_snap=False)

@mcp.tool()
def capture_snap(camera_name: str) -> str:
    """Cattura un frame."""
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target_path = f"/tmp/cam_{camera_name}_{now}.jpg"
    
    res = run_executable_stream(["snap", camera_name, "--out", target_path], is_snap=True)
    
    time.sleep(0.5)
    
    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
        return f"Snapshot creato: {target_path}"
    
    return f"Cattura fallita:\n{res}"

def main():
    """Entry point per l'MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()