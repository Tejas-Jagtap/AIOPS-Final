"""Detailed inspection of original PPT design elements."""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN
import json

prs = Presentation(r'c:\Users\k64169500\Downloads\AIOPS-main\AIOPS-main\Presentation\ESE_Presentation (1).pptx')

print(f"Slide width: {prs.slide_width} EMU = {prs.slide_width/914400:.2f} inches")
print(f"Slide height: {prs.slide_height} EMU = {prs.slide_height/914400:.2f} inches")
print(f"Total slides: {len(prs.slides)}")
print(f"Available layouts: {[l.name for l in prs.slide_layouts]}")
print()

for i, slide in enumerate(prs.slides):
    print(f"{'='*60}")
    print(f"SLIDE {i+1} - Layout: {slide.slide_layout.name}")
    print(f"{'='*60}")
    
    # Check slide background
    bg = slide.background
    if bg.fill.type is not None:
        print(f"  Background fill type: {bg.fill.type}")
    
    for j, shape in enumerate(slide.shapes):
        print(f"\n  Shape {j}: type={shape.shape_type}, name='{shape.name}'")
        print(f"    Position: left={shape.left} ({shape.left/914400:.2f}in), top={shape.top} ({shape.top/914400:.2f}in)")
        print(f"    Size: width={shape.width} ({shape.width/914400:.2f}in), height={shape.height} ({shape.height/914400:.2f}in)")
        
        # Check fill
        if hasattr(shape, 'fill'):
            try:
                fill = shape.fill
                if fill.type is not None:
                    print(f"    Fill type: {fill.type}")
                    if fill.type == 1:  # Solid
                        try:
                            print(f"    Fill color: {fill.fore_color.rgb}")
                        except:
                            print(f"    Fill color: (theme/inherited)")
            except:
                pass
        
        # Check line
        if hasattr(shape, 'line'):
            try:
                line = shape.line
                if line.fill.type is not None:
                    print(f"    Line type: {line.fill.type}")
                    try:
                        print(f"    Line color: {line.color.rgb}")
                    except:
                        pass
            except:
                pass
        
        if shape.has_text_frame:
            tf = shape.text_frame
            print(f"    Text frame: word_wrap={tf.word_wrap}")
            try:
                print(f"    Vertical anchor: {tf.paragraphs[0].alignment}")
            except:
                pass
            for k, para in enumerate(tf.paragraphs):
                text = para.text
                if text.strip():
                    print(f"    Para {k}: '{text[:80]}{'...' if len(text)>80 else ''}'")
                    try:
                        print(f"      Font size: {para.font.size}")
                        print(f"      Font bold: {para.font.bold}")
                        print(f"      Font name: {para.font.name}")
                        if para.font.color and para.font.color.rgb:
                            print(f"      Font color: {para.font.color.rgb}")
                    except:
                        pass
                    try:
                        print(f"      Alignment: {para.alignment}")
                    except:
                        pass
                    # Check runs
                    for r, run in enumerate(para.runs):
                        if run.text.strip():
                            print(f"      Run {r}: '{run.text[:60]}' size={run.font.size} bold={run.font.bold} name={run.font.name}", end='')
                            try:
                                print(f" color={run.font.color.rgb}", end='')
                            except:
                                print(f" color=(inherited)", end='')
                            print()
        
        if shape.has_table:
            table = shape.table
            print(f"    Table: {len(table.rows)} rows x {len(table.columns)} cols")
            print(f"    Col widths: {[f'{c.width/914400:.2f}in' for c in table.columns]}")
            # Check header cell formatting
            if len(table.rows) > 0:
                cell = table.cell(0, 0)
                print(f"    Header cell 0,0: '{cell.text}'")
                try:
                    print(f"      Cell fill: {cell.fill.type}")
                    if cell.fill.type == 1:
                        print(f"      Cell fill color: {cell.fill.fore_color.rgb}")
                except:
                    pass
                for p in cell.text_frame.paragraphs:
                    for run in p.runs:
                        print(f"      Header run: size={run.font.size} bold={run.font.bold} color=", end='')
                        try:
                            print(run.font.color.rgb)
                        except:
                            print("(inherited)")
        
        if shape.shape_type == 13:  # Picture
            print(f"    Image: {shape.image.content_type}")
    
    print()
