"""
Generate a publication-quality AIOps system architecture diagram
for the IEEE conference paper.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe
import numpy as np

# ── Configuration ──────────────────────────────────────────────
fig, ax = plt.subplots(1, 1, figsize=(10, 13))
ax.set_xlim(0, 10)
ax.set_ylim(0, 14)
ax.axis('off')
fig.patch.set_facecolor('white')

# ── Color Palette ──────────────────────────────────────────────
C_DATA     = '#E3F2FD'   # light blue
C_DATA_B   = '#1565C0'   # blue border
C_PREP     = '#FFF3E0'   # light orange
C_PREP_B   = '#E65100'   # orange border
C_ML       = '#E8F5E9'   # light green
C_ML_B     = '#2E7D32'   # green border
C_ORCH     = '#F3E5F5'   # light purple
C_ORCH_B   = '#6A1B9A'   # purple border
C_ACT      = '#FFEBEE'   # light red
C_ACT_B    = '#C62828'   # red border
C_FEED     = '#FFF8E1'   # light yellow
C_FEED_B   = '#F9A825'   # yellow border
C_LAYER_BG = '#FAFAFA'   # layer background
C_LAYER_BD = '#BDBDBD'   # layer border
C_ARROW    = '#455A64'   # arrow color
C_FEEDBACK = '#F9A825'   # feedback arrow


def draw_box(x, y, w, h, text, fc, ec, fontsize=8.5, bold=False, lw=1.5, text2=None):
    """Draw a rounded box with centered text."""
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle="round,pad=0.08",
                         facecolor=fc, edgecolor=ec, linewidth=lw,
                         zorder=3)
    ax.add_patch(box)
    weight = 'bold' if bold else 'normal'
    ax.text(x + w/2, y + h/2 + (0.12 if text2 else 0),
            text, ha='center', va='center',
            fontsize=fontsize, fontweight=weight, color='#212121', zorder=4)
    if text2:
        ax.text(x + w/2, y + h/2 - 0.18,
                text2, ha='center', va='center',
                fontsize=7, fontstyle='italic', color='#616161', zorder=4)
    return box


def draw_layer_bg(y, h, label):
    """Draw a layer background with label."""
    box = FancyBboxPatch((0.3, y), 9.4, h,
                         boxstyle="round,pad=0.1",
                         facecolor=C_LAYER_BG, edgecolor=C_LAYER_BD,
                         linewidth=1.0, linestyle='--', zorder=1, alpha=0.5)
    ax.add_patch(box)
    ax.text(0.55, y + h - 0.22, label,
            fontsize=7.5, fontweight='bold', color='#757575',
            fontstyle='italic', zorder=2, rotation=0)


def arrow(x1, y1, x2, y2, color=C_ARROW, style='->', lw=1.5, ls='-'):
    """Draw an arrow between two points."""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color,
                               lw=lw, linestyle=ls,
                               connectionstyle='arc3,rad=0'),
                zorder=5)


# ── Title ──────────────────────────────────────────────────────
ax.text(5, 13.6, 'Proposed AIOps Framework Architecture',
        ha='center', va='center', fontsize=14, fontweight='bold',
        color='#212121')

# ── Layer 1: Data Collection (y=11.5 to 13.0) ─────────────────
draw_layer_bg(11.4, 1.85, 'Layer 1: Data Collection')

# Jenkins
draw_box(1.0, 12.2, 2.3, 0.85, 'Jenkins CI Server', C_DATA, C_DATA_B,
         fontsize=9, bold=True)
ax.text(2.15, 12.0, 'Build Metadata + Console Logs',
        ha='center', va='center', fontsize=6.5, color='#616161')

# Prometheus
draw_box(6.7, 12.2, 2.3, 0.85, 'Prometheus', C_DATA, C_DATA_B,
         fontsize=9, bold=True)
ax.text(7.85, 12.0, 'CPU Utilization Metrics',
        ha='center', va='center', fontsize=6.5, color='#616161')

# REST API label
ax.text(2.15, 11.7, 'REST API', ha='center', va='center',
        fontsize=6.5, color=C_DATA_B, fontstyle='italic')
ax.text(7.85, 11.7, 'PromQL', ha='center', va='center',
        fontsize=6.5, color=C_DATA_B, fontstyle='italic')

# ── Layer 2: Preprocessing (y=9.4 to 10.9) ────────────────────
draw_layer_bg(9.3, 1.85, 'Layer 2: Preprocessing & Feature Engineering')

draw_box(0.6, 9.7, 2.4, 0.85, 'Structured Feature', C_PREP, C_PREP_B,
         fontsize=8.5, bold=True, text2='Extraction')

draw_box(3.8, 9.7, 2.4, 0.85, 'TF-IDF Log', C_PREP, C_PREP_B,
         fontsize=8.5, bold=True, text2='Vectorization')

draw_box(7.0, 9.7, 2.4, 0.85, 'Min-Max Scaling', C_PREP, C_PREP_B,
         fontsize=8.5, bold=True, text2='+ Sequence Windowing')

# Arrows: Data → Preprocessing
arrow(2.15, 11.7, 1.8, 10.55, lw=1.8)   # Jenkins → Feature Extraction
arrow(2.15, 11.7, 5.0, 10.55, lw=1.8)   # Jenkins → TF-IDF (logs)
arrow(7.85, 11.7, 8.2, 10.55, lw=1.8)   # Prometheus → Scaling

# Feature labels on arrows
ax.text(1.5, 11.2, 'Build\nMetadata', ha='center', va='center',
        fontsize=6, color='#757575')
ax.text(4.1, 11.2, 'Console\nLogs', ha='center', va='center',
        fontsize=6, color='#757575')
ax.text(8.5, 11.2, 'CPU\nTime-Series', ha='center', va='center',
        fontsize=6, color='#757575')

# ── Layer 3: Machine Learning (y=7.1 to 8.7) ──────────────────
draw_layer_bg(7.0, 2.0, 'Layer 3: Machine Learning Models')

draw_box(0.6, 7.35, 2.4, 1.0, 'XGBoost', C_ML, C_ML_B,
         fontsize=9, bold=True, text2='Failure Prediction')

draw_box(3.8, 7.35, 2.4, 1.0, 'Autoencoder', C_ML, C_ML_B,
         fontsize=9, bold=True, text2='Anomaly Detection')

draw_box(7.0, 7.35, 2.4, 1.0, 'LSTM', C_ML, C_ML_B,
         fontsize=9, bold=True, text2='CPU Forecasting')

# Output labels below ML boxes
ax.text(1.8, 7.15, 'P(failure)', ha='center', va='center',
        fontsize=6.5, color=C_ML_B, fontstyle='italic')
ax.text(5.0, 7.15, 'Reconstruction\nError', ha='center', va='center',
        fontsize=6.5, color=C_ML_B, fontstyle='italic')
ax.text(8.2, 7.15, 'ĉ(t+1)', ha='center', va='center',
        fontsize=6.5, color=C_ML_B, fontstyle='italic')

# Arrows: Preprocessing → ML
arrow(1.8, 9.7, 1.8, 8.35, lw=1.8)
arrow(5.0, 9.7, 5.0, 8.35, lw=1.8)
arrow(8.2, 9.7, 8.2, 8.35, lw=1.8)

# ── Layer 4: Orchestration (y=5.1 to 6.5) ─────────────────────
draw_layer_bg(5.0, 1.7, 'Layer 4: AIOps Orchestration')

draw_box(2.5, 5.3, 5.0, 1.1, 'FastAPI Orchestration Engine', C_ORCH, C_ORCH_B,
         fontsize=10, bold=True)
ax.text(5.0, 5.22, 'Unified Decision Policy  |  Threshold Evaluation  |  API Gateway',
        ha='center', va='center', fontsize=6.5, color='#616161')

# Arrows: ML → Orchestration
arrow(1.8, 7.15, 3.5, 6.4, lw=1.8)
arrow(5.0, 7.15, 5.0, 6.4, lw=1.8)
arrow(8.2, 7.15, 6.5, 6.4, lw=1.8)

# ── Layer 5: Actions & Autoscaling (y=2.5 to 4.4) ─────────────
draw_layer_bg(2.6, 2.1, 'Layer 5: Operational Actions')

draw_box(0.6, 3.05, 2.2, 0.95, 'Build Risk\nAlert', C_ACT, C_ACT_B,
         fontsize=8.5, bold=True)
ax.text(1.7, 2.82, 'P(y=1|x) > τf', ha='center', va='center',
        fontsize=6.5, color=C_ACT_B, fontstyle='italic')

draw_box(3.4, 3.05, 2.2, 0.95, 'Anomaly\nAlert', C_ACT, C_ACT_B,
         fontsize=8.5, bold=True)
ax.text(4.5, 2.82, 'Lrec > τa', ha='center', va='center',
        fontsize=6.5, color=C_ACT_B, fontstyle='italic')

draw_box(6.2, 3.05, 3.2, 0.95, 'Predictive\nAutoscaling', C_ACT, C_ACT_B,
         fontsize=9, bold=True)
ax.text(7.8, 2.82, 'ĉ(t+1) > τc → Scale Up', ha='center', va='center',
        fontsize=6.5, color=C_ACT_B, fontstyle='italic')

# Arrows: Orchestration → Actions
arrow(3.8, 5.3, 1.7, 4.0, lw=1.8)
arrow(5.0, 5.3, 4.5, 4.0, lw=1.8)
arrow(6.2, 5.3, 7.8, 4.0, lw=1.8)

# ── Kubernetes Target ──────────────────────────────────────────
draw_box(6.2, 1.2, 3.2, 0.85, 'Kubernetes Cluster', C_FEED, C_FEED_B,
         fontsize=9, bold=True)
ax.text(7.8, 1.0, 'Pod Scaling  |  Resource Adjustment',
        ha='center', va='center', fontsize=6.5, color='#616161')

# Arrow: Autoscaling → Kubernetes
arrow(7.8, 3.05, 7.8, 2.05, lw=2.0)

# ── Feedback Loop ──────────────────────────────────────────────
# Kubernetes → Prometheus (curved feedback arrow on the right side)
ax.annotate('', xy=(9.6, 12.6), xytext=(9.6, 1.6),
            arrowprops=dict(arrowstyle='->', color=C_FEEDBACK,
                           lw=2.0, linestyle='--',
                           connectionstyle='arc3,rad=-0.0'),
            zorder=5)
ax.text(9.85, 7.2, 'F\ne\ne\nd\nb\na\nc\nk',
        ha='center', va='center', fontsize=6, color=C_FEEDBACK,
        fontweight='bold', rotation=0, linespacing=0.8)

# Feedback arrow tip connects to Prometheus
arrow(9.6, 12.6, 9.0, 12.6, color=C_FEEDBACK, lw=2.0, ls='--')

# ── Save ───────────────────────────────────────────────────────
plt.tight_layout(pad=0.3)
fig.savefig(r'G:\Mtech-Project\AIOPS\Conference Paper\architecture.png',
            dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print("Architecture diagram saved successfully!")
plt.close()
