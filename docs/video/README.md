# Narrated demo

`Antikythera-demo.mp4` is a 1280×720 demonstration with a one-minute UI tour and ten-slide narration. Duration is 249.09 seconds. It includes video, audio and a selectable subtitle track. `Antikythera-demo.srt` is also provided separately.

Narration uses the installed Apple Samantha voice, generated locally. There is no external speech service or paid model request. `TRANSCRIPT.md` contains the spoken text. Captures show the actual local research workspace, and scientific results remain pending exactly as in the report.

Rebuild on a Mac with the installed voice and FFmpeg using `make video`. The script verifies nonempty narration, streams and the ten-minute duration limit. Voice/audio conversion needs access to the installed system speech service. Slide images and the original narration are retained for editable production.
