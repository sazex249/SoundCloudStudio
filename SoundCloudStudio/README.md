# SoundCloud Studio

A Windows desktop library manager for public SoundCloud profiles and playlists.
It downloads only tracks that SoundCloud/yt-dlp exposes as downloadable by the
uploader. It does not bypass private access, subscriptions, DRM, or rights controls.

## Run from source
1. Install Python 3.11 or newer.
2. Install FFmpeg and make `ffmpeg.exe` available on PATH (optional for original formats;
   required for MP3 conversion).
3. Run `python -m pip install -r requirements.txt`
4. Run `python main.py`

## Build the Windows EXE
The recommended route is GitHub Actions:
1. Create a GitHub repository and upload this project.
2. Push to the `main` branch (or use Actions -> Build Windows app -> Run workflow).
3. Open the completed workflow run and download the `SoundCloudStudio-Windows` artifact.
4. Extract the ZIP and launch `SoundCloudStudio.exe`.

The workflow builds on `windows-latest`; it does not produce a Linux executable.

## Notes
- MP3 conversion uses the bundled FFmpeg binary. If it cannot be initialized, choose "Source format".
- SoundCloud may not expose every track, playlist, or download. Availability is determined
  by the service and uploader settings.
- Downloads are stored locally. Respect creators' rights and SoundCloud's terms.
