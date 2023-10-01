import tempfile

import openai
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def generate_corrected_transcript(text: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": """You are an AI tool for fixing recognised text.
The next message from user is a result of voice recognition. It contain text user wanted to be recognised, but also it may contain some commands user wanted to apply to the recognised text. You need to answer with the text user wanted to be recognised with following editions:
1. Some words may be recognised incorrectly, if you think it is the case, fix them.
2. Fix grammar and punctuation.
3. If there are some commands, apply them to text and remove commands from the text.
4. Do not include any comments from you, only answer with fixed text."""
            },
            {
                "role": "user",
                "content": text
            }
        ]
    )
    return response['choices'][0]['message']['content']


def recognise_speech(m4a_file_path, smart_mode: bool):
    audio_file = open(m4a_file_path, "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)["text"]
    if smart_mode:
        transcript = generate_corrected_transcript(transcript)
    return transcript


app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


@app.route('/recognise', methods=['POST'])
@limiter.limit("10 per minute")
def recognise_endpoint():
    if 'm4a_file' not in request.files or 'smart_mode' not in request.form:
        print("error missing m4a_file or smart_mode parameter")
        return jsonify({'error': 'Missing m4a_file or smart_mode parameter'}), 400

    try:
        m4a_file = request.files['m4a_file']
        smart_mode = request.form['smart_mode'].lower() == 'true'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".m4a")
        m4a_file.save(temp_file.name)
        temp_file.flush()
        transcript = recognise_speech(temp_file.name, smart_mode)
        temp_file.close()
    except Exception as e:
        print(f"error {str(e)}")
        return jsonify({'error': 'Error during recognition.'}), 400
    print("Successful recognition")
    return jsonify({'transcript': transcript})


if __name__ == '__main__':
    app.run(debug=False)
