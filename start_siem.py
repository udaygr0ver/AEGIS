#!/usr/bin/env python3
import sys
import os
import time
import subprocess
import webbrowser
import threading

def main():
    print("=" * 60)
    print("🛡️  STARTING AEGIS SIEM ANALYTICS SYSTEM")
    print("=" * 60)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    python_bin = os.path.join(backend_dir, "venv", "bin", "python")

    if not os.path.exists(python_bin):
        python_bin = sys.executable

    env = os.environ.copy()
    env["PYTHONPATH"] = backend_dir

    print("🚀 Launching SIEM Backend & Detection Engine on http://localhost:8000 ...")
    backend_process = subprocess.Popen(
        [python_bin, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=base_dir,
        env=env
    )

    time.sleep(2)

    print("⚡ Starting Attack Simulator continuous traffic stream...")
    def run_simulator():
        time.sleep(3)
        sim_script = os.path.join(base_dir, "simulator", "generate_logs.py")
        subprocess.run([python_bin, sim_script, "--scenario", "continuous"])

    sim_thread = threading.Thread(target=run_simulator, daemon=True)
    sim_thread.start()

    print("\n🌐 Opening SIEM SOC Dashboard in your browser: http://localhost:8000\n")
    try:
        webbrowser.open("http://localhost:8000")
    except Exception:
        pass

    print("=" * 60)
    print("✅ AEGIS SIEM IS ONLINE AND RUNNING!")
    print("👉 Dashboard: http://localhost:8000")
    print("👉 Swagger API Docs: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server.")
    print("=" * 60)

    try:
        backend_process.wait()
    except KeyboardInterrupt:
        print("\nStopping SIEM Server...")
        backend_process.terminate()

if __name__ == "__main__":
    main()
