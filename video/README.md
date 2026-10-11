# Vidéo Outils métier N4 · N5 · N7 (2 min)

`Video_Outils_N4_N5_N7.mp4` — 1920×1080, 30 i/s, 120 s, musique originale synthétisée (libre de droits).

Régénération (assets = dossier `ppt/media` extrait du .pptx) :

```
python3 src/music.py music.wav
python3 src/video.py <ppt/media> 0 3600 video.mp4
ffmpeg -i video.mp4 -i music.wav -c:v copy -c:a aac -shortest final.mp4
```
