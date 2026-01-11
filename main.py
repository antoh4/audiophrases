import json
import os
from TTS.api import TTS
from pydub import AudioSegment
from pydub.silence import *

languages_dir = 'languages'
output_audio_dir = 'site/output_audio'
tmp_dir = 'tmp'

# Ensure output directories exist
os.makedirs(output_audio_dir, exist_ok=True)
os.makedirs(tmp_dir, exist_ok=True)

# List all json files in the languages directory
json_files = [f for f in os.listdir(languages_dir) if f.endswith('.json')]

tts = TTS("tts_models/en/ljspeech/vits")

print(f"Found {len(json_files)} JSON files in '{languages_dir}': {json_files}\n")

html_content = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width" />
    <title>Audio language courses</title>
  </head>
<body>"""

# Iterate and parse each json file
for json_file in json_files:
    file_path = os.path.join(languages_dir, json_file)
    with open(file_path, 'r') as file:
        data = json.load(file)

        language_name = data['language_name']
        language_slug = data['slug']
        print(f"\n--- Processing {language_name} ({json_file}) ---\n")


        course_audio = AudioSegment.empty()
        silence = AudioSegment.silent(duration=1000) # 1 second silence

        for i, sentence in enumerate(data['sentences']):
            english_sentence = sentence["english"]
            target_audio_filename = sentence["audio_file"]

            # Assuming native audio files are in a subdirectory named after the slug within languages_dir
            native_audio_path = os.path.join(languages_dir, language_slug, target_audio_filename)

            if not os.path.exists(native_audio_path):
                print(f"WARNING: Native audio file not found: {native_audio_path}. Skipping this sentence.")
                continue

            print(f"Generating audio for: '{english_sentence}'")

            # Load native speaker audio
            native_audio = AudioSegment.from_file(native_audio_path)

            # Generate TTS for the English translation
            tts_output_filepath = os.path.join(tmp_dir, f"tts_{language_slug}_{i}.wav")
            tts.tts_to_file(text=english_sentence, file_path=tts_output_filepath)
            english_tts_audio = AudioSegment.from_file(tts_output_filepath)

            # Concatenate native audio + silence + TTS audio + silence
            combined_sentence_audio = native_audio + silence + english_tts_audio + silence
            course_audio += combined_sentence_audio

            # Clean up temporary TTS file
            os.remove(tts_output_filepath)

        # Export the final course audio
        output_filename = f"{language_slug}_course.wav"
        output_filepath = os.path.join(output_audio_dir, output_filename)
        course_audio.export(output_filepath, format="wav")
        print(f"Successfully created course audio: {output_filepath}")

        html_content += f"""<div class="audio-item">
            <h2>English to {data['language_name']}</h2>
            <audio controls>
                <source src="{output_filepath}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
            <a href="{output_filepath}" download>Download course</a>
        </div>"""

print("\nAll courses processed.")

html_content += """</body>
</html>"""

with open("site/index.html", 'w', encoding='utf-8') as f:
    f.write(html_content)
