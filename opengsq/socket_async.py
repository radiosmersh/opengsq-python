import asyncio
import socket
from enum import Enum, auto


class SocketKind(Enum):
    SOCK_STREAM = auto()
    SOCK_DGRAM = auto()


class SocketAsync():
    @staticmethod
    async def send_and_receive(host: str, port: int, timeout: float, data: bytes, kind=SocketKind.SOCK_DGRAM):
        with SocketAsync(kind) as sock:
            sock.settimeout(timeout)
            await sock.connect((host, port))
            sock.send(data)
            return await sock.recv()

    @staticmethod
    def gethostbyname(hostname: str) -> str:
        return socket.gethostbyname(hostname)

    def __init__(self, kind: SocketKind = SocketKind.SOCK_DGRAM):
        self.__timeout = None
        self.__transport = None
        self.__protocol = None
        self.__kind = kind

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def settimeout(self, value: float):
        self.__timeout = value

    async def connect(self, remote_addr):
        await asyncio.wait_for(self.__connect(remote_addr), timeout=self.__timeout)

    async def __connect(self, remote_addr):
        loop = asyncio.get_running_loop()
        self.__protocol = self.__Protocol(self.__timeout)

        if self.__kind == SocketKind.SOCK_STREAM:
            self.__transport, _ = await loop.create_connection(
                lambda: self.__protocol,
                host=remote_addr[0],
                port=remote_addr[1],
            )
        else:
            self.__transport, _ = await loop.create_datagram_endpoint(
                lambda: self.__protocol,
                remote_addr=remote_addr,
            )

    def close(self):
        if self.__transport:
            self.__transport.close()

    def send(self, data: bytes):
        if self.__kind == SocketKind.SOCK_STREAM:
            self.__transport.write(data)
        else:
            self.__transport.sendto(data)

    async def recv(self) -> bytes:
        return await self.__protocol.recv()

    class __Protocol(asyncio.Protocol):
        def __init__(self, timeout: float):
            self.__packets = asyncio.Queue()
            self.__timeout = timeout

        async def recv(self):
            return await asyncio.wait_for(self.__packets.get(), timeout=self.__timeout)

        def connection_made(self, transport):
            pass

        def connection_lost(self, exc):
            pass

        # Streaming Protocols
        def data_received(self, data):
            """Called when some data is received. data is a non-empty bytes object containing the incoming data."""
            self.__packets.put_nowait(data)

        # Streaming Protocols
        def eof_received(self):
            """
            Called when the other end signals it won't send any more data
            (for example by calling transport.write_eof(), if the other end also uses asyncio).
            """
            pass

        # Datagram Protocols
        def datagram_received(self, data, addr):
            """Called when some datagram is received."""
            self.__packets.put_nowait(data)

        # Datagram Protocols
        def error_received(self, exc):
            """Called when a previous send or receive operation raises an OSError. exc is the OSError instance."""
            pass


if __name__ == '__main__':
    async def test_socket_async():
        with SocketAsync() as socket_async:
            socket_async.settimeout(5)
            await socket_async.connect(('122.128.109.245', 27015))
            socket_async.send(b'\xFF\xFF\xFF\xFFTSource Engine Query\x00\xFF\xFF\xFF\xFF')
            print(await socket_async.recv())

    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_socket_async())
    loop.close()
