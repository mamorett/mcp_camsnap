# /// script
# dependencies = ["mcp"]
# ///
import subprocess
import os
import shutil
import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Camsnap Manager")

@mcp.tool()
def list_cameras() -> str:
    """Questa funziona perché camsnap list è leggero e non invoca ffmpeg."""
    bin_path = shutil.which("camsnap") or "camsnap"
    return subprocess.check_output([bin_path, "list"], text=True)

@mcp.tool()
def capture_snap_direct(camera_rtsp_url: str, camera_name: str) -> str:
    """
    Bypassiamo camsnap e chiamiamo FFmpeg direttamente.
    Eliminiamo un livello di astrazione per evitare il 'signal: killed'.
    """
    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_path = f"/tmp/snap_{camera_name}_{now}.jpg"
    
    # Comando FFmpeg ottimizzato per snapshot singolo e veloce
    cmd = [
        ffmpeg_bin,
        "-y",                   # Sovrascrivi se esiste
        "-rtsp_transport", "tcp", # Forza TCP per stabilità
        "-i", camera_rtsp_url,  # URL che l'AI ha già letto dalla lista
        "-frames:v", "1",       # Prendi solo un frame
        "-q:v", "2",            # Alta qualità
        target_path
    ]
    
    try:
        # Usiamo DEVNULL per i log per non intasare l'MCP
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        
        if os.path.exists(target_path):
            return f"Snapshot OK (FFmpeg diretto): {target_path}"
        return "Errore: FFmpeg non ha prodotto il file."
    except Exception as e:
        return f"Errore durante l'invocazione diretta di FFmpeg: {str(e)}"

def main():
    mcp.run()

if __name__ == "__main__":
    main()