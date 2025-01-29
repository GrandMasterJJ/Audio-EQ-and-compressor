import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import scipy.signal
from matplotlib.gridspec import GridSpec


def apply_expander_compressor(input_db, expander_threshold_db, compressor_threshold_db, compressor_ratio, expander_ratio):
    """
    Apply a combined expander and compressor transfer function with separate thresholds.
    - Expand signals below the expander threshold using the expander ratio.
    - Compress signals above the compressor threshold using the compressor ratio.
    - Leave signals between the thresholds unchanged.
    """
    output_db = np.copy(input_db)

    # Apply expansion for signals below the expander threshold
    mask_expansion = input_db < expander_threshold_db
    output_db[mask_expansion] = expander_threshold_db - (expander_threshold_db - input_db[mask_expansion]) * expander_ratio

    # Apply compression for signals above the compressor threshold
    mask_compression = input_db > compressor_threshold_db
    output_db[mask_compression] = compressor_threshold_db + (input_db[mask_compression] - compressor_threshold_db) / compressor_ratio

    return output_db


def apply_compression_expansion_frequency(input_signal, sample_rate, expander_threshold, compressor_threshold, compressor_ratio, expander_ratio, target_freq_range):
    """
    Apply compression and expansion only to a specific frequency range.
    """
    # Perform STFT to transform the signal into the frequency domain
    f, t, Zxx = scipy.signal.stft(input_signal, fs=sample_rate, nperseg=1024)
    
    # Magnitude and phase of the frequency components
    magnitude = np.abs(Zxx)
    phase = np.angle(Zxx)

    # Identify the frequency bins corresponding to the target range
    target_bins = (f >= target_freq_range[0]) & (f <= target_freq_range[1])

    # Apply compression/expansion only to the magnitude in the target range
    magnitude[target_bins, :] = apply_expander_compressor(
        20 * np.log10(magnitude[target_bins, :]),  # Convert magnitude to dB
        expander_threshold, 
        compressor_threshold, 
        compressor_ratio, 
        expander_ratio
    )
    
    # Convert dB back to magnitude
    magnitude[target_bins, :] = 10 ** (magnitude[target_bins, :] / 20)

    # Reconstruct the frequency domain signal
    Zxx_processed = magnitude * np.exp(1j * phase)

    # Transform back to the time domain
    _, processed_signal = scipy.signal.istft(Zxx_processed, fs=sample_rate)
    
    return processed_signal


def interactive_audio_processor():
    """
    Interactive visualization combining audio signal processing and transfer function display.
    Shows time domain, frequency spectrum, and compressor/expander transfer function.
    """
    # Generate test input signal
    sample_rate = 44100
    t = np.linspace(0, 2, sample_rate * 2, endpoint=False)
    input_signal = np.sin(2 * np.pi * 440 * t) + 0.5 * np.sin(2 * np.pi * 1000 * t)

    # Initial parameters
    initial_expander_threshold = -40
    initial_compressor_threshold = -10
    initial_compressor_ratio = 4
    initial_expander_ratio = 2
    target_freq_range = (500, 2000)

    # Process initial signal
    processed_signal = apply_compression_expansion_frequency(
        input_signal,
        sample_rate,
        initial_expander_threshold,
        initial_compressor_threshold,
        initial_compressor_ratio,
        initial_expander_ratio,
        target_freq_range
    )

    # Ensure processed signal length matches input
    if len(processed_signal) > len(t):
        processed_signal = processed_signal[:len(t)]
    elif len(processed_signal) < len(t):
        processed_signal = np.pad(processed_signal, (0, len(t) - len(processed_signal)), mode='constant')

    # Create figure and GridSpec layout
    fig = plt.figure(figsize=(15, 15))
    gs = GridSpec(3, 2, height_ratios=[1, 1, 0.4], figure=fig)
    
    # Create main plotting axes
    ax1 = fig.add_subplot(gs[0, 0])  # Time domain plot
    ax2 = fig.add_subplot(gs[1, 0])  # Frequency domain plot
    ax3 = fig.add_subplot(gs[0:2, 1])  # Transfer function plot
    
    # Create a subplot for sliders
    slider_area = fig.add_subplot(gs[2, :])
    slider_area.set_visible(False)

    # Time-domain plot
    ax1.plot(t, input_signal, label="Original Signal", alpha=0.6)
    time_processed_line, = ax1.plot(t, processed_signal, label="Processed Signal", linewidth=2)
    ax1.set_title("Time Domain Signal")
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Amplitude")
    ax1.legend()
    ax1.grid(True)

    # Frequency domain plot setup
    def plot_spectrum(signal):
        spectrum = np.fft.rfft(signal)
        freqs = np.fft.rfftfreq(len(signal), 1/sample_rate)
        magnitude_db = 20 * np.log10(np.abs(spectrum) + 1e-10)
        return freqs, magnitude_db

    # Initial spectrum plots
    freqs_orig, mag_db_orig = plot_spectrum(input_signal)
    freqs_proc, mag_db_proc = plot_spectrum(processed_signal)
    
    ax2.plot(freqs_orig, mag_db_orig, label="Original Spectrum", alpha=0.6)
    spectrum_line, = ax2.plot(freqs_proc, mag_db_proc, label="Processed Spectrum", linewidth=2)
    
    ax2.axvline(x=target_freq_range[0], color='r', linestyle='--', alpha=0.5, label='Target Range')
    ax2.axvline(x=target_freq_range[1], color='r', linestyle='--', alpha=0.5)
    ax2.set_title("Frequency Spectrum")
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Magnitude (dB)")
    ax2.set_xscale('log')
    ax2.set_xlim(20, sample_rate/2)
    ax2.grid(True)
    ax2.legend()

    # Transfer function plot
    input_db = np.linspace(-60, 0, 1000)
    output_db = apply_expander_compressor(
        input_db,
        initial_expander_threshold,
        initial_compressor_threshold,
        initial_compressor_ratio,
        initial_expander_ratio
    )

    ax3.plot(input_db, input_db, 'k--', alpha=0.5, label='1:1 (No Change)')
    combined_line, = ax3.plot(input_db, output_db, 'b-', linewidth=2, label='Transfer Function')

    # Add threshold lines
    expander_threshold_line_x = ax3.axvline(x=initial_expander_threshold, color='g', linestyle=':', alpha=0.7, label='Expander Threshold')
    expander_threshold_line_y = ax3.axhline(y=initial_expander_threshold, color='g', linestyle=':', alpha=0.7)
    compressor_threshold_line_x = ax3.axvline(x=initial_compressor_threshold, color='r', linestyle=':', alpha=0.7, label='Compressor Threshold')
    compressor_threshold_line_y = ax3.axhline(y=initial_compressor_threshold, color='r', linestyle=':', alpha=0.7)

    ax3.grid(True, alpha=0.3)
    ax3.set_title('Compressor/Expander Transfer Function')
    ax3.set_xlabel('Input Level (dB)')
    ax3.set_ylabel('Output Level (dB)')
    ax3.legend()
    ax3.set_xlim(-60, 0)
    ax3.set_ylim(-60, 0)
    ax3.axis('square')

    # Calculate positions for sliders
    slider_height = 0.03
    slider_spacing = 0.05
    bottom_margin = 0.05

    # Create slider axes
    ax_compressor_threshold = plt.axes([0.2, bottom_margin + 3*slider_spacing, 0.65, slider_height])
    ax_compressor_ratio = plt.axes([0.2, bottom_margin + 2*slider_spacing, 0.65, slider_height])
    ax_expander_threshold = plt.axes([0.2, bottom_margin + slider_spacing, 0.65, slider_height])
    ax_expander_ratio = plt.axes([0.2, bottom_margin, 0.65, slider_height])

    # Create sliders
    expander_threshold_slider = Slider(ax_expander_threshold, 'Expander Threshold (dB)', -60, 0, valinit=initial_expander_threshold)
    compressor_threshold_slider = Slider(ax_compressor_threshold, 'Compressor Threshold (dB)', -60, 0, valinit=initial_compressor_threshold)
    compressor_ratio_slider = Slider(ax_compressor_ratio, 'Compressor Ratio', 1, 20, valinit=initial_compressor_ratio)
    expander_ratio_slider = Slider(ax_expander_ratio, 'Expander Ratio', 1, 10, valinit=initial_expander_ratio)

    # Update function
    def update(val):
        expander_threshold = expander_threshold_slider.val
        compressor_threshold = compressor_threshold_slider.val
        compressor_ratio = compressor_ratio_slider.val
        expander_ratio = expander_ratio_slider.val

        # Update processed signal
        processed_signal = apply_compression_expansion_frequency(
            input_signal,
            sample_rate,
            expander_threshold,
            compressor_threshold,
            compressor_ratio,
            expander_ratio,
            target_freq_range
        )

        # Ensure processed signal length matches input
        if len(processed_signal) > len(t):
            processed_signal = processed_signal[:len(t)]
        elif len(processed_signal) < len(t):
            processed_signal = np.pad(processed_signal, (0, len(t) - len(processed_signal)), mode='constant')

        # Update time domain plot
        time_processed_line.set_ydata(processed_signal)
        
        # Update frequency domain plot
        freqs_proc, mag_db_proc = plot_spectrum(processed_signal)
        spectrum_line.set_ydata(mag_db_proc)

        # Update transfer function
        output_db = apply_expander_compressor(
            input_db,
            expander_threshold,
            compressor_threshold,
            compressor_ratio,
            expander_ratio
        )
        combined_line.set_ydata(output_db)

        # Update threshold lines
        expander_threshold_line_x.set_xdata([expander_threshold, expander_threshold])
        expander_threshold_line_y.set_ydata([expander_threshold, expander_threshold])
        compressor_threshold_line_x.set_xdata([compressor_threshold, compressor_threshold])
        compressor_threshold_line_y.set_ydata([compressor_threshold, compressor_threshold])
        
        fig.canvas.draw_idle()

    # Connect sliders to update function
    expander_threshold_slider.on_changed(update)
    compressor_threshold_slider.on_changed(update)
    compressor_ratio_slider.on_changed(update)
    expander_ratio_slider.on_changed(update)

    # Adjust layout
    #plt.tight_layout()
    #plt.subplots_adjust(top=0.95, bottom=0.2)
    plt.subplots_adjust(top=0.95, bottom=0.2, hspace=0.5)

    plt.show()



# Run the interactive expander/compressor
interactive_audio_processor()
