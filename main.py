import json
import os
from pydub import AudioSegment
from pydub.silence import *
import shutil
from datetime import datetime, timezone

languages_dir = 'languages'
output_audio_dir = '_site/audio_courses'

# we remove the old audio courses and recreate the folder. as we will regenerate the courses
shutil.rmtree(output_audio_dir, ignore_errors=True)
# Ensure output directories exist
os.makedirs(output_audio_dir, exist_ok=True)


# # we read the old courses.json file to check if we need to regenerate some courses or not
# with open("_site/courses.json", 'r') as file:
#     old_courses_data = json.load(file)


# we create a new courses.json file, but won't save it if there are no updates? or we update either way
courses = {}
courses["lastUpdated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
courses["courses"] = []

# course = {
#     "id": i,
#     "name": f"Product {i}",
#     "price": round(9.99 * i, 2),
#     "tags": [f"tag{i}a", f"tag{i}b"],
    # "id": "spanish-basics",
    # "title": "Spanish Basics",
    # "language": "es",
    # "description": "A beginner course covering everyday Spanish.",
    # "thumbnail": "/courses/spanish-basics/thumbnail.jpg",
    # "version": 2,
    # "lessons": 12,
    # "totalSizeMB": 45.2,
    # "audioBaseUrl": "/courses/spanish-basics/audio/"
# }
# courses["courses"].append(course)

# List all json files in the languages directory
json_files = sorted([f for f in os.listdir(languages_dir) if f.endswith('.json')])

print(f"Found {len(json_files)} JSON files in '{languages_dir}': {json_files}\n")


LANG_NAMES = {
    "en-US": "English",
    "fr-FR": "French",
    "cmn-CN": "Mandarin Chinese",
    "ru-RU": "Russian",
    "es-ES": "Spanish",
    "de-DE": "German",
    "hi-IN": "Hindi",
    "ar-EG": "Egyptian Arabic",
    "tr-TR": "Turkish",
    "it-IT": "Italian",
    "vi-VN": "Vietnamese",
    "fil-PH": "Filipino",
    "ja-JP": "Japanese",
    "ko-KR": "Korean",
}

phrases_per_audio = 30

# Iterate and parse each json file
for json_file in json_files:
    file_path = os.path.join(languages_dir, json_file)
    with open(file_path, 'r') as file:
        data = json.load(file)

    slug = json_file.removesuffix('.json')

    #old_version = next((c.get("version") for c in data.get("courses", []) if c.get("id") == f"{slug}_{language}"), None)
    
    possible_translations = {"en-US": [[AudioSegment.empty()], 0, False], "fr-FR": [[AudioSegment.empty()], 0, False]}

    course_name = data['course_name']

    print(f"\n--- Processing {course_name} ({json_file}) ---\n")

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

                    if possible_translations[language][1] % phrases_per_audio == 0:
                        possible_translations[language][0].append(AudioSegment.empty())
                    
                    possible_translations[language][0][-1] += combined_sentence_audio

    for language in possible_translations:
        if len(possible_translations[language][0][0]) > 10:
            tr_language_name = LANG_NAMES.get(language, language)

            for z, split in enumerate(possible_translations[language][0]):

                # Export the final course audio
                output_filename = f"{slug}_{language}_{z+1}_course.mp3"
                output_filepath = os.path.join(output_audio_dir, output_filename)
                #site_output_filepath = os.path.join('course', output_filename)
                split = split.set_frame_rate(22050)
                split = split.set_sample_width(2)
                split.export(output_filepath, format="mp3", bitrate="128k")
            
            course = {
                "id": f"{slug}_{language}",
                "title": data['course_name'],
                "language": data['language_code'],
                "translation": language,
                #"description": "A beginner course covering everyday Spanish.",
                #"thumbnail": "/courses/spanish-basics/thumbnail.jpg",
                "version": data['version'],
                #"lessons": 12,
                #"totalSizeMB": 45.2,
                #"audioBaseUrl": "/courses/spanish-basics/audio/"
            }
            courses["courses"].append(course)

            print(f"Successfully created audio course: {tr_language_name} -> {course_name}")

print("\nAll courses processed.")

with open("_site/courses.json", "w") as f:
    json.dump(courses, f, indent=2)
