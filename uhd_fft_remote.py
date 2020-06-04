import requests
import threading
import time
import base64
import io
import matplotlib.pyplot as plt

from uhd_fft import UhdFft


class UhdFftRemote():
    params = {}
    base_url = ""
    room_id = "test"
    params_thread = None
    running = True

    def __init__(self, base_url="http://localhost:8000", room_id="test"):
        self.uhd_fft = UhdFft(center_freq=796e6,
                              bandwidth=10e6,
                              gain=38)
        self.room_id = room_id
        self.base_url = base_url
        self.params_thread = threading.Thread(
            target=self.receive_params_worker,
            daemon=True)
        self.params_thread.start()

    def extract_param(self, k):
        if k in self.params and "raw" in self.params[k]:
            return self.params[k]["raw"]
        return None

    def receive_params_worker(self):
        requests.post("%s/create_room?room=%s" % (self.base_url, self.room_id))
        while self.running:
            try:
                self.recieve_params()
            except Exception as err:
                print("Error receiving remote params...")
                print(err)
            finally:
                time.sleep(.5)
        self.running = False

    def recieve_params(self):
        url = "%s/params?room=%s" % (self.base_url, self.room_id)
        resp = requests.get(url)
        self.params = resp.json()

    def send_result(self, freq_result, freq_result2):
        url = "%s/result?room=%s" % (self.base_url, self.room_id)
        result = {
            "room": self.room_id,
            "freq": self.ndarray_to_list(freq_result),
            "image": self.make_plot(freq_result, freq_result2)
        }
        resp = requests.post(url, json=result)

    @staticmethod
    def ndarray_to_list(freq_result):
        result = []
        for r in freq_result:
            result.append(list(r))
        return result

    def make_plot(self, freq_result, freq_result2):
        bts = io.BytesIO()

        with plt.style.context(('dark_background')):
            fig, ax = plt.subplots(2, 1, sharex=True)
            plt.subplots_adjust(hspace=.0, bottom=0.20)
            self.uhd_fft.plot_spectogram(ax[0], freq_result)
            self.uhd_fft.plot_avg_power(ax[1], freq_result, 1.,
                                        label="Antenna 0", color="g")
            self.uhd_fft.plot_avg_power(ax[1], freq_result2, 1.,
                                        label="Antenna 1", color="r")

            plt.figtext(.05, .9, "Sweep time: %.2f ms" %
                        (self.uhd_fft.time_res*1e3))
            plt.figtext(.7, .9, "Resolution: %.2f kHz" %
                        (self.uhd_fft.freq_res/1e3))
            ax[0].tick_params(colors='white')
            ax[1].tick_params(colors='white')
            ax[1].legend()

            fig.savefig(bts, format='png')
            bts.seek(0)
            plt.close()
        return base64.encodebytes(bts.read()).decode("ascii")

    def measurement_worker(self):
        while self.running:
            try:
                center_freq = self.extract_param("cf")
                gain = self.extract_param("antennaGain")
                fft_size = self.extract_param("fftSize")
                sampling_rate = self.extract_param("samplingRate")
                power_min = self.extract_param("powerMin")
                power_max = self.extract_param("powerMax")
                if not center_freq is None:
                    self.uhd_fft.center_freq = center_freq
                if not gain is None:
                    self.uhd_fft.gain = gain
                if not fft_size is None:
                    self.uhd_fft.fft_size = fft_size
                if not sampling_rate is None:
                    self.uhd_fft.bandwidth = sampling_rate
                if not power_min is None:
                    self.uhd_fft.vmin = power_min
                if not power_max is None:
                    self.uhd_fft.vmax = power_max

                prev_antenna_id = self.uhd_fft.antenna_id
                next_antenna_id = (prev_antenna_id + 1) % 2

                freq_result1 = self.uhd_fft.usrp_recv()
                self.uhd_fft.antenna_id = next_antenna_id
                freq_result2 = self.uhd_fft.usrp_recv()
                self.uhd_fft.antenna_id = prev_antenna_id

                self.send_result(freq_result1, freq_result2)
            except Exception as err:
                print("Error measuring...")
                print(err)
            finally:
                time.sleep(.5)
        self.running = False
