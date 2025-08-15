import base64
import hashlib
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

class Crypter:

    secret_key = os.getenv("SECRET_KEY", "")
    secret_iv = os.getenv("SECRET_IV", "")
    method = os.getenv("CRYPTER_METHOD", "")
    
    @staticmethod
    def encrypt_aes(value: str) -> str:
        key_hash = hashlib.sha256(Crypter.secret_key.encode()).hexdigest()
        key = key_hash[:32].encode('utf-8')  # Primeros 32 chars como UTF-8 (32 bytes)

        iv_hash = hashlib.sha256(Crypter.secret_iv.encode()).hexdigest()
        iv_string = iv_hash[:16]  # Primeros 16 caracteres como string
        iv = iv_string.encode('utf-8')  # Convertir string a bytes UTF-8 (16 bytes)
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        padded_data = pad(value.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        
        first_b64 = base64.b64encode(encrypted).decode()
        return base64.b64encode(first_b64.encode()).decode()
    
    @staticmethod
    def decrypt_aes(value: str) -> str:
        key_hash = hashlib.sha256(Crypter.secret_key.encode()).hexdigest()
        key = key_hash[:32].encode('utf-8')
        
        iv_hash = hashlib.sha256(Crypter.secret_iv.encode()).hexdigest()
        iv_string = iv_hash[:16]
        iv = iv_string.encode('utf-8')
        
        # Decodificar el doble base64 (como hace PHP)
        first_decode = base64.b64decode(value).decode()
        encrypted = base64.b64decode(first_decode)
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_padded = cipher.decrypt(encrypted)
        return unpad(decrypted_padded, AES.block_size).decode()