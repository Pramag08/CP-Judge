"""C11 private readiness channel; deliberately separate from the DMOJ protocol.

The operator starts the trusted verifier inside the existing pinned worker. No
Docker socket, data-transfer API or participant-visible manifest is exposed.
"""
import hashlib
import hmac
import json
import socket
import struct

MAX_FRAME = 2 * 1024 * 1024
ADDRESS = ('127.0.0.1', 9994)
DOMAIN = b'cpjudge-readiness-v1\0'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def seal(value, key):
    return {'body': value, 'mac': hmac.new(key.encode(), DOMAIN + canonical(value), hashlib.sha256).hexdigest()}


def unseal(value, key):
    if set(value) != {'body', 'mac'} or not hmac.compare_digest(
            value['mac'], seal(value['body'], key)['mac']):
        raise ValueError('Unauthenticated readiness message')
    return value['body']


def read_frame(stream):
    def exactly(size):
        output = bytearray()
        while len(output) < size:
            data = stream.recv(size-len(output))
            if not data:
                raise ValueError('Incomplete readiness message')
            output.extend(data)
        return bytes(output)
    size = struct.unpack('!I', exactly(4))[0]
    if not 0 < size <= MAX_FRAME:
        raise ValueError('Readiness message exceeds bound')
    return json.loads(exactly(size))


def write_frame(stream, value):
    data = canonical(value)
    if len(data) > MAX_FRAME:
        raise ValueError('Readiness message exceeds bound')
    stream.sendall(struct.pack('!I', len(data)) + data)


def request(body, key, address=ADDRESS):
    with socket.create_connection(address, timeout=8) as stream:
        stream.settimeout(8)
        write_frame(stream, seal(body, key))
        return unseal(read_frame(stream), key)
