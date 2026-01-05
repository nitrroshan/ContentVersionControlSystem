"""
Content extractor for different file types.
Extracts comparable content from various file formats.
"""

import json
import csv
from pathlib import Path
from typing import Optional
import xml.etree.ElementTree as ET


class ContentExtractor:
    """Extract content from different file types for comparison."""
    
    @staticmethod
    def extract_text(file_path: str) -> str:
        """Extract text content from .txt files."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    @staticmethod
    def extract_rtf(file_path: str) -> str:
        """Extract text from RTF files (simplified - reads as text)."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    @staticmethod
    def extract_json(file_path: str) -> str:
        """Extract and normalize JSON content."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Normalize by re-serializing with consistent formatting
        return json.dumps(data, indent=2, sort_keys=True)
    
    @staticmethod
    def extract_xml(file_path: str) -> str:
        """Extract XML content."""
        tree = ET.parse(file_path)
        return ET.tostring(tree.getroot(), encoding='unicode')
    
    @staticmethod
    def extract_csv(file_path: str) -> str:
        """Extract CSV content as normalized text."""
        with open(file_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
        return '\n'.join([','.join(row) for row in rows])
    
    @staticmethod
    def extract_docx(file_path: str) -> str:
        """Extract text from DOCX files."""
        try:
            import docx
            doc = docx.Document(file_path)
            return '\n'.join([para.text for para in doc.paragraphs])
        except ImportError:
            # If python-docx is not available, store as binary
            return f"[DOCX file - requires python-docx library]"
        except Exception as e:
            return f"[Error extracting DOCX: {e}]"
    
    @staticmethod
    def extract_odt(file_path: str) -> str:
        """Extract text from ODT files."""
        try:
            from odf import text, teletype
            from odf.opendocument import load
            
            doc = load(file_path)
            all_text = []
            for para in doc.getElementsByType(text.P):
                all_text.append(teletype.extractText(para))
            return '\n'.join(all_text)
        except ImportError:
            return f"[ODT file - requires odfpy library]"
        except Exception as e:
            return f"[Error extracting ODT: {e}]"
    
    @staticmethod
    def extract_pdf(file_path: str) -> str:
        """Extract text from PDF files."""
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = []
                for page in reader.pages:
                    text.append(page.extract_text())
                return '\n'.join(text)
        except ImportError:
            return f"[PDF file - requires PyPDF2 library]"
        except Exception as e:
            return f"[Error extracting PDF: {e}]"
    
    @staticmethod
    def extract_content(file_path: str) -> tuple[bytes, Optional[str]]:
        """
        Extract content from a file.
        Returns (raw_bytes, extracted_text) tuple.
        extracted_text is None for binary files without extraction.
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        # Read raw bytes
        with open(file_path, 'rb') as f:
            raw_content = f.read()
        
        # Extract text representation if possible
        try:
            if extension == '.txt':
                text_content = ContentExtractor.extract_text(file_path)
            elif extension == '.rtf':
                text_content = ContentExtractor.extract_rtf(file_path)
            elif extension == '.json':
                text_content = ContentExtractor.extract_json(file_path)
            elif extension == '.xml':
                text_content = ContentExtractor.extract_xml(file_path)
            elif extension == '.csv':
                text_content = ContentExtractor.extract_csv(file_path)
            elif extension == '.docx':
                text_content = ContentExtractor.extract_docx(file_path)
            elif extension == '.odt':
                text_content = ContentExtractor.extract_odt(file_path)
            elif extension == '.pdf':
                text_content = ContentExtractor.extract_pdf(file_path)
            else:
                # For unknown types, try to decode as text
                try:
                    text_content = raw_content.decode('utf-8')
                except UnicodeDecodeError:
                    text_content = None
            
            return raw_content, text_content
        except Exception:
            # If extraction fails, return only raw content
            return raw_content, None
