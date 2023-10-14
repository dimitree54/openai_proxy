import tempfile
import openai
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from typing import Tuple


class TranscriptGenerator:
    def __init__(self):
        self.model = "gpt-4"
        self.temperature = 0

    def generate_corrected_transcript(self, text: str) -> str:
        response = openai.ChatCompletion.create(
            model=self.model,
            temperature=self.temperature,
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


class SpeechRecognizer:
    def __init__(self, smart_mode: bool):
        self.smart_mode = smart_mode
        self.transcript_generator = TranscriptGenerator()

    def recognise_speech(self, m4a_file_path: str) -> str:
        with open(m4a_file_path, "rb") as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)["text"]
        if self.smart_mode:
            transcript = self.transcript_generator.generate_corrected_transcript(transcript)
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
def recognise_endpoint() -> Tuple[str, int]:
    if 'm4a_file' not in request.files or 'smart_mode' not in request.form:
        app.logger.error("Missing m4a_file or smart_mode parameter")
        return jsonify({'error': 'Missing m4a_file or smart_mode parameter'}), 400
    try:
        m4a_file = request.files['m4a_file']
        smart_mode = request.form['smart_mode'].lower() == 'true'
        with tempfile.NamedTemporaryFile(delete=True, suffix=".m4a") as temp_file:
            m4a_file.save(temp_file.name)
            temp_file.flush()
            recognizer = SpeechRecognizer(smart_mode)
            transcript = recognizer.recognise_speech(temp_file.name)
    except Exception as e:
        app.logger.error(f"Error during recognition: {str(e)}")
        return jsonify({'error': 'Error during recognition.'}), 400
    app.logger.info("Successful recognition")
    return jsonify({'transcript': transcript})


if __name__ == '__main__':
    app.run(debug=False)
