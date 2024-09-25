import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.animation import FuncAnimation
from noise import pnoise2  # Perlin noise function
import io
import os
# Function to create a multi-layered Perlin noise field with larger waves
def multi_layer_perlin_noise(num_points, num_threads, scale, octaves, seed=0):
    noise_field = np.zeros((num_points, num_threads))
    for octave in range(octaves):
        frequency = 2 ** octave
        amplitude = 1 / (frequency ** 0.5)  # Slower amplitude decrease for larger waves
        for i in range(num_points):
            for j in range(num_threads):
                x = (i / num_points) * scale * frequency + seed
                y = (j / num_threads) * scale * frequency + seed
                noise_field[i][j] += pnoise2(x, y, octaves=1, repeatx=1024, repeaty=1024, base=0) * amplitude
    return noise_field

# Function to update the plot
def update(frame):
    global slowdown_factor
    # Get current slider values
    num_threads = int(slider_threads.val)
    noise_scale = slider_noise.val
    wave_size = slider_wave_size.val
    distortion_amplitude = slider_distortion.val
    speed = slider_speed.val
    line_thickness = slider_thickness.val
    line_density = slider_density.val

    # Update distortion field
    distortion_field = multi_layer_perlin_noise(num_points, num_threads, noise_scale, octaves=int(wave_size), seed=frame * speed)

    # Apply slow-down effect
    slowdown_factor *= 0.995  # Adjust this value for desired slow-down rate

    ax.clear()

    # Generate and plot threads
    for i in range(num_threads):
        # Base x-coordinates for each thread
        x_base = np.full(num_points, i * line_density)

        # Apply distortions with slow-down factor
        x = x_base + distortion_field[:, i] * distortion_amplitude * slowdown_factor
        y = y_base + distortion_field[:, i] * distortion_amplitude * slowdown_factor * 2  # Increased y-distortion

        ax.plot(x, y, color='darkblue', linewidth=line_thickness, alpha=0.7)

    ax.axis('off')
    ax.set_aspect('equal', adjustable='box')
    ax.set_title('Organic Motion Simulation', fontsize=16)
    ax.set_xlim(-1, num_threads * line_density + 1)
    ax.set_ylim(-2, 12)  # Increased y-range

# Function to reset sliders
def reset(event):
    slider_threads.reset()
    slider_noise.reset()
    slider_wave_size.reset()
    slider_distortion.reset()
    slider_speed.reset()
    slider_thickness.reset()
    slider_density.reset()
    global slowdown_factor
    slowdown_factor = 1.0  # Reset slowdown factor

# Function to handle slider changes
def on_slider_change(val):
    global slowdown_factor
    slowdown_factor = 1.0  # Reset slowdown factor when parameters change
    update(0)  # Call update function directly
    fig.canvas.draw_idle()  # Redraw the figure

# Function to export the current frame as SVG
def export_svg(event):
    # Create a new figure with only the plot
    fig_export, ax_export = plt.subplots(figsize=(10, 8))

    # Get current slider values
    num_threads = int(slider_threads.val)
    noise_scale = slider_noise.val
    wave_size = slider_wave_size.val
    distortion_amplitude = slider_distortion.val
    line_thickness = slider_thickness.val
    line_density = slider_density.val

    # Update distortion field
    distortion_field = multi_layer_perlin_noise(num_points, num_threads, noise_scale, octaves=int(wave_size))

    # Generate and plot threads
    for i in range(num_threads):
        x_base = np.full(num_points, i * line_density)
        x = x_base + distortion_field[:, i] * distortion_amplitude
        y = y_base + distortion_field[:, i] * distortion_amplitude * 2  # Increased y-distortion
        ax_export.plot(x, y, color='black', linewidth=line_thickness, alpha=0.7)

    ax_export.axis('off')
    ax_export.set_aspect('equal', adjustable='box')
    ax_export.set_xlim(-1, num_threads * line_density + 1)
    ax_export.set_ylim(-2, 12)  # Increased y-range

    # Create output directory if it doesn't exist
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)

    # Save the new figure as SVG in the output directory
    buf = io.BytesIO()
    fig_export.savefig(buf, format='svg', bbox_inches='tight', pad_inches=0)
    output_path = os.path.join(output_dir, 'organic_fabric.svg')
    with open(output_path, 'wb') as f:
        f.write(buf.getvalue())

    # Close the export figure to free up memory
    plt.close(fig_export)

    print(f"SVG exported as '{output_path}'")

# Initial parameters
num_threads = 1
num_points = 200
y_base = np.linspace(0, 10, num_points)
slowdown_factor = 1.0  # Initialize slowdown factor

# Modify the figure creation and layout
fig = plt.figure(figsize=(16, 9))
grid = plt.GridSpec(1, 2, width_ratios=[3, 1])

# Main plot area
ax = fig.add_subplot(grid[0, 0])
ax.set_aspect('equal', adjustable='box')
ax.axis('off')

# Control panel area
control_panel = fig.add_subplot(grid[0, 1])
control_panel.axis('off')

# Adjust the overall layout
plt.subplots_adjust(left=0.05, right=0.98, top=0.95, bottom=0.05)

# Create sliders in the control panel
slider_y = 0.85
slider_height = 0.02
slider_spacing = 0.06

sliders = []
slider_params = [
    ('Number of Lines', 1, 50, num_threads, 1),
    ('Noise Scale', 0.05, 1, 0.2),
    ('Wave Size', 1, 8, 4, 1),
    ('Distortion', 0.01, 3.0, 1.0),
    ('Speed', 0.005, 0.2, 0.01),
    ('Line Thickness', 0.1, 2.0, 0.5),
    ('Line Density', 0.01, 0.2, 0.05)
]

for label, min_val, max_val, init_val, *step in slider_params:
    slider_ax = control_panel.inset_axes([0.1, slider_y, 0.8, slider_height])
    slider = Slider(slider_ax, label, min_val, max_val, valinit=init_val, valstep=step[0] if step else None)
    sliders.append(slider)
    slider_y -= slider_spacing

# Assign sliders to variables
slider_threads, slider_noise, slider_wave_size, slider_distortion, slider_speed, slider_thickness, slider_density = sliders

# Create reset and export buttons
button_y = 0.1
button_width = 0.35
button_height = 0.06
button_spacing = 0.05

reset_button_ax = control_panel.inset_axes([0.1, button_y, button_width, button_height])
reset_button = Button(reset_button_ax, 'Reset', color='#f0f0f0', hovercolor='#e0e0e0')

export_button_ax = control_panel.inset_axes([0.55, button_y, button_width, button_height])
export_button = Button(export_button_ax, 'Export SVG', color='#f0f0f0', hovercolor='#e0e0e0')

# Add a title to the control panel
control_panel.text(0.5, 0.97, 'Organic Motion Controls', fontsize=14, fontweight='bold', ha='center', va='top')

# Connect sliders and buttons to functions
for slider in sliders:
    slider.on_changed(on_slider_change)

reset_button.on_clicked(reset)
export_button.on_clicked(export_svg)

# Customize the appearance
plt.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'sans-serif']
for slider in sliders:
    slider.label.set_fontsize(10)
    slider.valtext.set_fontsize(8)

# Start the animation
anim = FuncAnimation(fig, update, interval=50)

plt.show()
