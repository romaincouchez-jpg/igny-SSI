# Vidéo Outils métier N4 · N5 · N7 (2 min)

`Video_Outils_N4_N5_N7.mp4` — 1920×1080, 30 i/s, 120 s, musique originale synthétisée (libre de droits).

Régénération (assets = dossier `ppt/media` extrait du .pptx) :

```
python3 src/music.py music.wav
python3 src/video.py <ppt/media> 0 3600 video.mp4
ffmpeg -i video.mp4 -i music.wav -c:v copy -c:a aac -shortest final.mp4
```

## v2 (3 min)

`Video_Outils_N4_N5_N7_v2.mp4` — constat sur un seul slide avec les vrais plans « avant », puis une scène par outil
avec les vrais livrables (plan, DOE généré, Excel de chiffrage rempli, dossier N4, plan technicien).

```
python3 src/music2.py music.wav
python3 src/video2.py <ppt/media> <dossier_captures> 0 5400 video.mp4
```

## PowerPoint équivalent

`Presentation_Outils_N4_N5_N7_v2.pptx` — deck d’origine, constat sur 1 slide et 8 slides solutions (mêmes visuels que la vidéo), notes de présentation sur chaque slide.
