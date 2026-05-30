import json
import queue
import re
import shutil
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk


DOWNLOADS_DIR = Path("downloads")
PROGRESS_PATTERN = re.compile(r"\[download\]\s+(\d+(?:\.\d+)?)%")


class DownloaderUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Mass MP3 Downloader")
        self.root.geometry("1000x420")

        self.url_var = tk.StringVar()
        self.update_queue: queue.Queue[tuple[int, str, str]] = queue.Queue()
        self.items: list[dict[str, str]] = []
        self.downloading = False

        self._build_ui()
        self.root.after(100, self._process_updates)

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=12)
        top.pack(fill="x")

        ttk.Label(top, text="URL:").pack(side="left")
        entry = ttk.Entry(top, textvariable=self.url_var)
        entry.pack(side="left", fill="x", expand=True, padx=(8, 8))
        entry.bind("<Return>", lambda _: self.add_url())

        ttk.Button(top, text="Adicionar", command=self.add_url).pack(side="left")
        ttk.Button(top, text="Remover selecionada", command=self.remove_selected).pack(side="left", padx=(8, 0))

        columns = ("url", "status", "progress", "quality")
        self.table = ttk.Treeview(self.root, columns=columns, show="headings", height=14)
        self.table.pack(fill="both", expand=True, padx=12, pady=12)

        self.table.heading("url", text="URL")
        self.table.heading("status", text="Status")
        self.table.heading("progress", text="Progresso")
        self.table.heading("quality", text="Qualidade")

        self.table.column("url", width=560, anchor="w")
        self.table.column("status", width=150, anchor="center")
        self.table.column("progress", width=120, anchor="center")
        self.table.column("quality", width=140, anchor="center")

        bottom = ttk.Frame(self.root, padding=(12, 0, 12, 12))
        bottom.pack(fill="x")
        self.download_button = ttk.Button(bottom, text="Download", command=self.start_download)
        self.download_button.pack(side="right")

    def add_url(self) -> None:
        if self.downloading:
            return

        url = self.url_var.get().strip()
        if not url:
            return

        item = {"url": url, "status": "Aguardando", "progress": "0%", "quality": "-"}
        self.items.append(item)
        self.table.insert("", "end", values=(item["url"], item["status"], item["progress"], item["quality"]))
        self.url_var.set("")

    def remove_selected(self) -> None:
        if self.downloading:
            return

        selected = self.table.selection()
        indexed = sorted((self.table.index(tree_id), tree_id) for tree_id in selected)
        for index, tree_id in reversed(indexed):
            self.table.delete(tree_id)
            if 0 <= index < len(self.items):
                self.items.pop(index)

    def start_download(self) -> None:
        if self.downloading:
            return

        if not self.items:
            messagebox.showwarning("Sem URLs", "Adicione ao menos uma URL para baixar.")
            return

        if shutil.which("yt-dlp") is None:
            messagebox.showerror("Dependência ausente", "yt-dlp não encontrado no PATH.")
            return

        if shutil.which("ffmpeg") is None:
            messagebox.showerror("Dependência ausente", "ffmpeg não encontrado no PATH.")
            return

        DOWNLOADS_DIR.mkdir(exist_ok=True)
        self.downloading = True
        self.download_button.configure(state="disabled")
        threading.Thread(target=self._download_worker, daemon=True).start()

    def _download_worker(self) -> None:
        for index, item in enumerate(self.items):
            if item["status"] == "Concluído":
                continue

            self._queue_update(index, "status", "Preparando")

            quality = self._probe_quality(item["url"])
            self._queue_update(index, "quality", quality)

            command = [
                "yt-dlp",
                "--newline",
                "--progress",
                "--ignore-errors",
                "--no-playlist",
                "--extract-audio",
                "--audio-format",
                "mp3",
                "--audio-quality",
                "0",
                "--embed-thumbnail",
                "--convert-thumbnails",
                "jpg",
                "--embed-metadata",
                "--add-metadata",
                "--windows-filenames",
                "--parse-metadata",
                "%(title)s:%(artist)s - %(title)s",
                "--retries",
                "10",
                "--fragment-retries",
                "10",
                "--concurrent-fragments",
                "8",
                "-o",
                str(DOWNLOADS_DIR / "%(artist)s - %(title)s.%(ext)s"),
                item["url"],
            ]

            self._queue_update(index, "status", "Baixando")
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            if process.stdout:
                for line in process.stdout:
                    match = PROGRESS_PATTERN.search(line)
                    if match:
                        self._queue_update(index, "progress", f"{match.group(1)}%")

            code = process.wait()
            if code == 0:
                self._queue_update(index, "progress", "100%")
                self._queue_update(index, "status", "Concluído")
            else:
                self._queue_update(index, "status", "Erro")

        self.update_queue.put((-1, "done", ""))

    def _probe_quality(self, url: str) -> str:
        command = [
            "yt-dlp",
            "--dump-single-json",
            "--skip-download",
            "--no-warnings",
            url,
        ]
        try:
            data = subprocess.check_output(command, text=True)
            info = json.loads(data)
            abr = info.get("abr")
            if isinstance(abr, (int, float)):
                return f"{int(round(abr))} kbps"

            format_note = info.get("format_note")
            if isinstance(format_note, str) and format_note.strip():
                return format_note.strip()
        except Exception:
            pass
        return "Desconhecida"

    def _queue_update(self, index: int, field: str, value: str) -> None:
        self.update_queue.put((index, field, value))

    def _process_updates(self) -> None:
        while True:
            try:
                index, field, value = self.update_queue.get_nowait()
            except queue.Empty:
                break

            if field == "done":
                self.downloading = False
                self.download_button.configure(state="normal")
                continue

            if not (0 <= index < len(self.items)):
                continue

            self.items[index][field] = value
            row_id = self.table.get_children()[index]
            item = self.items[index]
            self.table.item(row_id, values=(item["url"], item["status"], item["progress"], item["quality"]))

        self.root.after(100, self._process_updates)


def main() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    DownloaderUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
