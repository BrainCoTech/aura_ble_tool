import socket
import logging
import threading

logger = logging.getLogger(__name__)


class TcpClient(object):
    def __init__(self, on_connection=None, on_message=None):
        self._on_connection = on_connection
        self._on_message = on_message
        self._sock = None
        self._ip = None
        self._port = None
        self._keep_running = False
        self._server_connected = False
        self._tcp_thread = None

    def _run_tcp_client(self, ip, port):
        while self._keep_running:
            if not self._server_connected:
                self._init_socket(ip, port)
            else:
                try:
                    data = self._sock.recv(1024)
                    if data != b'':
                        if self._on_message is not None:
                            self._on_message(data)
                except Exception as e:
                    logger.info("connection closed: {}".format(e))
                    self._sock.close()
                    if self._on_connection is not None:
                        self._on_connection(False)
                    self._server_connected = False
        if self._on_connection is not None:
            self._on_connection(False)

    def _init_socket(self, ip, port):
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.connect((ip, port))
            self._server_connected = True
            if self._on_connection is not None:
                self._on_connection(True)
        except Exception as e:
            self._server_connected = False
            if "WinError 10061" not in str(e):
                logger.error(e, exc_info=True)

    def write(self, bytes_to_write):
        if self._server_connected:
            try:
                self._sock.send(bytes_to_write)
                logger.debug("sent: {}".format(bytes_to_write))
            except Exception as e:
                logger.error(e, exc_info=True)

    def connect_to_server(self, ip, port):
        self._keep_running = True
        self._server_connected = False
        self._tcp_thread = threading.Thread(target=self._run_tcp_client, args=(ip, port), daemon=True)
        self._tcp_thread.start()

    def close(self):
        self._keep_running = False
        self._sock.close()
        self._server_connected = False

    def is_connected(self):
        return self._server_connected

