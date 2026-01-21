"""
Encryption utilities for end-to-end encryption of sensitive data.
"""

import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from base64 import b64encode, b64decode
from flask import current_app


def get_encryption_key():
    """Derive encryption key from SECRET_KEY."""
    secret_key = current_app.config['SECRET_KEY'].encode()
    salt = b'CommunityWatch_salt'  # Fixed salt for consistency
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(secret_key)


def encrypt_data(data: str) -> str:
    """Encrypt a string and return base64 encoded ciphertext."""
    if not data:
        return data

    key = get_encryption_key()
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Pad data to block size
    block_size = 16
    padded_data = data.encode('utf-8')
    padding_length = block_size - (len(padded_data) % block_size)
    padded_data += bytes([padding_length]) * padding_length

    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return b64encode(iv + ciphertext).decode('utf-8')


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt base64 encoded ciphertext and return string."""
    if not encrypted_data:
        return encrypted_data

    key = get_encryption_key()
    try:
        encrypted_bytes = b64decode(encrypted_data)
        iv = encrypted_bytes[:16]
        ciphertext = encrypted_bytes[16:]

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()

        # Remove padding
        padding_length = padded_data[-1]
        data = padded_data[:-padding_length]
        return data.decode('utf-8')
    except Exception as e:
        current_app.logger.error(f"Decryption failed: {e}")
        return encrypted_data  # Return as-is if decryption fails


def encrypt_file(file_path: str) -> None:
    """Encrypt a file in place."""
    key = get_encryption_key()
    iv = os.urandom(16)

    with open(file_path, 'rb') as f:
        data = f.read()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Pad data
    block_size = 16
    padding_length = block_size - (len(data) % block_size)
    data += bytes([padding_length]) * padding_length

    ciphertext = encryptor.update(data) + encryptor.finalize()

    with open(file_path, 'wb') as f:
        f.write(iv + ciphertext)


def decrypt_file(file_path: str) -> bytes:
    """Decrypt a file and return the decrypted bytes."""
    key = get_encryption_key()

    with open(file_path, 'rb') as f:
        encrypted_data = f.read()

    iv = encrypted_data[:16]
    ciphertext = encrypted_data[16:]

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    # Remove padding
    padding_length = padded_data[-1]
    return padded_data[:-padding_length]