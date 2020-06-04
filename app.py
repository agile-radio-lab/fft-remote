from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvas

import matplotlib
matplotlib.use('module://kivy.garden.matplotlib.backend_kivy')

import matplotlib.pyplot as plt

from uhd_fft import UhdFft


class UhdFftApp(App):
    canvas = None
    run_event = None
    btn_run = None
    uhd_fft = None

    def request_fft(self):
        self.canvas.figure.axes[0].clear()
        self.canvas.figure.axes[1].clear()

        freq_result = self.uhd_fft.usrp_recv()
        prev_antenna_id = self.uhd_fft.antenna_id
        # next_antenna_id = (prev_antenna_id + 1) % 2
        # self.uhd_fft.antenna_id = next_antenna_id

        # freq_result_2 = self.uhd_fft.usrp_recv()
        # self.uhd_fft.antenna_id = prev_antenna_id

        self.uhd_fft.plot_spectogram(self.canvas.figure.axes[0], freq_result)
        self.uhd_fft.plot_avg_power(
            self.canvas.figure.axes[1],
            freq_result,
            label="Antenna %s" % self.uhd_fft.antennas[prev_antenna_id])
        # self.uhd_fft.plot_avg_power(
        #     self.canvas.figure.axes[1],
        #     freq_result_2,
        #     opacity=.5,
        #     label="Antenna %s" % self.uhd_fft.antennas[next_antenna_id])

        self.canvas.figure.axes[0].tick_params(colors='white')
        self.canvas.figure.axes[1].tick_params(colors='white')

        self.canvas.figure.axes[1].legend()
        self.canvas.draw()

    def update_interval_callback(self, dt):
        self.request_fft()

    def on_btn_update(self, instance):
        self.request_fft()

    def on_btn_run(self, instance):
        if self.run_event:
            Clock.unschedule(self.run_event)
            self.run_event = None
            self.btn_run.text = "Run"
        else:
            self.run_event = Clock.schedule_interval(
                self.update_interval_callback, 1)
            self.btn_run.text = "Stop"

    def new_canvas(self):
        with plt.style.context(('dark_background')):
            figure, ax = plt.subplots(2, 1, sharex=True)
            plt.subplots_adjust(hspace=.0)
            wid = FigureCanvas(figure)
        return wid

    def on_bw_enter(self, instance):
        self.uhd_fft.bandwidth = instance.text
        self.request_fft()
        self.update_resolutions()

    def on_cf_enter(self, instance):
        self.uhd_fft.center_freq = instance.text
        self.request_fft()

    def on_gain_enter(self, instance):
        self.uhd_fft.gain = instance.text
        self.request_fft()

    def on_fft_size_enter(self, instance):
        self.uhd_fft.fft_size = instance.text
        self.request_fft()
        self.update_resolutions()

    def on_vmin_enter(self, instance):
        self.uhd_fft.vmin = instance.text
        self.request_fft()

    def on_vmax_enter(self, instance):
        self.uhd_fft.vmax = instance.text
        self.request_fft()

    def update_resolutions(self):
        self.time_res_label.text = "%.2f ms" % (self.uhd_fft.time_res*1e3)
        self.freq_res_label.text = "%.2f kHz" % (self.uhd_fft.freq_res/1e3)

    def build(self):
        self.uhd_fft = UhdFft(center_freq=796e6,
                              bandwidth=10e6,
                              gain=38)
        self.canvas = self.new_canvas()
        layout = BoxLayout(orientation='horizontal')
        layout.add_widget(self.canvas)

        settings = BoxLayout(orientation='vertical', size_hint_x=.3)
        settings.add_widget(
            Label(text='Time resolution', size_hint_y=None, height=30))
        self.time_res_label = Label(text='NaN', size_hint_y=None, height=30)
        settings.add_widget(self.time_res_label)

        settings.add_widget(
            Label(text='Frequency resolution', size_hint_y=None, height=30))
        self.freq_res_label = Label(text='NaN', size_hint_y=None, height=30)
        settings.add_widget(self.freq_res_label)
        self.update_resolutions()

        settings.add_widget(
            Label(text='Maximum Power', size_hint_y=None, height=30))
        vmax_input = TextInput(
            text=str(self.uhd_fft.vmax), multiline=False, size_hint_y=None, height=30)
        vmax_input.bind(on_text_validate=self.on_vmax_enter)
        settings.add_widget(vmax_input)

        settings.add_widget(
            Label(text='Mimimum Power', size_hint_y=None, height=30))
        vmin_input = TextInput(
            text=str(self.uhd_fft.vmin), multiline=False, size_hint_y=None, height=30)
        vmin_input.bind(on_text_validate=self.on_vmin_enter)
        settings.add_widget(vmin_input)

        settings.add_widget(
            Label(text='FFT Size', size_hint_y=None, height=30))
        fft_size_input = TextInput(
            text=str(self.uhd_fft.fft_size), multiline=False, size_hint_y=None, height=30)
        fft_size_input.bind(on_text_validate=self.on_fft_size_enter)
        settings.add_widget(fft_size_input)

        settings.add_widget(
            Label(text='Frequency', size_hint_y=None, height=30))
        cf_input = TextInput(
            text=str(self.uhd_fft.center_freq), multiline=False, size_hint_y=None, height=30)
        cf_input.bind(on_text_validate=self.on_cf_enter)
        settings.add_widget(cf_input)

        settings.add_widget(
            Label(text='Bandwidth', size_hint_y=None, height=30))
        bw_input = TextInput(text=str(self.uhd_fft.bandwidth),
                             multiline=False, size_hint_y=None, height=30)
        bw_input.bind(on_text_validate=self.on_bw_enter)
        settings.add_widget(bw_input)

        settings.add_widget(Label(text='Gain', size_hint_y=None, height=30))
        gain_input = TextInput(
            text=str(self.uhd_fft.gain), multiline=False, size_hint_y=None, height=30)
        gain_input.bind(on_text_validate=self.on_gain_enter)
        settings.add_widget(gain_input)

        dropdown = DropDown()
        for antenna_name in self.uhd_fft.antennas:
            btn = Button(text=antenna_name, size_hint_y=None, height=30)
            btn.bind(on_release=lambda btn: dropdown.select(btn.text))
            dropdown.add_widget(btn)
        antenna_dd_btn = Button(text='Antenna', size_hint_y=None, height=30)
        antenna_dd_btn.bind(on_release=dropdown.open)

        def dropdown_select(instance, val):
            setattr(antenna_dd_btn, 'text', val)
            self.uhd_fft.antenna_name = val
            self.request_fft()

        dropdown.bind(on_select=dropdown_select)
        settings.add_widget(antenna_dd_btn)

        btn_update = Button(text='Update', size_hint_y=None, height=30)
        btn_update.bind(on_press=self.on_btn_update)
        self.btn_run = Button(text='Run', size_hint_y=None, height=30)
        self.btn_run.bind(on_press=self.on_btn_run)
        settings.add_widget(btn_update)
        settings.add_widget(self.btn_run)
        layout.add_widget(settings)

        return layout


UhdFftApp().run()
