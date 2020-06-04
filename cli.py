from uhd_fft import UhdFft

import matplotlib.pyplot as plt

if __name__ == "__main__":
    uhd_fft = UhdFft(center_freq=796e6,
                     bandwidth=10e6,
                     gain=38)
    freq_result = uhd_fft.usrp_recv()
    # uhd_fft.plot(freq_result)
    fig, ax = plt.subplots()
    uhd_fft.plot_avg_power(ax, freq_result)
    # plt.show()
    # print(uhd_fft._freq_res)
