from pathlib import Path

import requests


def test_endpoint(url: str, m4a_path: str, smart_mode: bool):
    with open(m4a_path, 'rb') as f:
        print(f"File size: {len(f.read())} bytes")  # Check the size before sending
        f.seek(0)
        files = {'m4a_file': (m4a_path.split("/")[-1], f)}
        response = requests.post(url, files=files, data={'smart_mode': smart_mode})

    if response.status_code == 200:
        print(response.json()['transcript'])
    else:
        print("Error:", response.json()['error'])


# Test
if __name__ == "__main__":
    test_endpoint(
        "http://0.0.0.0:8000/recognise",
        str(Path(__file__).parent / "data" / "test_speech.mp3"),
        True
    )
