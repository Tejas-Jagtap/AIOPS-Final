"""
Generate Phase-II PPT matching the EXACT design pattern of original PPT.
Strategy: Open original PPT (preserves theme/fonts/master), delete all
existing slides, rebuild with Phase-II content using same layout.

Original pattern (from inspection):
- Layout: "Title Slide" (index 0) for ALL slides
- Footer: COEP logo + dept text + separator line (manually on each slide)
- Title: ~40pt bold, positioned near top
- Content: ~24pt, JUSTIFY aligned
- Slide numbers in bottom-right
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

# ---- Paths ----
BASE = r'c:\Users\k64169500\Downloads\AIOPS-main\AIOPS-main'
OLD_PPT = os.path.join(BASE, 'Presentation', 'ESE_Presentation (1).pptx')
NEW_PPT = os.path.join(BASE, 'Presentation', 'ESE_Phase2_v2.pptx')
PLOTS = os.path.join(BASE, 'evaluation', 'plots')
REPORT = os.path.join(BASE, 'Report')
LOGO_TMP = os.path.join(BASE, 'Presentation', '_logo.jpg')

# ---- Step 1: Extract COEP logo from original PPT ----
src = Presentation(OLD_PPT)
for s in src.slides[0].shapes:
    if s.shape_type == 13:  # Picture
        with open(LOGO_TMP, 'wb') as f:
            f.write(s.image.blob)
        print(f"Extracted logo: {s.image.content_type}")
        break

# ---- Step 2: Open original PPT (preserves theme, master, layouts) ----
prs = Presentation(OLD_PPT)
print(f"Slide dimensions: {prs.slide_width/914400:.2f} x {prs.slide_height/914400:.2f} inches")

# ---- Step 3: Delete all existing slides ----
sldIdLst = prs.slides._sldIdLst
for elem in list(sldIdLst):
    rId = elem.get(qn('r:id'))
    prs.part.drop_rel(rId)
    sldIdLst.remove(elem)
print(f"Cleared {15} original slides")

# ---- Layout ----
layout = prs.slide_layouts[0]  # "Title Slide"

# ---- Colors (exact values from original inspection) ----
FOOTER_CLR = RGBColor(0x20, 0x38, 0x64)   # #203864 - footer text
SEP_CLR    = RGBColor(0x32, 0x54, 0x90)   # #325490 - separator line
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)

# ---- Exact measurements from original PPT (EMU precision) ----
# Footer elements (identical on every slide)
LOGO_L, LOGO_T  = 554040, 5662800      # (0.61in, 6.19in)
LOGO_W, LOGO_H  = 1283400, 1173960     # (1.40in, 1.28in)
FTR_L, FTR_T    = 1963440, 5648760     # (2.15in, 6.18in)
FTR_W, FTR_H    = 9249120, 1106542     # (10.11in, 1.21in)
SEP_T            = 5533200              # 6.05in
SEP_W, SEP_H    = 12191400, 114840     # (13.33in, 0.13in)
SN_L, SN_T      = 8610600, 6356350     # (9.42in, 6.95in)
SN_W, SN_H      = 2743200, 365125      # (3.00in, 0.40in)
# Title (content slides)
TTL_L            = 851254               # 0.93in
TTL_W, TTL_H    = 10488891, 827882     # (11.47in, 0.91in)
TTL_SZ           = 508000              # 40pt
# Content area (content slides)
CNT_L            = 789270               # 0.86in
CNT_T            = 1149378              # 1.26in
CNT_W, CNT_H    = 10612859, 3835922    # (11.61in, 4.20in)
CNT_SZ           = 304800              # 24pt


# ===========================================================
# HELPER FUNCTIONS (matching original PPT pattern exactly)
# ===========================================================

def add_footer(slide, slide_num):
    """Add the 4 footer elements matching original PPT exactly."""
    # 1. COEP logo (jpeg, bottom-left)
    slide.shapes.add_picture(LOGO_TMP, LOGO_L, LOGO_T, LOGO_W, LOGO_H)

    # 2. Footer text box (dept + university, centered, Times New Roman 24pt bold)
    tb = slide.shapes.add_textbox(FTR_L, FTR_T, FTR_W, FTR_H)
    tb.fill.background()
    tb.line.fill.background()
    tf = tb.text_frame
    # Vertical centering
    bodyPr = tf._txBody.find(qn('a:bodyPr'))
    bodyPr.set('anchor', 'ctr')

    p1 = tf.paragraphs[0]
    p1.alignment = PP_ALIGN.CENTER
    r1 = p1.add_run()
    r1.text = "Dept of Computer Science and Engineering"
    r1.font.size = Pt(24)
    r1.font.bold = True
    r1.font.name = "Times New Roman"
    r1.font.color.rgb = FOOTER_CLR

    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    r2 = p2.add_run()
    r2.text = "COEP Technological University, Pune"
    r2.font.size = Pt(24)
    r2.font.bold = True
    r2.font.name = "Times New Roman"
    r2.font.color.rgb = FOOTER_CLR

    # 3. Separator line (full-width colored rectangle)
    sep = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, SEP_T, SEP_W, SEP_H)
    sep.fill.solid()
    sep.fill.fore_color.rgb = SEP_CLR
    sep.line.color.rgb = SEP_CLR

    # 4. Slide number (bottom-right)
    sn = slide.shapes.add_textbox(SN_L, SN_T, SN_W, SN_H)
    sn.text_frame.paragraphs[0].text = str(slide_num)


def set_title(slide, text, top=246660):
    """Set title using placeholder[0], repositioned to match original."""
    ph = slide.placeholders[0]
    ph.left = TTL_L
    ph.top = top
    ph.width = TTL_W
    ph.height = TTL_H
    p = ph.text_frame.paragraphs[0]
    p.text = text
    for run in p.runs:
        run.font.size = Emu(TTL_SZ)
        run.font.bold = True
    return ph


def set_content(slide, lines, font_size=CNT_SZ, align=PP_ALIGN.JUSTIFY,
                left=None, top=None, width=None, height=None):
    """Set content using placeholder[1], repositioned to match original."""
    ph = slide.placeholders[1]
    ph.left  = left  or CNT_L
    ph.top   = top   or CNT_T
    ph.width = width or CNT_W
    ph.height = height or CNT_H
    tf = ph.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = line
        r.font.size = Emu(font_size)
    return ph


def remove_placeholder(slide, idx):
    """Remove a placeholder from the slide XML."""
    if idx in slide.placeholders:
        sp = slide.placeholders[idx]._element
        sp.getparent().remove(sp)


def add_textbox(slide, left, top, width, height):
    """Add a textbox and return the text frame."""
    tb = slide.shapes.add_textbox(left, top, width, height)
    tb.fill.background()
    return tb.text_frame


def add_content_textbox(slide, left, top, width, height, lines,
                        font_size=CNT_SZ, align=PP_ALIGN.JUSTIFY):
    """Add a textbox with content lines (for when placeholder is not suitable)."""
    tb = slide.shapes.add_textbox(left, top, width, height)
    tb.fill.background()
    tf = tb.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = line
        r.font.size = Emu(font_size)
    return tf


def add_image_safe(slide, path, left, top, width, height=None):
    """Add image if file exists."""
    if os.path.exists(path):
        if height:
            slide.shapes.add_picture(path, left, top, width, height)
        else:
            slide.shapes.add_picture(path, left, top, width)
        return True
    print(f"  WARNING: not found: {path}")
    return False


def make_table(slide, rows, cols, left, top, width, height,
               headers, data, header_font=Pt(11), data_font=Pt(10)):
    """Create a table matching original PPT style."""
    ts = slide.shapes.add_table(rows, cols, left, top, width, height)
    tbl = ts.table
    # Header row
    for i, h in enumerate(headers):
        cell = tbl.cell(0, i)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = SEP_CLR
        for p in cell.text_frame.paragraphs:
            for run in p.runs:
                run.font.size = header_font
                run.font.bold = True
                run.font.color.rgb = WHITE
    # Data rows
    for r, row_data in enumerate(data, 1):
        for c, val in enumerate(row_data):
            cell = tbl.cell(r, c)
            cell.text = val
            for p in cell.text_frame.paragraphs:
                for run in p.runs:
                    run.font.size = data_font
    return tbl


# ===========================================================
# BUILD ALL SLIDES
# ===========================================================

# ============================================================
# SLIDE 1: Title Slide
# ============================================================
s = prs.slides.add_slide(layout)
# Title placeholder - keep at original title slide position
ph0 = s.placeholders[0]
ph0.left = TTL_L
ph0.top = 382078         # 0.42in (original)
ph0.width = TTL_W
ph0.height = 2078317     # 2.27in (original - taller for multiline)
p = ph0.text_frame.paragraphs[0]
p.text = "Intelligent AIOps Framework for Predictive CI/CD\nPipeline Management and Autonomous Resource\nOptimization"
for run in p.runs:
    run.font.size = Emu(TTL_SZ)
    run.font.bold = True

# Subtitle - author info
ph1 = s.placeholders[1]
ph1.left = 1524000       # 1.67in
ph1.top = 2888997        # 3.16in
ph1.width = 9144000      # 10.00in
ph1.height = 1371918     # 1.50in
tf = ph1.text_frame
tf.paragraphs[0].text = "Tejas Annasaheb Jagtap"
tf.add_paragraph().text = "MTech Information Security"
tf.add_paragraph().text = "712442021"

# Guide name (separate textbox like original)
gtf = add_textbox(s, 1523700, 4689517, 9144000, 570640)
p_g = gtf.paragraphs[0]
r_g = p_g.add_run()
r_g.text = "Guide: Dr. V. K. Pachghare"
r_g.font.bold = True

add_footer(s, 1)
print("  Slide 1: Title")

# ============================================================
# SLIDE 2: Contents
# ============================================================
s = prs.slides.add_slide(layout)
set_title(s, "Contents", top=382079)
set_content(s, [
    "Introduction",
    "Literature Survey",
    "Research Gap",
    "Problem Statement",
    "Research Objectives",
    "Proposed High Level System Design",
    "Phase-II: Implementation & Evaluation",
    "    Synthetic Data Generation",
    "    Model Training (XGBoost, Autoencoder, LSTM)",
    "    Evaluation Results",
    "Future Plan (Phase-III)",
    "References",
], align=PP_ALIGN.LEFT, top=1209960)
add_footer(s, 2)
print("  Slide 2: Contents")

# ============================================================
# SLIDE 3: Introduction
# ============================================================
s = prs.slides.add_slide(layout)
set_title(s, "Introduction", top=117110)
set_content(s, [
    "Modern software systems rely heavily on continuous integration and continuous deployment (CI/CD) pipelines for rapid delivery",
    "These pipelines generate massive volumes of logs and metrics",
    "DevOps teams struggle with:",
    "Unpredictable build failures wasting time and resources",
    "Manual debugging of thousands of log lines",
    "Reactive (not proactive) Kubernetes scaling decisions",
    "AIOps (AI for IT Operations) integrates Machine Learning + Automation to enhance CI/CD reliability and infrastructure management",
])
add_footer(s, 3)
print("  Slide 3: Introduction")

# ============================================================
# SLIDE 4: Motivation
# ============================================================
s = prs.slides.add_slide(layout)
set_title(s, "Motivation")
set_content(s, [
    "Frequent build failures lead to deployment delays and wasted compute",
    "Manual root-cause analysis is slow and error-prone",
    "Traditional autoscaling in Kubernetes reacts AFTER resource spikes occur",
    "DevOps teams spend significant effort analyzing logs and failures",
    "Need for an automated, self-learning system that:",
    "Predicts failures early using historical build patterns",
    "Detects anomalies in logs immediately using ML",
    "Allocates resources proactively based on forecasts",
    "Reduces operational burden and improves delivery speed",
])
add_footer(s, 4)
print("  Slide 4: Motivation")

# ============================================================
# SLIDE 5: Literature Survey (table 1)
# ============================================================
s = prs.slides.add_slide(layout)
set_title(s, "Literature Survey", top=206797)
remove_placeholder(s, 1)  # Remove subtitle - using table instead

tbl = make_table(s, 4, 4,
    Inches(0.32), Inches(1.27), Inches(12.69), Inches(4.20),
    ["Sr.", "Paper Name", "Work Done", "Limitations"],
    [
        ["1", "Enhancing ML-Based Autoscaling for Cloud Resource Orchestration (2024)",
         "Evaluates ML models for autoscaling; compares architectures for predicting load.",
         "Focuses on autoscaling alone; no CI/CD or log integration."],
        ["2", "Time-series Forecasting-Based K8s Autoscaling Using Prophet and LSTM (2025)",
         "Hybrid Prophet+LSTM approach for cluster metric prediction and scaling.",
         "No CI/CD signals or log anomalies; evaluates autoscaling in isolation."],
        ["3", "Deep Learning for Multivariate Time-Series Anomaly Detection (2025)",
         "Survey of autoencoders, VAEs for anomaly detection; benchmarks thresholds.",
         "Survey-level; no concrete DevOps pipeline application for CI logs."],
    ], data_font=Pt(9))
tbl.columns[0].width = Inches(0.48)
tbl.columns[1].width = Inches(2.41)
tbl.columns[2].width = Inches(4.27)
tbl.columns[3].width = Inches(5.54)

add_footer(s, 5)
print("  Slide 5: Literature Survey (1)")

# ============================================================
# SLIDE 6: Literature Survey (table 2)
# ============================================================
s = prs.slides.add_slide(layout)
remove_placeholder(s, 0)
remove_placeholder(s, 1)

tbl2 = make_table(s, 5, 4,
    Inches(0.12), Inches(0.11), Inches(13.12), Inches(6.10),
    ["Sr.", "Paper Name", "Work Done", "Limitations"],
    [
        ["4", "Towards Optimization of Anomaly Detection in DevOps (2023)",
         "Evaluates anomaly detection techniques for DevOps monitoring.",
         "No CI/CD build prediction; focuses only on runtime anomalies."],
        ["5", "AI-Enhanced Platform Engineering: Revolutionizing CI/CD Pipelines (2025)",
         "Proposes AI integration for CI/CD optimization and resource management.",
         "Conceptual framework; no trained models or experimental validation."],
        ["6", "Predictive Failure Analysis in CI Pipelines Using Ensemble Trees (2025)",
         "Ensemble tree models for CI build failure prediction from metadata.",
         "Limited dataset; no anomaly detection or predictive scaling integration."],
        ["7", "Empirical Analysis on CI/CD Pipeline Evolution: Failures and Bottlenecks (2024)",
         "Identifies common failure causes, temporal patterns, and bottlenecks.",
         "Descriptive study; no automated ML solutions proposed."],
    ], data_font=Pt(9))
tbl2.columns[0].width = Inches(0.42)
tbl2.columns[1].width = Inches(2.70)
tbl2.columns[2].width = Inches(4.14)
tbl2.columns[3].width = Inches(5.86)

add_footer(s, 6)
print("  Slide 6: Literature Survey (2)")

# ============================================================
# SLIDE 7: Research Gap
# ============================================================
s = prs.slides.add_slide(layout)
set_title(s, "Research Gap")
set_content(s, [
    "No unified AIOps framework combining:",
    "Build failure prediction",
    "Log anomaly detection",
    "CPU forecasting",
    "Predictive autoscaling",
    "Lack of predictive autoscaling",
    "Limited real-world CI/CD datasets",
    "Lack of closed-loop automation integrating Jenkins \u2192 ML \u2192 Kubernetes.",
])
add_footer(s, 7)
print("  Slide 7: Research Gap")

# ============================================================
# SLIDE 8: Problem Statement
# ============================================================
s = prs.slides.add_slide(layout)
set_title(s, "Problem Statement", top=380148)
set_content(s, [
    '"To design and implement an intelligent AIOps-based framework that can proactively predict CI/CD pipeline failures, detect anomalies in Jenkins logs in real time, and autonomously optimize Kubernetes resources through predictive autoscaling."',
], top=2033543, height=1421928)
add_footer(s, 8)
print("  Slide 8: Problem Statement")

# ============================================================
# SLIDE 9: Research Objectives
# ============================================================
s = prs.slides.add_slide(layout)
set_title(s, "Research Objectives", top=382079)
set_content(s, [
    "To Develop Data Collection Framework for CI/CD and Cluster Metrics",
    "To Build Machine Learning Models for Failure Prediction, Anomaly Detection, and CPU Forecasting",
    "To Implement a FastAPI-Based AIOps Orchestrator for Intelligent Decision-Making",
    "To Design a Predictive Autoscaling Engine for Kubernetes Using ML Outputs",
], top=1608941, height=2471446)
add_footer(s, 9)
print("  Slide 9: Research Objectives")

# ============================================================
# SLIDE 10: Proposed High Level System Design
# ============================================================
s = prs.slides.add_slide(layout)
set_title(s, "Proposed High Level System Design", top=21240)
remove_placeholder(s, 1)

# Architecture image (left side)
arch_img = os.path.join(REPORT, 'architecutre.png')
add_image_safe(s, arch_img, 0, 659876, 3946372, 4594637)

# Component descriptions (right side) - matching original
add_content_textbox(s, 3946372, 895232, 7266188, 4524315, [
    "Components:",
    "Data Collectors",
    "Jenkins API for logs + metadata",
    "Prometheus for CPU metrics",
    "ML Layer",
    "XGBoost: Failure prediction",
    "TF-IDF based Autoencoder: Log anomaly detection",
    "LSTM: CPU forecasting",
    "AIOps Orchestrator",
    "FastAPI-based inference layer",
    "Predictive Autoscaler",
    "Kubernetes API for scaling decisions",
])

add_footer(s, 10)
print("  Slide 10: System Architecture")

# ============================================================
# SLIDE 11: Phase-II Implementation - Data Pipeline
# ============================================================
s = prs.slides.add_slide(layout)
set_title(s, "Phase-II: Data Pipeline & Collection", top=161736)
set_content(s, [
    "Synthetic Data Generation (generate_synthetic_data.py):",
    "600 Jenkins build records with realistic metadata",
    "600+ console log files (success, failure, unstable patterns)",
    "10,000+ CPU time-series data points with daily/weekly patterns",
    "",
    "Data Collection Infrastructure:",
    "Jenkins REST API collector for build metadata and logs",
    "Prometheus HTTP API collector for CPU/memory metrics",
    "Real-time streaming collector with configurable intervals",
    "",
    "Data preprocessing pipelines:",
    "TF-IDF vectorization (500 features, ngram 1-2, sublinear TF)",
    "MinMaxScaler normalization for CPU time-series",
    "Feature extraction from build metadata (8 features)",
])
add_footer(s, 11)
print("  Slide 11: Data Pipeline")

# ============================================================
# SLIDE 12: XGBoost - Failure Prediction
# ============================================================
s = prs.slides.add_slide(layout)
set_title(s, "Model 1: XGBoost \u2014 Failure Prediction", top=161736)
remove_placeholder(s, 1)

# Left: approach description
add_content_textbox(s, CNT_L, CNT_T, Inches(5.5), Inches(2.5), [
    "Gradient boosted ensemble of 100 decision trees",
    "Input: 8 features (duration, errors, warnings,",
    "  failures, log_length, tests_failed/passed/total)",
    "Output: Failure probability (0\u20131)",
    "Handles class imbalance via scale_pos_weight",
    "80/20 stratified train-test split",
    "5-Fold Cross Validation: 99.0% \u00b1 0.6% accuracy",
])

# Right: metrics table
tbl = make_table(s, 6, 2,
    Inches(6.5), Inches(1.1), Inches(4.0), Inches(2.8),
    ["Metric", "Value"],
    [["Accuracy", "98.33%"], ["Precision", "93.10%"],
     ["Recall", "100.00%"], ["F1-Score", "96.43%"],
     ["ROC AUC", "100.00%"]])
tbl.columns[0].width = Inches(2.0)
tbl.columns[1].width = Inches(2.0)

# Bottom: evaluation plots
cm_img = os.path.join(PLOTS, 'xgboost_confusion_matrix.png')
fi_img = os.path.join(PLOTS, 'xgboost_feature_importance.png')
add_image_safe(s, cm_img, Inches(0.3), Inches(4.0), Inches(3.8))
add_image_safe(s, fi_img, Inches(4.5), Inches(4.0), Inches(5.5))

add_footer(s, 12)
print("  Slide 12: XGBoost Model")

# ============================================================
# SLIDE 13: Autoencoder - Anomaly Detection
# ============================================================
s = prs.slides.add_slide(layout)
set_title(s, "Model 2: TF-IDF + Autoencoder \u2014 Anomaly Detection", top=161736)
remove_placeholder(s, 1)

# Left: approach
add_content_textbox(s, CNT_L, CNT_T, Inches(5.5), Inches(2.5), [
    "Two-Stage Pipeline:",
    "Stage 1: TF-IDF vectorization (500 features)",
    "  ngram range (1,2), sublinear TF scaling",
    "Stage 2: Autoencoder neural network",
    "  Architecture: 500\u2192128\u219264\u219232\u219264\u2192128\u2192500",
    "  Trained on normal logs only (unsupervised)",
    "  Anomaly = high reconstruction error",
    "Threshold: 95th percentile of normal errors",
])

# Right: metrics table
tbl = make_table(s, 6, 2,
    Inches(6.5), Inches(1.1), Inches(4.0), Inches(2.8),
    ["Metric", "Value"],
    [["Accuracy", "95.87%"], ["Precision", "84.85%"],
     ["Recall", "100.00%"], ["F1-Score", "91.80%"],
     ["ROC AUC", "98.92%"]])
tbl.columns[0].width = Inches(2.0)
tbl.columns[1].width = Inches(2.0)

# Bottom: plots
ae_cm = os.path.join(PLOTS, 'anomaly_confusion_matrix.png')
ae_dist = os.path.join(PLOTS, 'anomaly_error_distribution.png')
add_image_safe(s, ae_cm, Inches(0.3), Inches(4.0), Inches(3.8))
add_image_safe(s, ae_dist, Inches(4.5), Inches(4.0), Inches(5.5))

add_footer(s, 13)
print("  Slide 13: Autoencoder Model")

# ============================================================
# SLIDE 14: LSTM - CPU Forecasting
# ============================================================
s = prs.slides.add_slide(layout)
set_title(s, "Model 3: LSTM \u2014 CPU Forecasting", top=161736)
remove_placeholder(s, 1)

# Left: approach
add_content_textbox(s, CNT_L, CNT_T, Inches(5.5), Inches(2.5), [
    "Input: 60-minute CPU history (sliding window)",
    "Output: Predicted CPU usage 10 minutes ahead",
    "Architecture: LSTM(128) \u2192 LSTM(64) \u2192 Dense(32) \u2192 Dense(1)",
    "MinMaxScaler normalization to [0, 1]",
    "10,000+ training sequences",
    "Early stopping + LR reduction on plateau",
])

# Right: metrics table
tbl = make_table(s, 6, 2,
    Inches(6.5), Inches(1.1), Inches(4.0), Inches(2.5),
    ["Metric", "Value"],
    [["MSE", "0.0050"], ["MAE", "0.0436"],
     ["RMSE", "0.0710"], ["MAPE", "9.56%"],
     ["R\u00b2", "0.435"]])
tbl.columns[0].width = Inches(2.0)
tbl.columns[1].width = Inches(2.0)

# Bottom: plots
lstm_pred = os.path.join(PLOTS, 'lstm_actual_vs_predicted.png')
lstm_scat = os.path.join(PLOTS, 'lstm_scatter.png')
add_image_safe(s, lstm_pred, Inches(0.3), Inches(4.0), Inches(5.5))
add_image_safe(s, lstm_scat, Inches(6.3), Inches(4.0), Inches(3.8))

add_footer(s, 14)
print("  Slide 14: LSTM Model")

# ============================================================
# SLIDE 15: Combined Performance Summary
# ============================================================
s = prs.slides.add_slide(layout)
set_title(s, "Combined Model Performance Summary", top=161736)
remove_placeholder(s, 1)

# Summary table
tbl = make_table(s, 4, 4,
    Inches(0.5), Inches(1.3), Inches(11.5), Inches(2.0),
    ["Module", "Algorithm", "Key Metric", "ROC AUC / R\u00b2"],
    [
        ["Failure Prediction", "XGBoost", "F1 = 0.964", "AUC = 1.000"],
        ["Anomaly Detection", "TF-IDF + Autoencoder", "F1 = 0.918", "AUC = 0.989"],
        ["CPU Forecasting", "LSTM", "RMSE = 0.071", "R\u00b2 = 0.435"],
    ])
tbl.columns[0].width = Inches(2.8)
tbl.columns[1].width = Inches(3.2)
tbl.columns[2].width = Inches(2.5)
tbl.columns[3].width = Inches(3.0)

# Model comparison chart
compare_img = os.path.join(PLOTS, 'model_comparison_summary.png')
add_image_safe(s, compare_img, Inches(1.0), Inches(3.5), Inches(10.0))

add_footer(s, 15)
print("  Slide 15: Combined Summary")

# ============================================================
# SLIDE 16: ROC Curves
# ============================================================
s = prs.slides.add_slide(layout)
set_title(s, "ROC Curves \u2014 Classification Models", top=161736)
remove_placeholder(s, 1)

xgb_roc = os.path.join(PLOTS, 'xgboost_roc_curve.png')
ae_roc = os.path.join(PLOTS, 'anomaly_roc_curve.png')
add_image_safe(s, xgb_roc, Inches(0.3), Inches(1.3), Inches(5.5))
add_image_safe(s, ae_roc, Inches(6.3), Inches(1.3), Inches(5.5))

# Labels
tf1 = add_textbox(s, Inches(0.3), Inches(5.5), Inches(5.5), Inches(0.5))
p1 = tf1.paragraphs[0]
p1.alignment = PP_ALIGN.CENTER
r1 = p1.add_run()
r1.text = "XGBoost: AUC = 1.000"
r1.font.size = Emu(CNT_SZ)
r1.font.bold = True

tf2 = add_textbox(s, Inches(6.3), Inches(5.5), Inches(5.5), Inches(0.5))
p2 = tf2.paragraphs[0]
p2.alignment = PP_ALIGN.CENTER
r2 = p2.add_run()
r2.text = "Autoencoder: AUC = 0.989"
r2.font.size = Emu(CNT_SZ)
r2.font.bold = True

add_footer(s, 16)
print("  Slide 16: ROC Curves")

# ============================================================
# SLIDE 17: Future Plan
# ============================================================
s = prs.slides.add_slide(layout)
set_title(s, "Future Plan", top=161736)
set_content(s, [
    "Phase III: Integration",
    "Connect all models to FastAPI AIOps Orchestrator",
    "Implement APIs: failure, anomaly, CPU forecast",
    "Build predictive autoscaler using ML outputs",
    "Connect autoscaler to Kubernetes API",
    "",
    "Phase IV: Testing & Finalization",
    "End-to-end CI/CD testing",
    "Compare predictive autoscaler vs default HPA",
    "Create monitoring dashboard",
    "Final tuning + final documentation",
], top=1024061, height=4154984)
add_footer(s, 17)
print("  Slide 17: Future Plan")

# ============================================================
# SLIDE 18: References
# ============================================================
s = prs.slides.add_slide(layout)
set_title(s, "References", top=382079)
set_content(s, [
    '[1] I. Pintye, B. Goldschmidt, P. Holicza and A. Kertesz, "Enhancing Machine Learning-Based Autoscaling for Cloud Resource Orchestration," J. Grid Computing, vol. 22, 2024.',
    '[2] P. B. Guruge and Y. H. P. P. Priyadarshana, "Time Series Forecasting-Based Kubernetes Autoscaling Using Prophet and LSTM," Frontiers in CS, vol. 5, 2025.',
    '[3] M. A. Yahya, W. Bakhtawar and M. Usman, "Deep Learning for Multivariate Time Series Anomaly Detection: A Survey," AI Review, 2025.',
    '[4] A. Hrusto, "Towards Optimization of Anomaly Detection in DevOps," IST, vol. 158, 2023.',
    '[5] S. Das and P. Raj, "AI-Enhanced Platform Engineering: Revolutionizing CI/CD Pipelines," IJCEST, 2025.',
    '[6] P. Mathew and A. Baswareddy, "Predictive Failure Analysis in CI Pipelines Using Ensemble Trees," IJACS, 2025.',
    '[7] H. Guo et al., "LogBERT: Transformer-Based Log Anomaly Detection for CI/CD Systems," ICSE, 2021.',
    '[8] A. Houerbi et al., "Empirical Analysis on CI/CD Pipeline Evolution: Failures and Bottlenecks," JSME, 2024.',
], font_size=254000, top=1438739, height=3652282)
add_footer(s, 18)
print("  Slide 18: References")

# ============================================================
# SLIDE 19: Thank You
# ============================================================
s = prs.slides.add_slide(layout)
remove_placeholder(s, 1)
# Title centered vertically (original: top=2.39in, 72pt)
ph = s.placeholders[0]
ph.left = TTL_L
ph.top = 2186339         # 2.39in
ph.width = TTL_W
ph.height = TTL_H
p = ph.text_frame.paragraphs[0]
p.text = "Thank You !!!"
for run in p.runs:
    run.font.size = Pt(72)     # 914400 EMU - original size
    run.font.bold = True

add_footer(s, 19)
print("  Slide 19: Thank You")


# ============================================================
# SAVE
# ============================================================
prs.save(NEW_PPT)
print(f"\nPresentation saved to: {NEW_PPT}")
print(f"Total slides: {len(prs.slides)}")

# Clean up temp logo
try:
    os.remove(LOGO_TMP)
except:
    pass
