import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider


def compress_audio_sine_wave(
        frequency, duration, sample_rate, 
        compress_threshold_db, compress_ratio, 
        expand_threshold_db, expand_ratio, amplitude):
    """
    Apply dynamic range compression and expansion to a generated sine wave.
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    sine_wave = amplitude * np.sin(2 * np.pi * frequency * t)
    # additional_sine = 0.2 * np.sin(2 * np.pi * 5000 * t)  # 1kHz sine wave

    # sine_wave = sine_wave + additional_sine
    
    compress_threshold_linear = 10 ** (compress_threshold_db / 20)
    expand_threshold_linear = 10 ** (expand_threshold_db / 20)
    
    amplitude_env = np.abs(sine_wave)
    gain_reduction = np.ones_like(amplitude_env)
    
    # Compression (above compress threshold)
    compress_mask = amplitude_env > compress_threshold_linear
    gain_reduction[compress_mask] = (compress_threshold_linear + (amplitude_env[compress_mask] - compress_threshold_linear) / compress_ratio) / amplitude_env[compress_mask]
    
    # Expansion (below expand threshold)
    expand_mask = amplitude_env < expand_threshold_linear
    # Calculate expansion gain reduction
    gain_reduction[expand_mask] = (amplitude_env[expand_mask] / expand_threshold_linear) ** (expand_ratio - 1)
    #gain_reduction[expand_mask] = expand_threshold_linear - (expand_threshold_linear - amplitude_env[expand_mask]) * expand_ratio

    
    processed_audio = sine_wave * gain_reduction
    return sine_wave, processed_audio


def create_combined_interactive_plot():
    # Initial parameters
    frequency = 440
    duration = 0.01
    sample_rate = 44100
    initial_threshold = -20
    initial_ratio = 4
    initial_amplitude = 1.0
    
    # Create figure with two subplots side by side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    plt.subplots_adjust(bottom=0.25)  # Make room for shared sliders
    
    # Left subplot - Waveform
    t = np.linspace(0, duration, int(sample_rate * duration))
    original_wave, compressed_wave = compress_audio_sine_wave(
        frequency, duration, sample_rate,
        initial_threshold, initial_ratio,
        initial_amplitude
    )
    
    wave_original, = ax1.plot(t * 1000, original_wave, label="Original", alpha=0.7)
    wave_compressed, = ax1.plot(t * 1000, compressed_wave, label="Compressed", alpha=0.7)
    wave_threshold = ax1.axhline(y=10 ** (initial_threshold / 20), color='r', 
                                linestyle='--', label=f'Threshold ({initial_threshold}dB)')
    wave_neg_threshold = ax1.axhline(y=-10 ** (initial_threshold / 20), color='r', 
                                    linestyle='--')
    
    ax1.set_xlabel("Time (ms)")
    ax1.set_ylabel("Amplitude")
    ax1.set_title("Waveform Comparison")
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_ylim(-1.5, 1.5)
    
    # Right subplot - Transfer Function
    input_db = np.linspace(-60, 0, 1000)
    output_db = np.zeros_like(input_db)
    mask = input_db <= initial_threshold
    output_db[mask] = input_db[mask]
    output_db[~mask] = initial_threshold + (input_db[~mask] - initial_threshold) / initial_ratio
    
    ax2.plot(input_db, input_db, 'k--', alpha=0.5, label='1:1 (No Compression)')
    transfer_line, = ax2.plot(input_db, output_db, 'b-', linewidth=2, label='Compressor Response')
    transfer_threshold_x = ax2.axvline(x=initial_threshold, color='r', linestyle=':', alpha=0.5)
    transfer_threshold_y = ax2.axhline(y=initial_threshold, color='r', linestyle=':', alpha=0.5)
    
    ax2.grid(True, alpha=0.3)
    ax2.set_title('Compressor Transfer Function')
    ax2.set_xlabel('Input Level (dB)')
    ax2.set_ylabel('Output Level (dB)')
    ax2.legend()
    ax2.set_xlim(-60, 0)
    ax2.set_ylim(-60, 0)
    ax2.axis('square')
    
    # Create shared sliders
    ax_threshold = plt.axes([0.15, 0.1, 0.65, 0.03])
    ax_ratio = plt.axes([0.15, 0.05, 0.65, 0.03])
    ax_amplitude = plt.axes([0.15, 0.15, 0.65, 0.03])
    
    threshold_slider = Slider(
        ax=ax_threshold,
        label='Threshold (dB)',
        valmin=-60,
        valmax=0,
        valinit=initial_threshold,
        valstep=1
    )
    
    ratio_slider = Slider(
        ax=ax_ratio,
        label='Ratio',
        valmin=1,
        valmax=20,
        valinit=initial_ratio,
        valstep=0.1
    )

    amplitude_slider = Slider(
        ax=ax_amplitude,
        label='Input Amplitude',
        valmin=0.01,
        valmax=1.0,
        valinit=initial_amplitude
    )
    
    def update(val):
        # Get current slider values
        threshold_db = threshold_slider.val
        ratio = ratio_slider.val
        amplitude = amplitude_slider.val
        
        # Update waveform plot
        new_original, new_compressed = compress_audio_sine_wave(
            frequency, duration, sample_rate,
            threshold_db, ratio,
            amplitude
        )
        
        wave_original.set_ydata(new_original)
        wave_compressed.set_ydata(new_compressed)
        
        threshold_linear = 10 ** (threshold_db / 20)
        wave_threshold.set_ydata([threshold_linear, threshold_linear])
        wave_neg_threshold.set_ydata([-threshold_linear, -threshold_linear])
        
        # Update transfer function plot
        mask = input_db <= threshold_db
        output_db[mask] = input_db[mask]
        output_db[~mask] = threshold_db + (input_db[~mask] - threshold_db) / ratio
        
        transfer_line.set_ydata(output_db)
        transfer_threshold_x.set_xdata([threshold_db, threshold_db])
        transfer_threshold_y.set_ydata([threshold_db, threshold_db])
        
        # Update threshold line labels
        wave_threshold.set_label(f'Threshold ({threshold_db:.1f}dB)')
        ax1.legend()
        
        fig.canvas.draw_idle()
    
    # Register the update function with both sliders
    threshold_slider.on_changed(update)
    ratio_slider.on_changed(update)
    amplitude_slider.on_changed(update)
    
    plt.show()

# Run the combined interactive plot
# create_combined_interactive_plot()

def apply_expander_compressor(input_db, compressor_threshold_db, compressor_ratio, expander_threshold_db, expander_ratio):
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

    # Signals between the two thresholds remain unchanged
    return output_db

def plot_expander_compressor_separate_thresholds():
    # Initial parameters
    frequency = 440
    duration = 0.01
    sample_rate = 44100
    initial_amplitude = 1.0

    # Initial parameter values
    initial_compressor_threshold = -10
    initial_compressor_ratio = 4
    initial_expander_threshold = -40
    initial_expander_ratio = 2

    # Create figure with two subplots side by side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 10))
    plt.subplots_adjust(left=0.1, bottom=0.5)  # Make room for shared sliders

    t = np.linspace(0, duration, int(sample_rate * duration))
    original_wave, compressed_expanded_wave = compress_audio_sine_wave(
        frequency, duration, sample_rate,
        initial_compressor_threshold, initial_compressor_ratio,
        initial_expander_threshold, initial_expander_ratio,
        initial_amplitude
    )
    
    wave_original, = ax1.plot(t * 1000, original_wave, label="Original", alpha=0.7)
    wave_compressed_expanded, = ax1.plot(t * 1000, compressed_expanded_wave, label="Compressed", alpha=0.7)
    wave_compress_threshold = ax1.axhline(y=10 ** (initial_compressor_threshold / 20), color='r', 
                                linestyle='--', label=f'Compressor Threshold ({initial_compressor_threshold}dB)')
    wave_compress_neg_threshold = ax1.axhline(y=-10 ** (initial_compressor_threshold / 20), color='r', 
                                    linestyle='--')
    wave_expand_threshold = ax1.axhline(y=10 ** (initial_expander_threshold / 20), color='g', 
                                linestyle='--', label=f'Expander Threshold ({initial_expander_threshold}dB)')
    wave_expand_neg_threshold = ax1.axhline(y=-10 ** (initial_expander_threshold / 20), color='g', 
                                    linestyle='--')

    
    ax1.set_xlabel("Time (ms)")
    ax1.set_ylabel("Amplitude")
    ax1.set_title("Waveform Comparison")
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_ylim(-1.5, 1.5)

    # Right subplot - Transfer Function
    # Create input values in dB
    input_db = np.linspace(-60, 0, 1000)

    # Plot the 1:1 reference line
    ax2.plot(input_db, input_db, 'k--', alpha=0.5, label='1:1 (No Change)')

    # Calculate initial output values for the combined function
    output_db = apply_expander_compressor(
        input_db,
        initial_compressor_threshold,
        initial_compressor_ratio,
        initial_expander_threshold,
        initial_expander_ratio
    )

    # Plot the combined curve
    combined_line, = ax2.plot(input_db, output_db, 'b-', linewidth=2, label='Combined Response')

    # Add threshold lines
    expander_threshold_line_x = ax2.axvline(x=initial_expander_threshold, color='g', linestyle=':', alpha=0.7, label='Expander Threshold')
    expander_threshold_line_y = ax2.axhline(y=initial_expander_threshold, color='g', linestyle=':', alpha=0.7)

    compressor_threshold_line_x = ax2.axvline(x=initial_compressor_threshold, color='r', linestyle=':', alpha=0.7, label='Compressor Threshold')
    compressor_threshold_line_y = ax2.axhline(y=initial_compressor_threshold, color='r', linestyle=':', alpha=0.7)

    # Customize the plot
    ax2.grid(True, alpha=0.3)
    ax2.set_title('Expander and Compressor with Separate Thresholds (Interactive)', pad=20)
    ax2.set_xlabel('Input Level (dB)')
    ax2.set_ylabel('Output Level (dB)')
    ax2.legend()
    ax2.set_xlim(-60, 0)
    ax2.set_ylim(-60, 0)
    ax2.axis('square')

    # Create sliders
    ax_compressor_threshold = plt.axes([0.2, 0.25, 0.65, 0.03])
    ax_compressor_ratio = plt.axes([0.2, 0.2, 0.65, 0.03])
    ax_expander_threshold = plt.axes([0.2, 0.15, 0.65, 0.03])
    ax_expander_ratio = plt.axes([0.2, 0.1, 0.65, 0.03])
    ax_amplitude = plt.axes([0.2, 0.05, 0.65, 0.03])

    expander_threshold_slider = Slider(ax_expander_threshold, 'Expander Threshold (dB)', -60, 0, valinit=initial_expander_threshold)
    compressor_threshold_slider = Slider(ax_compressor_threshold, 'Compressor Threshold (dB)', -60, 0, valinit=initial_compressor_threshold)
    compressor_ratio_slider = Slider(ax_compressor_ratio, 'Compressor Ratio', 1, 20, valinit=initial_compressor_ratio)
    expander_ratio_slider = Slider(ax_expander_ratio, 'Expander Ratio', 1, 10, valinit=initial_expander_ratio)
    amplitude_slider = Slider(ax=ax_amplitude, label='Input Amplitude', valmin=0.01, valmax=1.0, valinit=initial_amplitude)
    
    # Update function for sliders
    def update(val):
        # Get current slider values
        compressor_threshold = compressor_threshold_slider.val
        compressor_ratio = compressor_ratio_slider.val
        expander_threshold = expander_threshold_slider.val
        expander_ratio = expander_ratio_slider.val
        amplitude = amplitude_slider.val

        
        # Update waveform plot
        new_original, new_compressed_expanded = compress_audio_sine_wave(
            frequency, duration, sample_rate,
            compressor_threshold, compressor_ratio,
            expander_threshold, expander_ratio,
            amplitude
        )

        wave_original.set_ydata(new_original)
        wave_compressed_expanded.set_ydata(new_compressed_expanded)

        compress_threshold_linear = 10 ** (compressor_threshold / 20)
        wave_compress_threshold.set_ydata([compress_threshold_linear, compress_threshold_linear])
        expand_threshold_linear = 10 ** (expander_threshold / 20)
        wave_expand_threshold.set_ydata([expand_threshold_linear, expand_threshold_linear])
        wave_compress_neg_threshold.set_ydata([-compress_threshold_linear, -compress_threshold_linear])
        wave_expand_neg_threshold.set_ydata([-expand_threshold_linear, -expand_threshold_linear])

        

        # Update the combined curve
        output_db = apply_expander_compressor(
            input_db,
            compressor_threshold,
            compressor_ratio,
            expander_threshold,
            expander_ratio
        )
        combined_line.set_ydata(output_db)

        # Update threshold lines
        expander_threshold_line_x.set_xdata([expander_threshold, expander_threshold])
        expander_threshold_line_y.set_ydata([expander_threshold, expander_threshold])

        compressor_threshold_line_x.set_xdata([compressor_threshold, compressor_threshold])
        compressor_threshold_line_y.set_ydata([compressor_threshold, compressor_threshold])


        # # Update threshold line labels
        wave_compress_threshold.set_label(f'Compressor Threshold ({compressor_threshold:.1f}dB)')
        wave_expand_threshold.set_label(f'Expander Threshold ({expander_threshold:.1f}dB)')
        ax1.legend()
        
        # Redraw the figure
        fig.canvas.draw_idle()

    # Connect sliders to the update function
    expander_threshold_slider.on_changed(update)
    compressor_threshold_slider.on_changed(update)
    compressor_ratio_slider.on_changed(update)
    expander_ratio_slider.on_changed(update)
    amplitude_slider.on_changed(update)

    plt.show()

# Run the interactive plot
plot_expander_compressor_separate_thresholds()
