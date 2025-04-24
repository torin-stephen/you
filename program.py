import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

# Only on Windows: registry for file association
if sys.platform == 'win32':
    import winreg as reg

# Simple obfuscation key (XOR)
KEY = 0xAA

# Determine script/exe directory for icon path
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

ICON_FILENAME = 'you_icon.ico'
ICON_PATH = os.path.join(SCRIPT_DIR, ICON_FILENAME)

# Registry keys for .you association
REG_ROOT = reg.HKEY_CURRENT_USER if sys.platform == 'win32' else None
ASSOC_KEY = r"Software\Classes\.you"
PROG_KEY = r"Software\Classes\youfile"

# Obfuscate/deobfuscate data
def obfuscate(data: bytes) -> bytes:
    return bytes(b ^ KEY for b in data)

def ensure_file_association(icon_path):
    ext = ".you"
    prog_id = "youfile"
    executable_path = os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else sys.argv[0])

    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, f"Software\\Classes\\{ext}", 0, reg.KEY_READ) as key:
            current_value, _ = reg.QueryValueEx(key, "")
            if current_value != prog_id:
                raise FileNotFoundError
    except FileNotFoundError:
        with reg.CreateKey(reg.HKEY_CURRENT_USER, f"Software\\Classes\\{ext}") as key:
            reg.SetValueEx(key, "", 0, reg.REG_SZ, prog_id)

    icon_key_path = f"Software\\Classes\\{prog_id}\\DefaultIcon"
    command_key_path = f"Software\\Classes\\{prog_id}\\shell\\open\\command"

    icon_set = False
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, icon_key_path, 0, reg.KEY_READ) as key:
            icon_value, _ = reg.QueryValueEx(key, "")
            if not os.path.isfile(icon_value.split(",")[0]):
                raise FileNotFoundError
            icon_set = True
    except FileNotFoundError:
        icon_set = False

    if not icon_set:
        with reg.CreateKey(reg.HKEY_CURRENT_USER, icon_key_path) as key:
            reg.SetValueEx(key, "", 0, reg.REG_SZ, f'"{icon_path}",0')

    with reg.CreateKey(reg.HKEY_CURRENT_USER, command_key_path) as key:
        reg.SetValueEx(key, "", 0, reg.REG_SZ, f'"{executable_path}" "%1"')

# Encode input file
def encode_file(input_path: str, output_path: str):
    ext_bytes = os.path.splitext(input_path)[1].encode('utf-8')
    if len(ext_bytes) > 255:
        messagebox.showerror("Error", "Extension too long!")
        return
    header = len(ext_bytes).to_bytes(1, 'big') + ext_bytes
    try:
        with open(input_path, 'rb') as f:
            data = f.read()
        obf = obfuscate(data)
        with open(output_path, 'wb') as f:
            f.write(header + obf)
        messagebox.showinfo("Success", f"File encoded to: {output_path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# Decode .you file
def decode_file(input_path: str, output_dir: str):
    try:
        with open(input_path, 'rb') as f:
            header_len = f.read(1)[0]
            ext = f.read(header_len).decode('utf-8')
            data = f.read()
        deobf = obfuscate(data)
        if not ext:
            ext = '.txt'
        base = os.path.splitext(os.path.basename(input_path))[0]
        out_name = f"{base}_decoded{ext}"
        out_path = os.path.join(output_dir, out_name)
        with open(out_path, 'wb') as f:
            f.write(deobf)
        messagebox.showinfo("Success", f"File decoded to: {out_path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# Handle .you file passed as argument
input_from_arg = None
if len(sys.argv) > 1 and sys.argv[1].endswith(".you") and os.path.isfile(sys.argv[1]):
    input_from_arg = sys.argv[1]

# Main GUI
root = tk.Tk()
root.title("YOU Encoder/Decoder")
root.resizable(False, False)

# Set window icon if available
if os.path.exists(ICON_PATH):
    try:
        root.iconbitmap(ICON_PATH)
    except Exception:
        pass

# Re-register filetype if icon is missing
if sys.platform == 'win32' and os.path.exists(ICON_PATH):
    ensure_file_association(ICON_PATH)

mode = tk.StringVar(value='decode' if input_from_arg else 'encode')

frame = tk.Frame(root, padx=10, pady=10)
frame.grid(row=0, column=0)

tk.Label(frame, text="Input File:").grid(row=0, column=0, sticky='w')
in_entry = tk.Entry(frame, width=40)
in_entry.grid(row=0, column=1)
tk.Button(frame, text="Browse", command=lambda: in_entry.delete(0, tk.END) or in_entry.insert(0, filedialog.askopenfilename())).grid(row=0, column=2)

# If launched with a .you file, pre-fill it
if input_from_arg:
    in_entry.insert(0, input_from_arg)

# Output
tk.Label(frame, text="Output (.you or folder):").grid(row=1, column=0, sticky='w')
out_entry = tk.Entry(frame, width=40)
out_entry.grid(row=1, column=1)

def select_output():
    if mode.get() == 'encode':
        path = filedialog.asksaveasfilename(defaultextension='.you', filetypes=[('YOU files','.you')])
    else:
        path = filedialog.askdirectory()
    if path:
        out_entry.delete(0, tk.END)
        out_entry.insert(0, path)

tk.Button(frame, text="Browse", command=select_output).grid(row=1, column=2)

tk.Radiobutton(frame, text="Encode", variable=mode, value='encode').grid(row=2, column=0)
tk.Radiobutton(frame, text="Decode", variable=mode, value='decode').grid(row=2, column=1)

def run_action():
    inp = in_entry.get()
    out = out_entry.get()
    if not inp or not out:
        messagebox.showerror("Error", "Please select both input and output.")
        return
    if mode.get() == 'encode':
        encode_file(inp, out)
    else:
        decode_file(inp, out)

tk.Button(frame, text="Run", command=run_action).grid(row=3, column=1, pady=10)

root.mainloop()
