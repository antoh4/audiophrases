import json
import os
from pydub import AudioSegment
from pydub.silence import *
import shutil

languages_dir = 'languages'
output_audio_dir = '_site/audio_courses'
output_pages_dir = '_site/courses'

# Ensure output directories exist
# we remove the old pages and recreate the folder. as we regenerate the pages
shutil.rmtree(output_audio_dir, ignore_errors=True)
os.makedirs(output_audio_dir, exist_ok=True)

shutil.rmtree(output_pages_dir, ignore_errors=True)
os.makedirs(output_pages_dir, exist_ok=True)

# List all json files in the languages directory
json_files = sorted([f for f in os.listdir(languages_dir) if f.endswith('.json')])

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
<p>Learn the basics of foreign languages with audio phrases, to communicate more easily around the world and make people smile.</p>
<p>Listen to the phrase in the target language, repeat it, listen to the translation, and repeat the phrase again and think of the link between the phrase and the translation.</p>
<p>The courses are made to be listened a lot of times (for instance while going on walks), make your memory work (mix of repetition and active recall), and get used to the sonorities of the language.</p>
<hr>
<h2>Courses</h2>"""


LANG_NAMES = {
    "en-US": "English",
    "fr-FR": "French",
    "cmn-CN": "Mandarin Chinese",
    "ru-RU": "Russian",
    "es-ES": "Spanish",
    "de-DE": "German",
    "hi-IN": "Hindi",
    "it-IT": "Italian",
}

tmp_current_lang = ""

# Iterate and parse each json file
for json_file in json_files:
    file_path = os.path.join(languages_dir, json_file)
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    possible_translations = {"en-US": [[AudioSegment.empty()], 0], "fr-FR": [[AudioSegment.empty()], 0]}

    course_name = data['course_name']
    language_category = LANG_NAMES.get(data['language_code'], data['language_code'])

    print(f"\n--- Processing {course_name} ({json_file}) ---\n")

    # html_content += f"""<hr><h2>{course_name} courses</h2><ul>"""

    pre_silence = AudioSegment.silent(duration=2500) # ms
    post_silence = AudioSegment.silent(duration=2500) # ms
    small_silence = AudioSegment.silent(duration=2500) # ms

    

    

    for i, sentence in enumerate(data['sentences']):
        target_audio_filename1 = sentence['sentence'][1]
        target_audio_filename2 = sentence['sentence'][2]

        if target_audio_filename1 != "" and target_audio_filename2 != "":

            target_audio_path1 = os.path.join(languages_dir, "individual_audios", target_audio_filename1)
            target_audio_path2 = os.path.join(languages_dir, "individual_audios", target_audio_filename2)

            if not os.path.exists(target_audio_path1) or not os.path.exists(target_audio_path2):
                print(f"WARNING: target audio file not found: {target_audio_path1}. Skipping this sentence.")
                continue

            # Load audios
            target_audio1 = AudioSegment.from_file(target_audio_path1)
            target_audio2 = AudioSegment.from_file(target_audio_path2)

            for language in possible_translations:

                #translation_filename = [t[2] for t in sentence['translations'] if t[0] == language][0]
                translation_filename = next((t[2] for t in sentence['translations'] if t[0] == language), None)
                    
                if translation_filename is not None and translation_filename != "":
                    translation_audio_path = os.path.join(languages_dir, "individual_audios", translation_filename)
                    
                    if not os.path.exists(translation_audio_path):
                        print(f"WARNING: translation audio file not found: {translation_audio_path}. Skipping this sentence.")
                        continue

                    translation_audio = AudioSegment.from_file(translation_audio_path)

                    combined_sentence_audio = target_audio2 + small_silence + target_audio1 + pre_silence + translation_audio + post_silence

                    possible_translations[language][1] += 1

                    if possible_translations[language][1] % 40 == 0:
                        possible_translations[language][0].append(AudioSegment.empty())
                    
                    possible_translations[language][0][-1] += combined_sentence_audio

    for language in possible_translations:
        if len(possible_translations[language][0][0]) > 10:
            tr_language_name = LANG_NAMES.get(language, language)

            page_url = f"courses/{json_file.removesuffix('.json')}_{language}_.html"

            if language_category != tmp_current_lang:
                if tmp_current_lang != "":
                    html_content += "</ul>"
                html_content += f"<h3>{language_category}</h3><ul>"
                tmp_current_lang = language_category

            html_content += f"""<li><a href="{page_url}"><b>{course_name}</b> for <i>{tr_language_name} speakers</i></a> ({possible_translations[language][1]} phrases)</li>"""

            page_html_content = f"""<!doctype html>
                <html lang="en">
                <head>
                    <meta charset="utf-8" />
                    <meta name="viewport" content="width=device-width" />
                    <title>Language learning audio phrases</title>
                    <link rel="stylesheet" href="../styles.css">
                </head>
                <body>
                <a href="../"><h1>Language learning audio phrases</h1></a>
                <h2><b>{course_name}</b> for {tr_language_name} speakers</h2>
                <p>Learn the basics of foreign languages with audio phrases, to communicate more easily around the world and make people smile.</p>
                <p>Listen to the phrase in the target language, repeat it, listen to the translation, and repeat the phrase again and think of the link between the phrase and the translation.</p>
                <p>The courses are made to be listened a lot of times (for instance while going on walks), make your memory work (mix of repetition and active recall), and get used to the sonorities of the language.</p>
                <hr>
                <p>({possible_translations[language][1]} phrases total)</p>
                """


            for z, split in enumerate(possible_translations[language][0]):

                # Export the final course audio
                output_filename = f"{json_file.removesuffix('.json')}_{tr_language_name.lower()}_{z}_course.mp3"
                output_filepath = os.path.join(output_audio_dir, output_filename)
                #site_output_filepath = os.path.join('course', output_filename)
                split = split.set_frame_rate(22050)
                split = split.set_sample_width(2)
                split.export(output_filepath, format="mp3", bitrate="128k")

                
                page_html_content += f"""<div class="audio-item">
                    <p><b>Part {z+1}</b></p>
                    <audio controls>
                        <source src="../audio_courses/{output_filename}" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                    </div></body>
                    </html>
                    """
                
            with open(f"_site/{page_url}", 'w', encoding='utf-8') as f:
                f.write(page_html_content)
            
            
            print(f"Successfully created course audio: {course_name}")

print("\nAll courses processed.")

html_content += """</ul><br><hr><small><p><a href="https://codeberg.org/anto4/audiophrases/">Open-source website</a></p></small></body>
</html>"""

with open("_site/index.html", 'w', encoding='utf-8') as f:
    f.write(html_content)
