import hashlib


def calculate_sha256(file_stream) -> str:
    file_stream.seek(0)
    sha256 = hashlib.sha256()
    for chunk in iter(lambda: file_stream.read(8192), b""):
        sha256.update(chunk)
    file_stream.seek(0)
    return sha256.hexdigest()
