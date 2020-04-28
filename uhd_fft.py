import uhd
import numpy as np
import matplotlib.pyplot as plt


class UhdFft():
    _start_freq = None
    _end_freq = None
    _center_freq = 796e6
    _bandwidth = 10e6
    _channel_id = 0
    _antenna_id = 0
    _antennas = None
    _antenna_name = None
    _sampling_rate = None
    _fft_size = 1024
    _n_samples = int(100e3)
    _n_fft_steps = None
    _usrp = None
    _freq_res = None
    _time_res = None
    _gain = 32
    _buffer = None
    _streamer = None
    _lo_offset = 2e6
    _vmin = -45
    _vmax = 0

    @property
    def vmax(self):
        return self._vmax

    @vmax.setter
    def vmax(self, val):
        self._vmax = float(val)

    @property
    def vmin(self):
        return self._vmin

    @vmin.setter
    def vmin(self, val):
        self._vmin = float(val)

    @property
    def time_res(self):
        return self._time_res

    @property
    def freq_res(self):
        return self._freq_res

    @property
    def fft_size(self):
        return self._fft_size

    @fft_size.setter
    def fft_size(self, val):
        self._fft_size = int(val)
        self.update_config()

    @property
    def center_freq(self):
        return self._center_freq

    @center_freq.setter
    def center_freq(self, val):
        self._center_freq = float(val)
        self.update_config()

    @property
    def bandwidth(self):
        return self._bandwidth

    @bandwidth.setter
    def bandwidth(self, val):
        self._bandwidth = float(val)
        self.update_config()

    @property
    def gain(self):
        return self._gain

    @gain.setter
    def gain(self, val):
        self._gain = float(val)
        self.update_config()

    @property
    def antennas(self):
        return self._antennas

    @property
    def antenna_id(self):
        return self._antenna_id

    @antenna_id.setter
    def antenna_id(self, val):
        self._antenna_id = int(val)
        self.update_antenna()

    @property
    def antenna_name(self):
        return self._antennas[self._antenna_id]

    @gain.setter
    def antenna_name(self, val):
        self._antenna_id = self._antennas.index(val)
        self.update_antenna()

    def __init__(self,
                 center_freq=900e6,
                 bandwidth=5e6,
                 gain=32):
        self._gain = gain
        self._center_freq = center_freq
        self._bandwidth = bandwidth

        self._usrp = uhd.usrp.MultiUSRP()
        self._antennas = self._usrp.get_rx_antennas(self._channel_id)

        self.update_config()
        self.update_antenna()

    def stop_streamer(self):
        if self._streamer:
            stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
            self._streamer.issue_stream_cmd(stream_cmd)

    def start_streamer(self):
        if self._streamer:
            stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
            self._streamer.issue_stream_cmd(stream_cmd)

    def update_config(self):
        self._sampling_rate = self._bandwidth
        self._freq_res = self._sampling_rate/self._fft_size
        self._time_res = (1/self._sampling_rate)*self._fft_size
        self._start_freq = self._center_freq - self._bandwidth/2
        self._end_freq = self._center_freq + self._bandwidth/2
        self._lo_offset = self._bandwidth
        self.update_usrp_params()

        self.stop_streamer()
        self._streamer = None

        # initialise streaming
        st_args = uhd.usrp.StreamArgs("fc32", "sc16")
        st_args.channels = [self._channel_id]
        self._streamer = self._usrp.get_rx_stream(st_args)
        # self.start_streamer()

    def update_usrp_params(self):
        tune_req = uhd.types.TuneRequest(self._center_freq, self._lo_offset)
        self._usrp.set_rx_freq(tune_req, self._channel_id)
        self._usrp.set_rx_gain(self._gain, self._channel_id)
        self._usrp.set_rx_rate(self._sampling_rate, self._channel_id)

    def update_antenna(self):
        if len(self._antennas) <= self._antenna_id:
            print("Antenna %d is out of range" % self._antenna_id)
            print("Available: %s" % ", ".join(self._antennas))
            return False

        self._antenna_name = self._antennas[self._antenna_id]
        self._usrp.set_rx_antenna(self._antenna_name)
        return True

    def show_info(self):
        if not self._usrp:
            print("USRP is not initialised!")
            return False
        print("Antenna: %s" %
              self._usrp.get_rx_antenna())
        print("Frequency: %.2f" %
              (self._usrp.get_rx_freq(self._channel_id)/1e6))
        return True

    def psd(self, samples):
        window = np.hamming(self._fft_size)
        result = np.multiply(window, samples)
        result = np.fft.fft(result, self._fft_size)
        result = np.fft.fftshift(result)
        result = np.square(np.abs(result))
        result = np.nan_to_num(10.0 * np.log10(result))
        result = np.abs(result)
        return result
        
    def usrp_recv(self):
        self.start_streamer()
        metadata = uhd.types.RXMetadata()
        buffer = np.empty((1, self._n_samples), dtype=np.complex64)
        samples = np.empty((1, self._n_samples), dtype=np.complex64)
        recv_samps = 0

        while recv_samps < self._n_samples:
            samps = self._streamer.recv(buffer, metadata)
            if metadata.error_code != uhd.types.RXMetadataErrorCode.none:
                print(metadata.strerror())
            if samps:
                real_samps = min(self._n_samples - recv_samps, samps)
                samples[:, recv_samps:recv_samps +
                        real_samps] = buffer[:, 0:real_samps]
                recv_samps += real_samps

        samples = samples[self._channel_id]
        n_fft_steps = int(np.floor(len(samples)/self._fft_size))

        freq_result = np.zeros([n_fft_steps, self._fft_size])
        for i in range(n_fft_steps):
            bins = -1*self.psd(samples[i*self._fft_size:(i+1)*self._fft_size])
            freq_result[i] = bins
        self.stop_streamer()
        return freq_result

    def format_freq_ticks(self, ticks):
        return (self._start_freq + int(self._freq_res) * ticks)//1e6

    def format_time_ticks(self, ticks):
        return np.round(self._time_res*ticks*1e3)

    def plot_spectogram(self, ax, freq_result):
        cmap = plt.get_cmap("inferno")
        cf = ax.pcolormesh(freq_result, cmap=cmap, vmax=self._vmax, vmin=self._vmin)
        ax.set_yticklabels(self.format_time_ticks(ax.get_yticks()))
        ax.set_ylabel("Time [ms]")
        return cf

    def plot_avg_power(self, ax, freq_result, opacity=.9, label=""):
        avg_power = np.mean(freq_result, axis=0)
        ax.plot(avg_power, alpha=opacity, label=label)
        ax.set_xlabel("Frequency [MHz]")
        ax.set_ylabel("Power [dB]")
        ax.set_xticklabels(
            self.format_freq_ticks(ax.get_xticks()),
            rotation=45)

    def plot(self, freq_result):
        f, ax = plt.subplots(2, 1, sharex=True)
        plt.subplots_adjust(hspace=.0)
        cf = self.plot_spectogram(ax[0], freq_result)
        f.colorbar(cf, ax=ax)
        self.plot_avg_power(ax[1], freq_result)
        plt.show()
