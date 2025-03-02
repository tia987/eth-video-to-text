import requests

def download_video(url, output_path):
    """Downloads video using requests instead of wget."""
    response = requests.get(url, stream=True)
    with open(output_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)