import logging
import socket
from urllib.parse import urlparse

OPTIONS = 'OPTIONS'
DESCRIBE = 'DESCRIBE'
SETUP = 'SETUP'
PLAY = 'PLAY'

buf_size = 4096

class RTSPClient():

    def __init__(self, url: str):
        self.url = url
        self.parsed_url = urlparse(url)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.parsed_url.hostname, self.parsed_url.port))
        self.recv_buf = b''

        self.cseq = 0
        self.session = ''
        self.sps = b''
        self.pps = b''

        self.option()
        self.describe()
        self.setup()
        self.play()
 
    def read_packet(self):
        pass
       

    def option(self):
        self.sock.sendall(self._construct_request_header(OPTIONS))
        headers, _ = self._get_rtsp()
        logging.debug(headers)


    def describe(self):
        self.sock.sendall(self._construct_request_header(DESCRIBE))
        headers, content = self._get_rtsp()
        logging.debug(headers)
        logging.debug(content)


    def setup(self):
        self.sock.sendall(self._construct_request_header(SETUP))
        headers, _ = self._get_rtsp()
        logging.debug(headers)
        self.session = headers['Session'].split(';')[0]


    def play(self):
        self.sock.sendall(self._construct_request_header(PLAY))
        headers, _ = self._get_rtsp_over_tcp()
        logging.debug(headers)
        self._get_rtp_over_tcp()
        self._get_rtp_over_tcp()
        self._get_rtp_over_tcp()
        self._get_rtp_over_tcp()
        self._get_rtp_over_tcp()
        self._get_rtp_over_tcp()
        self._get_rtp_over_tcp()


    def _construct_request_header(self, method: str) -> bytearray:
        self.cseq += 1

        header = '{} {} RTSP/1.0\r\nCSeq: {}\r\n'.format(method, self.url, self.cseq)
        if method == DESCRIBE:
            header += 'Accept: application/sdp\r\n'
        if method == SETUP:
            header += 'Transport: RTP/AVP/TCP\r\n'
        if method == PLAY:
            header += 'Session: {}\r\n'.format(self.session)
        header += '\r\n'

        return header.encode()

    def _get_rtsp(self) -> (dict, str):
        ''' 
        read socket, return rtsp headers and content
        ''' 
        rtsp = self._get_buf_until(b'\r\n\r\n')

        headers = rtsp.decode().split('\r\n')
        if headers[0] != 'RTSP/1.0 200 OK':
            logging.error('exception rtsp response ' + rtsp)
        
        headers_dict = {}
        for header in headers[1:]:
            k, v = header.split(': ')    
            headers_dict[k] = v
        
        content = ''
        if 'Content-Length' in headers_dict:
            l = int(headers_dict['Content-Length'])
            content = self._get_buf_by_size(l)

        return headers_dict, content


    def _get_rtsp_over_tcp(self):
        meta = self._get_buf_by_size(4)
        _, _, length = meta[0], meta[1], meta[2:4]
        self._get_buf_by_size(int.from_bytes(length, "big"))

        return self._get_rtsp()


    def _get_rtp_over_tcp(self):
        meta = self._get_buf_by_size(4)
        _, channel, length = meta[0], meta[1], meta[2:4]

        rtp = self._get_buf_by_size(int.from_bytes(length, 'big'))
    
        if channel == 1:
            logging.info("receive rtcp")

   
        rtp_header = rtp[:12]
        rtp_payload_offset = rtp_header[0] & 0xf * 4
        # rtp_sequence = int.from_bytes(rtp_header[2:4], 'big')

        rtp_payload = rtp[12+rtp_payload_offset:]

        #zero = rtp_payload[0] & 0x80
        #logging.info(zero)

        nalu_type = rtp_payload[0] & 0x1f

        logging.info(nalu_type)

        if nalu_type >= 1 and nalu_type <= 5:
            pass
        elif nalu_type == 6:
            pass
        elif nalu_type == 7:
            self.sps = rtp_payload
        elif nalu_type == 8:
            self.pps = rtp_payload
        elif nalu_type == 28: # FU-A
            pass


    def _get_buf_by_size(self, l: int) -> bytes:
        while True:
            if len(self.recv_buf) >= l:
                content, self.recv_buf= self.recv_buf[:l], self.recv_buf[l:]
                return content
            else:
                more = self.sock.recv(buf_size)
                self.recv_buf += more

    def _get_buf_until(self, b: bytes) -> bytes:
        while True:
            index = self.recv_buf.find(b)
            if index != -1:
                content = self.recv_buf[:index]
                self.recv_buf = self.recv_buf[index+len(b):]
                return content

            more = self.sock.recv(buf_size)
            self.recv_buf += more

   


logging.basicConfig(level = logging.DEBUG,format = '%(asctime)s %(pathname)s %(funcName)s %(lineno)d %(levelname)s \n%(message)s\n')
logger = logging.getLogger(__name__)

c = RTSPClient('rtsp://192.168.0.107:8554/test.264')
c.read_packet()