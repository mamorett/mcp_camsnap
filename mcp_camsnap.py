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
    """Elenca le telecamere (Logica originale funzionante)."""
    # Cerchiamo il binario senza percorsi fissi
    bin_path = shutil.which("camsnap") or "camsnap"
    # Esecuzione pulita: catturiamo solo stdout
    result = subprocess.run([bin_path, "list"], capture_output=True, text=True)
    return result.stdout.strip()

@mcp.tool()
def capture_snap_direct(camera_rtsp_url: str, camera_name: str) -> str:
    """Snapshot diretto via FFmpeg per evitare il crash del processo camsnap."""
    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target_path = f"/tmp/snap_{camera_name}_{now}.jpg"
    
    # Comando FFmpeg ottimizzato: TCP forzato, no audio, singolo frame
    cmd = [
        ffmpeg_bin, "-y", 
        "-rtsp_transport", "tcp", 
        "-i", camera_rtsp_url, 
        "-frames:v", "1", 
        "-q:v", "2", 
        target_path
    ]
    
    try:
        # Usiamo DEVNULL per evitare che FFmpeg sporchi lo stdout del protocollo MCP
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        
        if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            return f"Snapshot OK (FFmpeg): {target_path}"
        return "Errore: FFmpeg non ha generato il file."
    except Exception as e:
        return f"Errore durante lo snapshot: {str(e)}"

def main():
    # Lancio standard senza manipolazioni di sys.stdout
    mcp.run()

if __name__ == "__main__":
    main()