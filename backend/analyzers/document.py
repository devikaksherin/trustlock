import os
import zipfile
import pypdf
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from .media import inspect_image, UnreadableFile

def _parse_pdf_date(date_str: str):
    # PDF dates are like D:YYYYMMDDHHmmSSZ
    if not date_str: return None
    s = date_str.replace("D:", "").replace("'", "").replace("Z", "")
    if len(s) >= 14:
        try:
            return datetime.strptime(s[:14], "%Y%m%d%H%M%S")
        except ValueError:
            pass
    return None

def inspect_document(path: str, ext: str):
    findings = []
    notes = []
    extracted_text = ""
    
    ext = ext.lower().replace(".", "")
    
    try:
        if ext == "pdf":
            try:
                reader = pypdf.PdfReader(path)
                encrypted = reader.is_encrypted
                findings.append({"key": "encrypted", "label": "Encrypted", "value": "Yes" if encrypted else "No", "source": "measured"})
                
                if not encrypted:
                    pages = len(reader.pages)
                    findings.append({"key": "page_count", "label": "Page Count", "value": pages, "source": "measured"})
                    
                    text_parts = []
                    for i in range(min(5, pages)):
                        page = reader.pages[i]
                        text = page.extract_text() or ""
                        text_parts.append(text)
                        
                    full_text = "\n".join(text_parts)[:20000]
                    extracted_text = full_text
                    
                    extractable = bool(full_text.strip())
                    findings.append({"key": "text_extractable", "label": "Text Extractable", "value": "Yes" if extractable else "No", "source": "measured"})
                    if extractable:
                        findings.append({"key": "chars_extracted", "label": "Characters Extracted", "value": len(full_text), "source": "measured"})
                    else:
                        notes.append("No extractable text (possibly scanned). OCR is not implemented.")
                        # TODO(real-model): OCR for scanned documents.
                        
                    meta = reader.metadata or {}
                    producer = meta.get("/Producer", "")
                    creator = meta.get("/Creator", "")
                    creation_date = meta.get("/CreationDate", "")
                    mod_date = meta.get("/ModDate", "")
                    
                    if producer: findings.append({"key": "producer", "label": "Producer", "value": producer, "source": "measured"})
                    if creator: findings.append({"key": "creator", "label": "Creator", "value": creator, "source": "measured"})
                    
                    cd = _parse_pdf_date(creation_date)
                    md = _parse_pdf_date(mod_date)
                    if cd: findings.append({"key": "creation_date", "label": "Creation Date", "value": cd.isoformat(), "source": "measured"})
                    if md: findings.append({"key": "mod_date", "label": "Modification Date", "value": md.isoformat(), "source": "measured"})
            except Exception as e:
                raise UnreadableFile(f"PDF read error: {str(e)}")
                
        elif ext == "txt":
            try:
                with open(path, "r", encoding="utf-8") as f:
                    extracted_text = f.read(204800) # 200 KB cap
            except UnicodeDecodeError:
                raise UnreadableFile("TXT file must be UTF-8")
                
        elif ext == "docx":
            try:
                with zipfile.ZipFile(path) as z:
                    try:
                        with z.open("docProps/core.xml") as f:
                            tree = ET.parse(f)
                            root = tree.getroot()
                            ns = {
                                "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
                                "dc": "http://purl.org/dc/elements/1.1/",
                                "dcterms": "http://purl.org/dc/terms/"
                            }
                            creator = root.findtext("dc:creator", namespaces=ns)
                            last_mod_by = root.findtext("cp:lastModifiedBy", namespaces=ns)
                            created = root.findtext("dcterms:created", namespaces=ns)
                            modified = root.findtext("dcterms:modified", namespaces=ns)
                            
                            if creator: findings.append({"key": "creator", "label": "Creator", "value": creator, "source": "measured"})
                            if last_mod_by: findings.append({"key": "last_modified_by", "label": "Last Modified By", "value": last_mod_by, "source": "measured"})
                            if created: findings.append({"key": "creation_date", "label": "Creation Date", "value": created, "source": "measured"})
                            if modified: findings.append({"key": "mod_date", "label": "Modification Date", "value": modified, "source": "measured"})
                    except KeyError:
                        notes.append("No core.xml found in docx")
            except zipfile.BadZipFile:
                raise UnreadableFile("Bad DOCX file")
                
        elif ext in ("jpg", "jpeg", "png", "webp"):
            img_f, img_n = inspect_image(path)
            return img_f, img_n, ""

            
    except Exception as e:
        if isinstance(e, UnreadableFile):
            raise e
        raise UnreadableFile(str(e))
        
    return findings, notes, extracted_text
