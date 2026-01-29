import matplotlib.pyplot as plt
import numpy as np
import io
import os

def render_lecture_visual(topic, params=None):
    """Visualizes Statics concepts with a strictly centered origin for the Lab view."""
    fig, ax = plt.subplots(figsize=(6, 6), dpi=150)
    if params is None: params = {}
    
    # Grid and Origin Settings
    ax.axhline(0, color='black', lw=1.5, zorder=2)
    ax.axvline(0, color='black', lw=1.5, zorder=2)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.set_aspect('equal')
    
    # 1. Free Body Diagram: Vector Components
    if topic == "Free Body Diagram":
        force = params.get('force', 50)
        theta = np.radians(params.get('theta', 45))
        fx, fy = force * np.cos(theta), force * np.sin(theta)
        
        ax.quiver(0, 0, fx, fy, color='blue', angles='xy', scale_units='xy', scale=1, label=r'$\vec{F}$')
        ax.plot([fx, fx], [0, fy], 'k--', alpha=0.4) # dashed projection
        ax.plot(0, 0, 'ko', markersize=12) # The Particle
        limit = 110
        ax.set_title(r"FBD: Force Resolution $F_x, F_y$")

    # 2. Truss: Method of Joints
    elif topic == "Truss":
        f_load = params.get('load', 50) # Vertical load
        ax.quiver(0, 0, 0, -f_load, color='red', angles='xy', scale_units='xy', scale=1, label='Load')
        # Draw two reacting members (Compression/Tension)
        ax.quiver(0, 0, -40, 40, color='green', angles='xy', scale_units='xy', scale=1, label='Member AC')
        ax.quiver(0, 0, 40, 40, color='blue', angles='xy', scale_units='xy', scale=1, label='Member AB')
        ax.plot(0, 0, 'ko', markersize=12) # The Joint
        limit = 100
        ax.set_title(r"Truss: Equilibrium at Joint A ($\sum F = 0$)")

    # 3. Geometric Properties: Centroids
    elif topic == "Geometric Properties":
        w = params.get('width', 40)
        h = params.get('height', 60)
        # Center the rectangle on the plot
        ax.add_patch(plt.Rectangle((-w/2, -h/2), w, h, fill=False, hatch='//', color='gray'))
        ax.plot(0, 0, 'rx', markersize=15, markeredgewidth=3, label='Centroid')
        limit = 100
        ax.set_title(r"Geometry: Centroid $(\bar{x}, \bar{y})$ at Center of Mass")

    # 4. Equilibrium: Moment and Lever
    elif topic == "Equilibrium":
        weight = params.get('w', 50)
        dist = params.get('d', 40)
        # Draw the beam
        ax.plot([-dist, dist], [0, 0], 'brown', lw=10)
        # Draw the pivot
        ax.plot(0, -5, 'k^', markersize=20)
        # Draw the weight vector
        ax.quiver(-dist, 0, 0, -weight, color='red', angles='xy', scale_units='xy', scale=1)
        ax.text(-dist, 5, "Weight", ha='center')
        limit = 100
        ax.set_title(r"Equilibrium: Moment Balance $\sum M = 0$")

    # Final visual formatting
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    if topic != "Geometric Properties": ax.legend(loc='upper right')
    
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf
