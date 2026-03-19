import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    TKINTERDND_AVAILABLE = True
except ImportError:
    TKINTERDND_AVAILABLE = False
import imageio_ffmpeg
import subprocess

SUPPORTED_FORMATS = ["wav", "flac", "ogg"]


class QuickOGGApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QuickOGG")
        self.root.geometry("550x450")
        self.root.resizable(False, False)

        self.file_list = []
        self.output_folder = ""
        self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

        self.setup_ui()
        if TKINTERDND_AVAILABLE:
            self.setup_drag_drop()

    def setup_ui(self):
        self.root.configure(bg="#f0f0f0")

        title_label = tk.Label(
            self.root, text="QuickOGG", font=("Arial", 16, "bold"),
            bg="#f0f0f0"
        )
        title_label.pack(pady=10)

        output_frame = tk.Frame(self.root, bg="#f0f0f0")
        output_frame.pack(pady=5, padx=10, fill=tk.X)

        tk.Label(output_frame, text="Output Folder:", bg="#f0f0f0").pack(side=tk.LEFT)

        self.output_entry = tk.Entry(output_frame, width=40)
        self.output_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        browse_btn = tk.Button(output_frame, text="Browse", command=self.select_output_folder)
        browse_btn.pack(side=tk.LEFT)

        if TKINTERDND_AVAILABLE:
            self.drop_label = tk.Label(
                self.root, text="Drag & Drop Audio Files Here",
                bg="white", fg="gray", font=("Arial", 10),
                height=3, relief=tk.RIDGE, borderwidth=2
            )
        else:
            self.drop_label = tk.Label(
                self.root, text="Drag & Drop (install tkinterdnd2 for this feature)",
                bg="#e0e0e0", fg="gray", font=("Arial", 9),
                height=3, relief=tk.RIDGE, borderwidth=2
            )
        self.drop_label.pack(pady=5, padx=10, fill=tk.X)

        self.listbox = tk.Listbox(
            self.root, width=65, height=10, selectmode=tk.EXTENDED
        )
        self.listbox.pack(pady=5)

        scrollbar = tk.Scrollbar(self.root, orient=tk.VERTICAL)
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        btn_frame = tk.Frame(self.root, bg="#f0f0f0")
        btn_frame.pack(pady=10)

        add_btn = tk.Button(
            btn_frame, text="Add Files", width=15, command=self.add_files
        )
        add_btn.grid(row=0, column=0, padx=5)

        clear_btn = tk.Button(
            btn_frame, text="Clear List", width=15, command=self.clear_list
        )
        clear_btn.grid(row=0, column=1, padx=5)

        remove_btn = tk.Button(
            btn_frame, text="Remove Selected", width=15, command=self.remove_selected
        )
        remove_btn.grid(row=1, column=0, padx=5, pady=5)

        convert_btn = tk.Button(
            btn_frame,
            text="Convert to OGG",
            width=32,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.convert_files,
        )
        convert_btn.grid(row=2, column=0, columnspan=2, padx=5, pady=10)

        self.status_label = tk.Label(self.root, text="Ready", fg="gray", bg="#f0f0f0")
        self.status_label.pack(side=tk.BOTTOM, pady=5)

    def setup_drag_drop(self):
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind('<<Drop>>', self.handle_drop)

    def handle_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        added = 0
        for f in files:
            ext = os.path.splitext(f)[-1].lower().lstrip('.')
            if ext in SUPPORTED_FORMATS and f not in self.file_list:
                self.file_list.append(f)
                self.listbox.insert(tk.END, os.path.basename(f))
                added += 1
        self.update_status(f"{added} file(s) added via drag & drop")

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder = folder
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder)
            self.update_status(f"Output folder set: {folder}")

    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Select Audio Files",
            filetypes=[("Audio Files", "*.wav *.flac *.ogg")],
        )
        for f in files:
            if f not in self.file_list:
                self.file_list.append(f)
                self.listbox.insert(tk.END, os.path.basename(f))
        self.update_status(f"{len(files)} file(s) added")

    def clear_list(self):
        self.file_list.clear()
        self.listbox.delete(0, tk.END)
        self.update_status("List cleared")

    def remove_selected(self):
        selected = self.listbox.curselection()
        for i in reversed(selected):
            self.file_list.pop(i)
            self.listbox.delete(i)
        self.update_status("Selected file(s) removed")

    def convert_files(self):
        if not self.file_list:
            messagebox.showwarning("No Files", "Please add audio files to convert.")
            return

        if not self.output_folder:
            messagebox.showwarning("No Output Folder", "Please select an output folder.")
            return

        self.update_status("Converting...")
        self.root.config(cursor="watch")
        self.root.update()

        converted = 0
        errors = []

        for f in self.file_list:
            try:
                input_ext = f.rsplit(".", 1)[-1].lower()
                if input_ext not in SUPPORTED_FORMATS:
                    errors.append(f"{os.path.basename(f)}: Unsupported format")
                    continue

                output_file = os.path.join(
                    self.output_folder, os.path.splitext(os.path.basename(f))[0] + ".ogg"
                )

                result = subprocess.run(
                    [self.ffmpeg_path, "-i", f, "-y", "-vn", "-acodec", "libvorbis", "-q:a", "4", output_file],
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    errors.append(f"{os.path.basename(f)}: Conversion failed")
                    continue

                converted += 1
            except Exception as e:
                errors.append(f"{os.path.basename(f)}: {str(e)}")

        self.root.config(cursor="")

        if errors:
            error_msg = "\n".join(errors)
            messagebox.showwarning(
                "Conversion Complete",
                f"Converted: {converted}\nErrors: {len(errors)}\n\n{error_msg}",
            )
        else:
            messagebox.showinfo(
                "Success", f"Successfully converted {converted} file(s) to OGG!"
            )

        self.update_status("Ready")

    def update_status(self, text):
        self.status_label.config(text=text)


def main():
    if TKINTERDND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = QuickOGGApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
