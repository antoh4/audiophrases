import json
import os
from pydub import AudioSegment
from dotenv import load_dotenv
from google.cloud import texttospeech
from google.api_core.exceptions import ResourceExhausted
import datetime
import random
import string
import time

load_dotenv()

languages_dir = 'languages'

def synthesize(text: str, language_code: str, output_filepath: str, is_translation: bool=False, voice: str="Iapetus"):
    """Synthesizes speech from the input text and saves it to an MP3 file.

    Args:
        text: The text to synthesize.
        output_filepath: The path to save the generated audio file.
          Defaults to "output.mp3".
    """
    client = texttospeech.TextToSpeechClient()

    # if is_translation:
    #     synthesis_input = texttospeech.SynthesisInput(text=text)
    # else:
    #     synthesis_input = texttospeech.SynthesisInput(text=text, prompt="Read aloud in a clear tone.")
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Select the voice you want to use.
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice,
        model_name="gemini-2.5-flash-tts"
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    
    # Simple retry with exponential backoff
    max_retries = 3
    wait_time = 5
    
    for attempt in range(max_retries):
        try:
            response = client.synthesize_speech(
                input=synthesis_input, 
                voice=voice, 
                audio_config=audio_config
            )
            
            with open(output_filepath, "wb") as out:
                out.write(response.audio_content)
                print(f"Audio content written to file: {output_filepath}")
            
            # Small delay between successful requests
            time.sleep(10)
            return  # Success, exit function
            
        except ResourceExhausted as e:
            if attempt < max_retries - 1:
                print(f"Quota exhausted. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                time.sleep(wait_time)
                wait_time *= 2  # Exponential backoff
            else:
                print(f"Failed after {max_retries} attempts. Quota exhausted.")
                raise


timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


# List all json files in the languages directory
json_files = sorted([f for f in os.listdir(languages_dir) if f.endswith('.json')])


print(f"Found {len(json_files)} JSON files in '{languages_dir}': {json_files}\n")

# Iterate and parse each json file
for json_file in json_files:
    file_path = os.path.join(languages_dir, json_file)
    with open(file_path, 'r') as file:
        data = json.load(file)

    course_name = data['course_name']
    language_code = data['language_code']
    print(f"\n--- Processing {course_name} ({json_file}) ---\n")

    course_audio = AudioSegment.empty()

    for i, entry in enumerate(data['sentences']):
        sentence_content = entry["sentence"][0]
        sentence_file1 = entry["sentence"][1]
        sentence_file2 = entry["sentence"][2]

        sentence_file_path1 = os.path.join(languages_dir, "individual_audios", sentence_file1)
        sentence_file_path2 = os.path.join(languages_dir, "individual_audios", sentence_file2)

        if sentence_content != "" and (sentence_file1 == "" or not os.path.exists(sentence_file_path1)):
            print(f"sentence audio file not found: {sentence_content}. We generate this sentence.")

            output_filename = f"{json_file}_{i}_t1_{timestamp}.mp3"
            sentence_file_path1 = os.path.join(languages_dir, "individual_audios", output_filename)

            synthesize(text=sentence_content, language_code=language_code, output_filepath=sentence_file_path1, voice="Iapetus")

            data['sentences'][i]["sentence"][1] = output_filename

        if sentence_content != "" and (sentence_file2 == "" or not os.path.exists(sentence_file_path2)):
            print(f"sentence audio file not found: {sentence_content}. We generate this sentence.")

            output_filename = f"{json_file}_{i}_t2_{timestamp}.mp3"
            sentence_file_path2 = os.path.join(languages_dir, "individual_audios", output_filename)

            synthesize(text=sentence_content, language_code=language_code, output_filepath=sentence_file_path2, voice="Erinome")

            data['sentences'][i]["sentence"][2] = output_filename


        for y, translation in enumerate(entry['translations']):
            translation_language_code = translation[0]
            translation_content = translation[1]
            translation_file = translation[2]

            translation_file_path = os.path.join(languages_dir, "individual_audios", translation_file)

            if translation_content != "" and (translation_file == "" or not os.path.exists(translation_file_path)):
                print(f"translation audio file not found: {translation_content}. We generate this translation.")

                output_filename = f"{json_file}_{i}_{y}_{timestamp}.mp3"
                translation_file_path = os.path.join(languages_dir, "individual_audios", output_filename)
                
                synthesize(text=translation_content, language_code=translation_language_code, output_filepath=translation_file_path, is_translation=True)
                
                data['sentences'][i]["translations"][y][2] = output_filename
        

        # we save the updates at each sentence. to avoid losing some generations. but not saving at each translation either
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
