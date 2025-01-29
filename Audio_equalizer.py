import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, TextBox
import scipy.signal
from matplotlib.gridspec import GridSpec

def generate_sine_wave(frequency, duration, sample_rate=44100):
    """Generate a sine wave at specified frequency."""
    t = np.linspace(0, duration, int(sample_rate * duration))
    return np.sin(2 * np.pi * frequency * t), t

def calculate_spectrum(signal, sample_rate):
    """Calculate the frequency spectrum of a signal."""
    n = len(signal)
    freqs = np.fft.rfftfreq(n, 1/sample_rate)
    spectrum = np.abs(np.fft.rfft(signal))
    return freqs, 20 * np.log10(spectrum + 1e-10)

def apply_eq_filters(signal, sample_rate, center_freqs, gains, qs):
    """Apply EQ filters to the input signal."""
    filtered_signal = signal.copy()
    for f, g, q in zip(center_freqs, gains, qs):
        w0 = 2 * np.pi * f / sample_rate
        alpha = np.sin(w0) / (2 * q)
        A = 10 ** (g / 40)
        
        b0 = 1 + alpha * A
        b1 = -2 * np.cos(w0)
        b2 = 1 - alpha * A
        a0 = 1 + alpha / A
        a1 = -2 * np.cos(w0)
        a2 = 1 - alpha / A
        
        filtered_signal = scipy.signal.lfilter([b0, b1, b2], [a0, a1, a2], filtered_signal)
    
    return filtered_signal

def plot_eq_response():
    # Initial parameters
    sample_rate = 44100
    frequencies = [80, 500, 1000, 2000, 3000, 4000]
    q_factors = [2.547, 5.799, 11.075, 12.34, 14.071, 3.978]
    initial_gains = [0] * len(frequencies)

    # Generate test signal (1 kHz sine wave)
    duration = 0.1
    test_signal, time = generate_sine_wave(1000, duration, sample_rate)
    
    # Create figure and layout
    fig = plt.figure(figsize=(15, 16))
    gs = GridSpec(5, 1, height_ratios=[2, 1, 1, 1, 1])
    
    ax_freq = fig.add_subplot(gs[0])
    ax_signal = fig.add_subplot(gs[1])
    ax_spectrum = fig.add_subplot(gs[2])
    ax_sliders_gain = fig.add_subplot(gs[3])
    ax_sliders_freq_q = fig.add_subplot(gs[4])
    ax_sliders_gain.set_visible(False)
    ax_sliders_freq_q.set_visible(False)

    # Calculate frequency points for plotting
    freq_points = np.logspace(np.log10(20), np.log10(20000), 1000)

    def calculate_response(freqs, center_freqs, gains, qs):
        magnitudes = np.ones_like(freqs)
        for f, q, g in zip(center_freqs, qs, gains):
            w0 = 2 * np.pi * f / sample_rate
            alpha = np.sin(w0) / (2 * q)
            A = 10 ** (g / 40)
            b0 = 1 + alpha * A
            b1 = -2 * np.cos(w0)
            b2 = 1 - alpha * A
            a0 = 1 + alpha / A
            a1 = -2 * np.cos(w0)
            a2 = 1 - alpha / A
            w, h = scipy.signal.freqz([b0, b1, b2], [a0, a1, a2], worN=freqs, fs=sample_rate)
            magnitudes *= np.abs(h)
        return 20 * np.log10(magnitudes)

    # Initial response
    initial_response = calculate_response(freq_points, frequencies, initial_gains, q_factors)
    response_line, = ax_freq.semilogx(freq_points, initial_response, 'b-', linewidth=2)
    
    # Plot initial signal
    filtered_signal = apply_eq_filters(test_signal, sample_rate, frequencies, initial_gains, q_factors)
    signal_line, = ax_signal.plot(time, test_signal, 'b-', alpha=0.5, label='Original')
    filtered_line, = ax_signal.plot(time, filtered_signal, 'r-', label='Filtered')
    ax_signal.legend()
    ax_signal.set_title('Signal Waveform')
    ax_signal.set_xlabel('Time (s)')
    ax_signal.set_ylabel('Amplitude')
    
    # Plot initial spectrum
    orig_freqs, orig_spectrum = calculate_spectrum(test_signal, sample_rate)
    filt_freqs, filt_spectrum = calculate_spectrum(filtered_signal, sample_rate)
    spectrum_orig_line, = ax_spectrum.semilogx(orig_freqs, orig_spectrum, 'b-', alpha=0.5, label='Original')
    spectrum_filt_line, = ax_spectrum.semilogx(filt_freqs, filt_spectrum, 'r-', label='Filtered')
    ax_spectrum.grid(True, which="both", ls="-", alpha=0.6)
    ax_spectrum.set_xlim(20, 20000)
    ax_spectrum.set_title('Frequency Spectrum')
    ax_spectrum.set_ylim(-50, 100)
    ax_spectrum.set_xlabel('Frequency (Hz)')
    ax_spectrum.set_ylabel('Magnitude (dB)')
    ax_spectrum.legend()
    
    # Plot settings for EQ response
    ax_freq.grid(True, which="both", ls="-", alpha=0.6)
    ax_freq.set_xlim(20, 20000)
    ax_freq.set_ylim(-15, 15)
    ax_freq.set_title('Equalizer Frequency Response')
    ax_freq.set_xlabel('Frequency (Hz)')
    ax_freq.set_ylabel('Magnitude (dB)')
    ax_freq.axhline(y=0, color='k', linestyle='--', alpha=0.5)

    freq_lines = [ax_freq.axvline(x=f, color='r', linestyle=':', alpha=0.5) for f in frequencies]

    slider_width = 0.05
    slider_spacing = 0.12
    slider_height_gain = 0.12
    slider_height_freq_q = 0.02
    slider_bottom_gain = 0.22
    slider_bottom_freq = 0.12
    slider_bottom_q = 0.07
    textbox_bottom = slider_bottom_freq + 0.05

    sliders_gain = []
    sliders_freq = []
    sliders_q = []
    textboxes_freq = []

    current_gains = initial_gains[:]
    current_frequencies = frequencies[:]
    current_q_factors = q_factors[:]

    def validate_frequency(text):
        try:
            freq = float(text)
            return 20 <= freq <= 20000
        except ValueError:
            return False

    def textbox_submit(text, index):
        if validate_frequency(text):
            freq = float(text)
            log_freq = np.log10(freq)
            sliders_freq[index].set_val(log_freq)
            update_response()

    for i, (freq, gain, q) in enumerate(zip(frequencies, initial_gains, q_factors)):
        slider_left = 0.1 + i * slider_spacing
        
        # Frequency text input
        ax_textbox = plt.axes([slider_left, textbox_bottom, slider_width, 0.03])
        text_box = TextBox(ax_textbox, '', initial=str(int(freq)))
        text_box.on_submit(lambda text, idx=i: textbox_submit(text, idx))
        textboxes_freq.append(text_box)
        
        # Gain slider
        ax_slider_gain = plt.axes([slider_left, slider_bottom_gain, slider_width, slider_height_gain])
        slider_gain = Slider(ax_slider_gain, f'Band {i+1}', -12, 12, valinit=gain, orientation='vertical')
        sliders_gain.append(slider_gain)
        
        # Frequency slider (logarithmic)
        ax_slider_freq = plt.axes([slider_left, slider_bottom_freq, slider_width, slider_height_freq_q])
        slider_freq = Slider(ax_slider_freq, 'Freq', np.log10(20), np.log10(20000), valinit=np.log10(freq))
        slider_freq.valtext.set_text(f'{10**slider_freq.val:.1f} Hz')
        sliders_freq.append(slider_freq)
        
        # Q-factor slider
        ax_slider_q = plt.axes([slider_left, slider_bottom_q, slider_width, slider_height_freq_q])
        slider_q = Slider(ax_slider_q, 'Q', 0.1, 15, valinit=q)
        sliders_q.append(slider_q)

    def update_response():
        current_gains[:] = [s.val for s in sliders_gain]
        current_frequencies[:] = [10**s.val for s in sliders_freq]
        current_q_factors[:] = [s.val for s in sliders_q]
        
        # Update frequency response
        new_response = calculate_response(freq_points, current_frequencies, current_gains, current_q_factors)
        response_line.set_ydata(new_response)

        # Update filtered signal
        new_filtered_signal = apply_eq_filters(test_signal, sample_rate, 
                                             current_frequencies, current_gains, current_q_factors)
        filtered_line.set_ydata(new_filtered_signal)
        
        # Update spectrum
        _, new_filt_spectrum = calculate_spectrum(new_filtered_signal, sample_rate)
        spectrum_filt_line.set_ydata(new_filt_spectrum)

        # Update frequency display text and textboxes
        for i, (slider, textbox) in enumerate(zip(sliders_freq, textboxes_freq)):
            freq = 10**slider.val
            slider.valtext.set_text(f'{freq:.1f} Hz')
            if textbox.text != str(int(freq)):
                textbox.set_val(str(int(freq)))
        
        for line, freq in zip(freq_lines, current_frequencies):
            line.set_xdata([freq, freq])
        
        fig.canvas.draw_idle()

    def slider_freq_update(val, index):
        freq = 10**sliders_freq[index].val
        textboxes_freq[index].set_val(str(int(freq)))
        update_response()

    for i, slider in enumerate(sliders_freq):
        slider.on_changed(lambda val, idx=i: slider_freq_update(val, idx))

    for slider in sliders_gain + sliders_q:
        slider.on_changed(lambda _: update_response())

    plt.subplots_adjust(bottom=0.15)
    plt.show()

plot_eq_response()