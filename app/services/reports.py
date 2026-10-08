import csv, json
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def export_json(path, data):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(data,default=str,ensure_ascii=False,indent=2),encoding="utf8")

def export_csv(path, rows):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    rows=list(rows)
    if not rows: return
    keys=sorted({k for r in rows for k in r})
    with open(path,"w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)

def export_pdf(path,title,lines):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(path,pagesize=letter); y=750
    c.setFont("Helvetica-Bold",14); c.drawString(45,y,title); y-=30; c.setFont("Helvetica",9)
    for line in lines:
        for part in str(line)[:120].split("\n"):
            if y<50: c.showPage(); y=750; c.setFont("Helvetica",9)
            c.drawString(45,y,part); y-=13
    c.save()
