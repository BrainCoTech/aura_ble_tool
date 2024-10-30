import logging
import json
import time
import numpy as np
from threading import Thread, Timer
from datetime import datetime
from queue import SimpleQueue, Empty

from mindray.client import TcpClient

logger = logging.getLogger(__name__)


monitor_ip = '192.168.0.122'
monitor_port = 4601


class MindaryMonitor(object):
    def __init__(self, buffer_size):
        super(MindaryMonitor).__init__()
        self.monitor = TcpClient(on_connection=self.on_connected, on_message=self.on_message)
        self.monitor.connect_to_server(monitor_ip, monitor_port)

        self.hr_buffer = [np.nan] * buffer_size
        self.pvc_buffer = [np.nan] * buffer_size
        self.rr_buffer = [np.nan] * buffer_size
        self.spo2_buffer = [np.nan] * buffer_size
        self.pr_buffer = [np.nan] * buffer_size

        self._received_messages = SimpleQueue()
        self._message_parser = Thread(target=self._parse_mindray_message, daemon=True)
        self._message_parser.start()

        self.data_file_name = ""
        # from mindray.mindray_widget import MindrayWidget
        # self.widget = MindrayWidget()
        # self.widget.show()

    def disconnect(self):
        self.monitor.close()

    def is_connected(self):
        return self.monitor.is_connected()

    def on_connected(self, connected):
        logger.info(f'monitor connected {connected}')
        timer = Timer(5, self._send_query_msg)
        timer.start()

    def on_message(self, message):
        try:
            self._received_messages.put(message)
        except Exception as e:
            logger.error(e, exc_info=True)

    def _parse_mindray_message(self):
        while True:
            try:
                message = self._received_messages.get(timeout=0.2)
                messages = []
                current_msg = []
                for b in message:
                    if b == 0x0b:  # start
                        current_msg = [b]
                    elif len(current_msg):
                        if b == 0x0d and current_msg[-1] == 0x1c:  # end
                            messages.append(bytes(current_msg[1:-1]))
                            current_msg.clear()
                        else:
                            current_msg.append(b)
                for m in messages:
                    self._parse_hl7_msg(m)
            except Empty:
                pass
            except Exception as e:
                logger.error(e, exc_info=True)

    def _send_tcp_connection_msg(self):
        msh = b'MSH|^~\&|||||||QRY^R02|' + b'160' + b'|P|2.3.1\r'
        msg = bytes([0x0b]) + msh + bytes([0x1c, 0x0d])
        self.monitor.write(msg)

    def _send_query_msg(self):
        msh = b'MSH|^~\&|||||||QRY^R02|1203|P|2.3.1|\r'

        time_stamp = datetime.now().strftime('%Y%m%d%H%M%S').encode()
        qry_id = b'Query0'
        qrd = b'QRD|'+ time_stamp + b'|R|I|' + qry_id + b'|||||RES\r'

        ip32 = b'0'       # not required for bedside monitor
        send_type = b'1'  # physiological parameters
        send_freq = b'1'  # second
        send_all = b'0'
        # qry_list = b'101&102&151&160&161'  # HR, PVCs, RespirationRate, SPO2, PulseRate
        qry_list = b'101&161'  # HR, PulseRate
        # QRF|MON||||<IP>&<IPSeq>^<SendType>^<SendFreq>^<SendAll>^<List>
        qrf = b'QRF|MON||||' + ip32 + b'&0^' + send_type + b'^' + send_freq + b'^' + send_all + b'^' + qry_list + b'\r'
        qry = bytes([0x0b]) + msh + qrd + qrf + bytes([0x1c, 0x0d])
        logger.info(f'send query: {qry}')
        self.monitor.write(qry)

    def _parse_hl7_msg(self, msg):
        for segment in msg.split(b'\r'):
            if len(segment) == 0:
                continue
            segment = segment.decode(encoding='gbk')
            fields = segment.split('|')
            if fields[0] == 'MSH':
                if int(fields[9]) == 106:
                    self._send_tcp_connection_msg()
            elif fields[0] == 'OBX':
                if fields[2] == 'NM':
                    logger.info(" ".join(fields))
                    for key, buffer in zip(['101^HR', '102^PVCs', '151^RR', '160^SpO2', '161^PR'],
                                           [self.hr_buffer, self.pvc_buffer, self.rr_buffer, self.spo2_buffer, self.pr_buffer]):
                        if fields[3] == key:
                            buffer.pop(0)
                            value = int(fields[5])
                            buffer.append(value if value != -100 else np.nan)

                            if self.data_file_name != "":
                                save_data_to_file("{}_mindray.txt".format(self.data_file_name), {key: value})


def save_data_to_file(file_name, data_dict):
    with open(file_name, 'a') as f:
        data_dict["time"] = time.time()
        json.dump(data_dict, f)
        f.write("\n")