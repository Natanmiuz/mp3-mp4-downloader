#!/usr/bin/env python3
import os
import sys
import argparse
from datetime import datetime
import yt_dlp

class Downloader:
    def __init__(self, url, format, path, ffmpeg_path):
        self.url = url
        self.format = format
        self.path = path
        self.ffmpeg_path = ffmpeg_path
        self.start_time = datetime.now()
        
    def run(self):
        try:
            print(f"\n[+] Iniciando descarga: {self.url}")
            options = self._build_options()
            
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(self.url, download=False)
                title = info.get('title', 'video')
                print(f"[>] Descargando: {title}")
                ydl.download([self.url])
                
            elapsed = datetime.now() - self.start_time
            print(f"\n[✓] Descarga completada en {elapsed.total_seconds():.1f} segundos")
            
        except Exception as e:
            print(f"\n[!] Error: {str(e)}")
            sys.exit(1)

    def _build_options(self):
        options = {
            'outtmpl': os.path.join(self.path, '%(title)s.%(ext)s'),
            'ffmpeg_location': self.ffmpeg_path,
            'progress_hooks': [self._progress_hook],
            'noplaylist': True,
            'quiet': False,
            'no_warnings': False,
        }

        if self.format == 'mp3':
            print("[>] Formato seleccionado: MP3 (Audio)")
            options.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            print("[>] Formato seleccionado: Video (Mejor calidad disponible)")
            options['format'] = 'bestvideo+bestaudio/best'

        return options

    def _progress_hook(self, data):
        if data['status'] == 'downloading':
            percent = data.get('_percent_str', 'N/A').strip()
            speed = data.get('_speed_str', 'N/A').strip()
            eta = data.get('_eta_str', 'N/A').strip()
            print(f"\r[↓] Progreso: {percent} | Velocidad: {speed} | ETA: {eta}", end='', flush=True)
        elif data['status'] == 'finished':
            print("\n[▶] Post-procesando...")

def main():
    parser = argparse.ArgumentParser(description='Descargador CLI de videos/audios')
    parser.add_argument('url', nargs='?', help='URL del video (opcional)')
    parser.add_argument('-f', '--format', choices=['mp3', 'mp4'], default='mp4',
                        help='Formato de salida: mp3 (audio) o mp4 (video) (default: mp4)')
    parser.add_argument('-o', '--output', default='./descargas',
                        help='Directorio de salida (default: ./descargas)')
    parser.add_argument('--ffmpeg', default='ffmpeg',
                        help='Ruta a FFmpeg (default: busca en PATH)')

    args = parser.parse_args()

    # Obtener URL si no se proporcionó
    if not args.url:
        args.url = input("\nIngrese la URL del video: ").strip()
        if not args.url:
            print("[!] Error: Debe proporcionar una URL")
            sys.exit(1)

    # Crear directorio si no existe
    os.makedirs(args.output, exist_ok=True)
    
    downloader = Downloader(
        url=args.url,
        format=args.format,
        path=args.output,
        ffmpeg_path=args.ffmpeg
    )
    
    downloader.run()

if __name__ == "__main__":
    main()