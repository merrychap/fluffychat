'''
This module includes Encryptor class that provides
message encryption and decryption
'''


import json
import Crypto

from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256


class Encryptor:
    def __init__(self):
        self.key_length = 1024
        self.random_gen = Random.new().read
        self.user2pubkey = {}

        self._generate_keys()

    def add_pubkey(self, user_id, pubkey):
        ''' Add public key of a host in chat to the dictionary '''
        self.user2pubkey[user_id] = pubkey

    def _generate_keys(self):
        ''' Generate private/public RSA keys '''

        self._keypair = RSA.generate(self.key_length, self.random_gen)
        self.pubkey = self.keypair.publickey()

    def encrypt(self, user_id, message):
        '''
        Encrypt sending message with RSA

        Args:
            user_id (int) Id of a user that receives message
            message (bytes) Message itself
        Return:
            tuple First is signature and second is encrypted message itself
        '''

        # if message isn't bytes then convert it
        try:
            bytes(message)
        except TypeError:
            message = bytes(message, 'utf-8')

        message_hash = SHA256.new(message).digest()
        signature = self.user2pubkey[user_id].sign(message_hash, '')
        encrypted_msg = self.user2pubkey[user_id].encrypt(message, 32)

        return json.dumps({
            'signature': signature,
            'encrypted_msg': encrypted_msg})

    def decrypt(self, signature, encrypted_msg):
        '''
        Decrypt received message. If this message can't be verified then
        return None

        Args:
            encrypted_msg (bytes) Encrypted message from a user in the chat
        Return:
            None if message isn't verified else decrypted message
        '''

        decrypted_msg = self._keypair.decrypt(encrypted_msg)
        decrypted_msg_hash = SHA256.new(decrypted_msg).digest()

        if self.verify(decrypted_msg_hash, signature):
            return decrypted_msg


    def verify(self, _hash, sign):
        ''' Verify message hash by signature '''
        return self.pubkey.verify(_hash, sign)

    def save_key(self, key):
        pass


# if __name__ == '__main__':
#     KEY_LENGTH = 1024
#     random_gen = Random.new().read
#
#     keypair_first  = RSA.generate(KEY_LENGTH, random_gen)
#     keypair_second = RSA.generate(KEY_LENGTH, random_gen)
#
#     pubkey_first  = keypair_first.publickey()
#     pubkey_second = keypair_second.publickey()
#
#     message_to_first  = 'hello, first'
#     message_to_second = 'hello, second'
#
#     hash_of_first_message = SHA256.new(message_to_first.encode()).digest()
#     signature_second = keypair_second.sign(hash_of_first_message, '')
#
#     hash_of_second_message = SHA256.new(message_to_second.encode()).digest()
#     signature_first = keypair_first.sign(hash_of_second_message, '')
#
#     encrypted_for_first  = pubkey_first.encrypt(message_to_first.encode(), 32)
#     encrypted_for_second = pubkey_second.encrypt(message_to_second.encode(), 32)
#
#     decrypt_first  = keypair_first.decrypt(encrypted_for_first)
#     decrypt_second = keypair_second.decrypt(encrypted_for_second)
#
#     hash_first_decrypt = SHA256.new(decrypt_first).digest()
#     if pubkey_second.verify(hash_first_decrypt, signature_second):
#         print(decrypt_first)
