import json
import os
from pydub import AudioSegment
from pydub.silence import *

languages_dir = 'languages'
output_audio_dir = '_site/course'
tmp_dir = 'tmp'

# Ensure output directories exist
os.makedirs(output_audio_dir, exist_ok=True)
os.makedirs(tmp_dir, exist_ok=True)

# List all json files in the languages directory
json_files = [f for f in os.listdir(languages_dir) if f.endswith('.json')]


print(f"Found {len(json_files)} JSON files in '{languages_dir}': {json_files}\n")

html_content = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width" />
    <title>Language learning audio phrases</title>
    <link rel="stylesheet" href="styles.css">
  </head>
<body>
<h1>Language learning audio phrases</h1>
<p>Learn the basics of foreign languages with audio phrases, to communicate more easily around the world.</p>
<p>Listen to the phrase in the target language, repeat it, listen to the translation, and repeat the phrase again and think of the link between the phrase and the translation.</p>
<p>The courses are made to be listened multiple times (for instance while going on walks), make your memory work (mix of repetition and recall), and get used to the sonorities of the language.</p>"""

# Iterate and parse each json file
for json_file in json_files:
    file_path = os.path.join(languages_dir, json_file)
    with open(file_path, 'r') as file:
        data = json.load(file)

        language_name = data['language_name']
        language_slug = data['slug']
        print(f"\n--- Processing {language_name} ({json_file}) ---\n")

        course_audio = AudioSegment.empty()
        silence = AudioSegment.silent(duration=2000) # ms

        for i, sentence in enumerate(data['sentences']):
            target_audio_filename = sentence["target_audio"]
            english_audio_filename = sentence["english_audio"]

            # Assuming target audio files are in a subdirectory named after the slug within languages_dir
            target_audio_path = os.path.join(languages_dir, language_slug, target_audio_filename)
            english_audio_path = os.path.join(languages_dir, language_slug, english_audio_filename)

            if not os.path.exists(target_audio_path):
                print(f"WARNING: target audio file not found: {target_audio_path}. Skipping this sentence.")
                continue
            if not os.path.exists(english_audio_path):
                print(f"WARNING: english audio file not found: {english_audio_path}. Skipping this sentence.")
                continue

            # Load audios
            target_audio = AudioSegment.from_file(target_audio_path)
            english_audio = AudioSegment.from_file(english_audio_path)

            # Concatenate target audio + silence + english audio + silence
            combined_sentence_audio = target_audio + silence + english_audio + silence
            course_audio += combined_sentence_audio

        # Export the final course audio
        output_filename = f"{language_slug}_course.mp3"
        output_filepath = os.path.join(output_audio_dir, output_filename)
        site_output_filepath = os.path.join('course', output_filename)
        course_audio = course_audio.set_frame_rate(22050)
        course_audio = course_audio.set_sample_width(2)
        course_audio.export(output_filepath, format="mp3", bitrate="128k")
        print(f"Successfully created course audio: {output_filepath}")

        html_content += f"""<hr><div class="audio-item">
            <h2>{data['language_name']} course</h2>
            <audio controls>
                <source src="{site_output_filepath}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
            <br>
            <a href="{site_output_filepath}" download>Download course</a>
            <p>Audio source: <a href={data['sources'][0]}>{data['sources'][0]}</a></p>
        </div>"""

print("\nAll courses processed.")

html_content += """<br><hr><a href="https://codeberg.org/anto4/audiophrases/">Open-source website</a>. <p>The courses are built by extracting and organizing content from other existing public domain sources. Those external sources have their link provided.</p></body>
</html>"""

with open("_site/index.html", 'w', encoding='utf-8') as f:
    f.write(html_content)
