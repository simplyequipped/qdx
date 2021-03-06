import os, threading, time
import pexpect
from pexpect.popen_spawn import PopenSpawn


class MiniModem:
    RX = 'rx'
    TX = 'tx'
    MODES = [RX, TX]

    def __init__(self, mode, alsa_dev, baudrate=300, start=True):

        if mode in MiniModem.MODES:
            self.mode = mode
        else:
            raise Exception('Unknown mode \'' + mode + '\'')

        self.alsa_dev = alsa_dev
        self.baudrate = baudrate
        self.process = None
        self.active = False
        #TODO handle case of minimodem not installed
        self.execpath = pexpect.which('minimodem')

        #shellcmd = [
        #    self.execpath,
        #    '--' + self.mode,
        #    '--quiet',
        #    '--alsa=' + self.alsa_dev,
        #    str(self.baudrate)
        #]

        self.shellcmd = '%s --%s --quiet --alsa=%s %s' %(self.execpath, self.mode, self.alsa_dev, self.baudrate)

        #self.shellcmd = ' '.join(shellcmd)

        if start:
            self.start()

    def start(self):
        if not self.active:
            self.process = PopenSpawn(self.shellcmd, timeout=None, encoding='utf-8')
            self.active = True

    def stop(self):
        self.active = False
        #TODO how to kill the process?
        #self.process.kill()


class FSKModem:
    RX      = 'rx'
    TX      = 'tx'
    RXTX    = 'rx/tx'
    MODES = [RX, TX, RXTX]

    #TODO arg for arecord or aplay
    @staticmethod
    def find_alsa_device(search_str='QDX'):
        alsa_dev = None
        cmd = pexpect.spawn('arecord -l')
        cmd.expect(pexpect.EOF)
        alsa_devs = cmd.before.decode('utf-8').split('\r\n')
        cmd.close()

        for line in alsa_devs:
            if search_str in line:
                start = 'card'
                end = ':'
                start_index = line.find(start) + len(start)
                end_index = line.find(end, start_index)
                card = line[start_index:end_index].strip()

                start = 'device'
                end = ':'
                start_index = line.find(start) + len(start)
                end_index = line.find(end, start_index)
                device = line[start_index:end_index].strip()

                alsa_dev = card + ',' + device
                break

        return alsa_dev

    def __init__(self, alsa_dev_in, alsa_dev_out=None, baudrate=300, mode='rx/tx', start=True):
        self.baudrate = baudrate
        self.alsa_dev_in = alsa_dev_in
        self.alsa_dev_out = alsa_dev_out
        self.rx = None
        self.tx = None
        self.active = False

        if mode in FSKModem.MODES:
            self.mode = mode
        else:
            raise Exception('Unknown mode \'' + mode + '\'')

        if self.alsa_dev_out == None:
            self.alsa_dev_out = self.alsa_dev_in

        if self.mode in [FSKModem.RXTX, FSKModem.RX]:
            self.rx = MiniModem(MiniModem.RX, self.alsa_dev_in, baudrate=self.baudrate, start=False)

        if self.mode in [FSKModem.RXTX, FSKModem.TX]:
            self.tx = MiniModem(MiniModem.TX, self.alsa_dev_out, baudrate=self.baudrate, start=False)

        if start:
            self.start()

    def start(self):
        if self.rx:
            self.rx.start()
        if self.tx:
            self.tx.start()

        self.active = True

        self._job_thread = threading.Thread(target=self._job_loop)
        self._job_thread.daemon = True
        self._job_thread.start()

    def stop(self):
        self.active = False

        if self.tx:
            self.tx.stop()
        if self.rx:
            self.rx.stop()

    def send(self, data):
        if not self.tx:
            return None

        self.tx.process.sendline(data)

    def receive(self, timeout=0):
        if not self.rx:
            return None

        self.rx.process.expect_exact(pexpect.TIMEOUT, timeout=timeout)
        return self.rx.process.before

    def register_rx_callback(self, func):
        pass

    def _job_loop(self):
        while self.active:
            if self.rx:
                data = ''

                try:
                    data = self.receive()
                except UnicodeDecodeError as e:
                    #TODO handle error
                    pass

                if len(data):
                    #TODO append data to buffer?
                    print(data)

            time.sleep(1)








