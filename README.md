<div align="center">

# Mass YouTube Downloader

</div>

A Windows batch script that uses `yt-dlp` and `ffmpeg` to download YouTube videos and convert them to high-quality MP3 files with embedded metadata and thumbnails.

---

## Overview

This tool automates the process of downloading multiple YouTube videos and converting them into audio files suitable for personal use and DJ libraries.

It focuses on:
- High-quality audio extraction
- Automated metadata embedding
- Clean file organization

---

## Features

- Batch downloading from a `links.txt` file
- Automatic conversion to MP3 (highest available quality)
- Metadata embedding (title, artist where available)
- Thumbnail extraction and embedding
- Automatic output organization
- Compatibility with DJ software such as Rekordbox and Serato

---

## Requirements

Before using the script, install the following dependencies:

### FFmpeg
```bash
winget install Gyan.FFmpeg
```
