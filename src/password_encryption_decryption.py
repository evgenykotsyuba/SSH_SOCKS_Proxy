from cryptography.fernet import Fernet
import base64
import os

salt = b'\xa3\xe3\x85h#\x10\xd1\xa7\xeay\x81E\xaaw\xd7\x82'
# salt = generate_salt()


# def generate_salt(length=16):
#     """
#     Generates a random salt of the specified length.
#
#     :param length: Length of the salt in bytes
#     :return: Generated salt
#     """
#     return os.urandom(length)


def encrypt_password(password, salt):
    """
    Encrypts a password using the provided salt.

    :param password: Password to encrypt
    :param salt: Salt to use for encryption
    :return: Encrypted password
    """
    # Convert the password to bytes if it is a string
    if isinstance(password, str):
        password = password.encode('utf-8')

    # Combine the password and salt
    salted_password = salt + password

    # Generate a key based on the salt
    key = base64.urlsafe_b64encode(salt + b'0' * (32 - len(salt)))

    # Create a Fernet object for encryption
    fernet = Fernet(key)

    # Encrypt the password
    encrypted_password = fernet.encrypt(salted_password)

    return encrypted_password


def decrypt_password(encrypted_password, salt):
    """
    Decrypts a password using the provided salt.

    :param encrypted_password: Encrypted password
    :param salt: Salt used during encryption
    :return: Decrypted password
    """
    # Generate a key based on the salt
    key = base64.urlsafe_b64encode(salt + b'0' * (32 - len(salt)))

    # Create a Fernet object for decryption
    fernet = Fernet(key)

    # Decrypt the password
    decrypted_salted_password = fernet.decrypt(encrypted_password)

    # Remove the salt from the beginning of the password
    decrypted_password = decrypted_salted_password[len(salt):]

    return decrypted_password
