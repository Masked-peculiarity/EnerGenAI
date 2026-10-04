from io import BytesIO
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import pdfplumber
from PIL import Image

def safe_filename(filename):
    return re.sub(r"[^\w.\- ]","_",Path(filename.replace("\\","/")).name)[:120]

def extract_text(filename,content,allow_image=False):
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt",".md"}:
        return content.decode("utf-8-sig",errors="replace")
    if suffix==".pdf":
        with pdfplumber.open(BytesIO(content)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages[:100])
    if allow_image and suffix in {".png",".jpg",".jpeg"}:
        executable = shutil.which("tesseract")
        if not executable:
            raise ValueError("Image bills require local Tesseract OCR. Upload a selectable-text PDF, or install Tesseract and add it to PATH.")
        with tempfile.TemporaryDirectory() as folder:
            image_path = Path(folder)/"bill.png"
            with Image.open(BytesIO(content)) as image:
                image.convert("RGB").save(image_path)
            return subprocess.run([executable,str(image_path),"stdout"],capture_output=True,text=True,timeout=25,check=True).stdout
    raise ValueError("Unsupported document format")

def analyze_bill(filename,content):
    text = extract_text(filename,content,allow_image=True)
    if not text.strip():
        raise ValueError("No selectable text found; scan needs OCR")
    def find(pattern):
        match = re.search(pattern,text,re.I)
        return match.group(1).strip() if match else None
    total = find(r"(?:total\s+(?:energy|consumption|units)|energy\s+consumed|consumption)\s*[:=]?\s*([\d,]+(?:\.\d+)?)\s*kWh")
    amount = find(r"(?:total\s+(?:amount|due)|amount\s+(?:due|payable))\s*[:=]?\s*(?:Rs\.?|INR|USD|EUR|\$|€)?\s*([\d,]+(?:\.\d+)?)")
    rate = find(r"(?:tariff|rate)\s*[:=]?\s*(?:Rs\.?|INR|USD|EUR|\$|€)?\s*(\d+(?:\.\d+)?)\s*(?:/|per)\s*kWh")
    fields = {"billing_period":find(r"billing\s+period\s*[:=]\s*([^\n]+)"),"total_kwh":float(total.replace(",","")) if total else None,
              "amount":float(amount.replace(",","")) if amount else None,"tariff_per_kwh":float(rate) if rate else None,
              "due_date":find(r"due\s+date\s*[:=]\s*([^\n]+)")}
    return {"source":filename,"fields":fields,"requires_confirmation":True,"method":"local text/OCR and labeled-field extraction",
            "comparison":"This bill belongs to its customer; the unrelated UCI demo household is not a valid billing comparator."}
