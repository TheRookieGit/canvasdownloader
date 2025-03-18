import subprocess

config_files = [
    r"C:\Users\Initi\Desktop\Canvassync_25WQ\course034.json",
    r"C:\Users\Initi\Desktop\Canvassync_25WQ\course050.json",
    r"C:\Users\Initi\Desktop\Canvassync_25WQ\course127.json"
]

for config_file in config_files:
    command = [r"C:\Users\Initi\AppData\Local\Programs\Python\Python313\Scripts\canvassyncer.exe", "-p", config_file]
    print("Running command:", " ".join(command))  # 打印命令用于调试
    try:
        subprocess.run(command, text=True, timeout=10, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}: {e}")
    except subprocess.TimeoutExpired:
        print("Command timed out.")
    except FileNotFoundError as e:
        print(f"Command not found: {e}")
