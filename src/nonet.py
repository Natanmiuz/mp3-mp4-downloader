import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
import threading
import os
import sys
from datetime import datetime

class VideoDownloaderApp:
    PLATFORMS = ['Auto-detect', 'YouTube', 'Facebook', 'TikTok', 'Twitter']
    FORMATS = [('MP4', 'mp4'), ('MP3', 'mp3')]
    RESOLUTIONS = ['360p', '480p', '720p', '1080p', 'Best available']
    DEFAULT_FORMAT = 'mp4'
    DEFAULT_RESOLUTION = '360p'

    def __init__(self, root):
        self.root = root
        self.root.title("Video/Audio Downloader")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.setup_variables()
        self.create_widgets()
        self.toggle_resolution()

    def setup_variables(self):
        self.url_var = tk.StringVar()
        self.platform_var = tk.StringVar(value='Auto-detect')
        self.format_var = tk.StringVar(value=self.DEFAULT_FORMAT)
        self.resolution_var = tk.StringVar(value=self.DEFAULT_RESOLUTION)
        self.download_path_var = tk.StringVar()

    def create_widgets(self):
        #Set up style
        style = ttk.Style()
        style.configure('TLabel', padding=5)
        style.configure('TButton', padding=5)
        style.configure('TRadiobutton', padding=5)

        #Create frame
        self.create_url_frame()
        self.create_options_frame()
        self.create_path_frame()
        self.create_button_frame()
        self.create_status_frame()

    def create_url_frame(self):
        frame = ttk.LabelFrame(self.root, text="Video URL", padding=10)
        frame.grid(row=0, column=0, padx=10, pady=5, sticky='ew')

        ttk.Label(frame, text="URL:").grid(row=0, column=0, sticky='w')
        url_entry = ttk.Entry(frame, textvariable=self.url_var, width=50)
        url_entry.grid(row=0, column=1, columnspan=2, sticky='ew', padx=5)
        url_entry.focus_set()

    def create_options_frame(self):
        frame = ttk.LabelFrame(self.root, text="Download Options", padding=10)
        frame.grid(row=1, column=0, padx=10, pady=5, sticky='ew')

        #Platform
        ttk.Label(frame, text="Platform:").grid(row=0, column=0, sticky='w')
        self.platform_combobox = ttk.Combobox(
            frame, textvariable=self.platform_var, values=self.PLATFORMS, state='readonly')
        self.platform_combobox.grid(row=0, column=1, sticky='ew', padx=5, pady=2)

        #Format
        ttk.Label(frame, text="Format:").grid(row=1, column=0, sticky='w')
        for i, (text, value) in enumerate(self.FORMATS):
            rb = ttk.Radiobutton(
                frame, text=text, variable=self.format_var, 
                value=value, command=self.toggle_resolution)
            rb.grid(row=1, column=i+1, sticky='w', padx=5)

        #Resolution
        ttk.Label(frame, text="Resolution:").grid(row=2, column=0, sticky='w')
        self.resolution_combobox = ttk.Combobox(
            frame, textvariable=self.resolution_var, values=self.RESOLUTIONS, state='readonly')
        self.resolution_combobox.grid(row=2, column=1, sticky='ew', padx=5, pady=2)

    def create_path_frame(self):
        frame = ttk.LabelFrame(self.root, text="Download Path", padding=10)
        frame.grid(row=2, column=0, padx=10, pady=5, sticky='ew')

        ttk.Label(frame, text="Path:").grid(row=0, column=0, sticky='w')
        path_entry = ttk.Entry(frame, textvariable=self.download_path_var, width=40)
        path_entry.grid(row=0, column=1, sticky='ew', padx=5)
        ttk.Button(frame, text="Browse", command=self.browse_directory).grid(row=0, column=2, padx=5)

    def create_button_frame(self):
        frame = ttk.Frame(self.root)
        frame.grid(row=3, column=0, padx=10, pady=10, sticky='e')

        ttk.Button(frame, text="Clear", command=self.clear_fields).pack(side='left', padx=5)
        self.download_button = ttk.Button(frame, text="Download", command=self.start_download)
        self.download_button.pack(side='left', padx=5)

    def create_status_frame(self):
        frame = ttk.LabelFrame(self.root, text="Status", padding=10)
        frame.grid(row=4, column=0, padx=10, pady=5, sticky='nsew')

        self.status_text = tk.Text(frame, height=10, width=70, wrap='word')
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

    def toggle_resolution(self):
        state = 'normal' if self.format_var.get() == 'mp4' else 'disabled'
        self.resolution_combobox.config(state=state)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.download_path_var.set(directory)

    def clear_fields(self):
        self.url_var.set('')
        self.platform_var.set('Auto-detect')
        self.format_var.set(self.DEFAULT_FORMAT)
        self.resolution_var.set(self.DEFAULT_RESOLUTION)
        self.download_path_var.set('')
        self.status_text.delete('1.0', tk.END)
        self.update_status("Fields cleared. Ready for new download.")
        self.toggle_resolution()

    def validate_inputs(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a valid URL.")
            return False
        
        if not self.download_path_var.get():
            messagebox.showerror("Error", "Please select a download directory.")
            return False
            
        if self.format_var.get() == 'mp4':
            ffmpeg_path = self.get_ffmpeg_path()
            if not os.path.isfile(ffmpeg_path):
                messagebox.showerror("Error", "FFmpeg not found. Required for video processing.")
                return False
                
        return True

    def get_ffmpeg_path(self):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, 'ffmpeg.exe')

    def start_download(self):
        if not self.validate_inputs():
            return

        self.download_button.config(state='disabled')
        threading.Thread(target=self.process_download, daemon=True).start()

    def process_download(self):
        try:
            url = self.url_var.get().strip()
            platform = self.detect_platform(url)
            options = self.build_ydl_options()
            
            self.update_status(f"Starting download from {platform}...")
            
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])
                
            self.update_status("Download completed successfully!")
            self.open_download_directory()
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
        finally:
            self.root.after(0, lambda: self.download_button.config(state='normal'))

    def detect_platform(self, url):
        if self.platform_var.get() != 'Auto-detect':
            return self.platform_var.get()
            
        url_lower = url.lower()
        for platform in self.PLATFORMS[1:]:  # Skip Auto-detect
            if platform.lower() in url_lower:
                return platform
        return 'Unknown Platform'

    def build_ydl_options(self):
        options = {
            'outtmpl': os.path.join(self.download_path_var.get(), '%(title)s.%(ext)s'),
            'ffmpeg_location': self.get_ffmpeg_path(),
            'progress_hooks': [self.progress_hook],
            'noplaylist': True,
            'quiet': True,
            'no_warnings': False,
        }

        if self.format_var.get() == 'mp3':
            options.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            res = self.resolution_var.get()
            options['format'] = self.get_video_format(res)

        return options

    def get_video_format(self, resolution):
        if resolution == 'Best available':
            return 'bestvideo+bestaudio/best'
        height = int(resolution.replace('p', ''))
        return f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'N/A').strip()
            speed = d.get('_speed_str', 'N/A').strip()
            self.update_status(f"Progress: {percent} | Speed: {speed}")
        elif d['status'] == 'finished':
            self.update_status("Post-processing...")

    def update_status(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.root.after(0, lambda: self.status_text.insert(
            tk.END, f"[{timestamp}] {message}\n"))
        self.root.after(0, lambda: self.status_text.see(tk.END))

    def open_download_directory(self):
        path = self.download_path_var.get()
        if path and os.path.isdir(path):
            try:
                os.startfile(path)
            except AttributeError:
                messagebox.showinfo("Download Complete", f"Files saved in: {path}")

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoDownloaderApp(root)
    root.mainloop()