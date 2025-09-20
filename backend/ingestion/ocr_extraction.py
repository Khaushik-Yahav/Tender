"""
Enhanced OCR Extraction for Tender Evaluation System
Multi-modal document processing with advanced OCR and layout analysis
"""
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import fitz  # PyMuPDF
import os
import logging
from typing import List, Dict, Any, Tuple, Optional, Union
from pathlib import Path
import io
import base64

from backend.config import TESSERACT_CONFIG, SUPPORTED_FILE_TYPES

logger = logging.getLogger(__name__)

class AdvancedOCRProcessor:
    def __init__(self):
        self.supported_formats = {
            '.pdf': self._process_pdf,
            '.png': self._process_image,
            '.jpg': self._process_image,
            '.jpeg': self._process_image,
            '.bmp': self._process_image,
            '.tiff': self._process_image,
            '.tif': self._process_image
        }
    
    def extract_text_from_file(self, file_path: Union[str, Path], 
                              enhance_image: bool = True) -> Dict[str, Any]:
        """
        Extract text from various file formats with metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_extension = file_path.suffix.lower()
        
        if file_extension not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        try:
            processor = self.supported_formats[file_extension]
            result = processor(file_path, enhance_image)
            
            # Add common metadata
            result.update({
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'file_extension': file_extension
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'error': str(e),
                'file_path': str(file_path)
            }
    
    def _process_pdf(self, file_path: Path, enhance_image: bool = True) -> Dict[str, Any]:
        """
        Process PDF with text extraction and OCR for scanned pages
        """
        try:
            doc = fitz.open(file_path)
            
            all_text = []
            page_data = []
            total_confidence = 0
            ocr_pages = 0
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # First try to extract text directly
                page_text = page.get_text()
                
                page_info = {
                    'page_number': page_num + 1,
                    'extracted_text': page_text,
                    'is_scanned': False,
                    'confidence': 1.0 if page_text.strip() else 0.0
                }
                
                # If no text found, likely a scanned page - use OCR
                if not page_text.strip():
                    logger.info(f"Page {page_num + 1} appears to be scanned, applying OCR")
                    
                    # Convert page to image
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # Apply OCR
                    ocr_result = self._extract_text_from_image(img, enhance_image)
                    page_text = ocr_result['text']
                    
                    page_info.update({
                        'extracted_text': page_text,
                        'is_scanned': True,
                        'confidence': ocr_result['confidence'],
                        'ocr_data': ocr_result.get('ocr_data', {})
                    })
                    
                    total_confidence += ocr_result['confidence']
                    ocr_pages += 1
                else:
                    total_confidence += 1.0
                
                all_text.append(page_text)
                page_data.append(page_info)
            
            # Calculate overall confidence
            avg_confidence = total_confidence / len(doc) if len(doc) > 0 else 0.0
            
            result = {
                'text': '\n\n'.join(all_text),
                'confidence': avg_confidence,
                'total_pages': len(doc),
                'ocr_pages': ocr_pages,
                'page_data': page_data,
                'document_type': 'pdf'
            }
            
            # Extract additional metadata
            metadata = doc.metadata
            if metadata:
                result['pdf_metadata'] = {
                    'title': metadata.get('title', ''),
                    'author': metadata.get('author', ''),
                    'subject': metadata.get('subject', ''),
                    'creator': metadata.get('creator', ''),
                    'creation_date': metadata.get('creationDate', ''),
                    'modification_date': metadata.get('modDate', '')
                }
            
            doc.close()
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise
    
    def _process_image(self, file_path: Path, enhance_image: bool = True) -> Dict[str, Any]:
        """
        Process image file with OCR
        """
        try:
            img = Image.open(file_path)
            result = self._extract_text_from_image(img, enhance_image)
            result['document_type'] = 'image'
            return result
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise
    
    def _extract_text_from_image(self, image: Image.Image, 
                               enhance_image: bool = True) -> Dict[str, Any]:
        """
        Extract text from PIL Image with preprocessing and confidence scoring
        """
        try:
            # Preprocess image if requested
            if enhance_image:
                image = self._preprocess_image(image)
            
            # Extract text with detailed data
            ocr_data = pytesseract.image_to_data(
                image, 
                config=TESSERACT_CONFIG,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text
            text = pytesseract.image_to_string(image, config=TESSERACT_CONFIG)
            
            # Calculate confidence
            confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Extract word-level information
            words_data = []
            for i in range(len(ocr_data['text'])):
                if int(ocr_data['conf'][i]) > 0:
                    word_info = {
                        'text': ocr_data['text'][i],
                        'confidence': int(ocr_data['conf'][i]),
                        'bbox': {
                            'left': ocr_data['left'][i],
                            'top': ocr_data['top'][i],
                            'width': ocr_data['width'][i],
                            'height': ocr_data['height'][i]
                        },
                        'block_num': ocr_data['block_num'][i],
                        'par_num': ocr_data['par_num'][i],
                        'line_num': ocr_data['line_num'][i],
                        'word_num': ocr_data['word_num'][i]
                    }
                    words_data.append(word_info)
            
            result = {
                'text': text,
                'confidence': avg_confidence / 100.0,  # Normalize to 0-1
                'word_count': len([w for w in words_data if w['text'].strip()]),
                'ocr_data': {
                    'words': words_data,
                    'avg_confidence': avg_confidence,
                    'total_words': len(words_data)
                },
                'image_info': {
                    'width': image.width,
                    'height': image.height,
                    'mode': image.mode,
                    'format': image.format
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in OCR extraction: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy
        """
        try:
            # Convert to grayscale if needed
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            # Apply slight gaussian blur to reduce noise
            image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
            
            # Convert to numpy array for OpenCV operations
            img_array = np.array(image)
            
            # Apply adaptive thresholding
            img_array = cv2.adaptiveThreshold(
                img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Morphological operations to clean up the image
            kernel = np.ones((1, 1), np.uint8)
            img_array = cv2.morphologyEx(img_array, cv2.MORPH_CLOSE, kernel)
            img_array = cv2.morphologyEx(img_array, cv2.MORPH_OPEN, kernel)
            
            # Convert back to PIL Image
            processed_image = Image.fromarray(img_array)
            
            return processed_image
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}, using original image")
            return image
    
    def extract_tables_from_pdf(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Extract tables from PDF (basic implementation)
        """
        try:
            doc = fitz.open(file_path)
            tables = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Find tables using layout analysis
                tabs = page.find_tables()
                
                for tab in tabs:
                    table_data = tab.extract()
                    if table_data:
                        tables.append({
                            'page_number': page_num + 1,
                            'table_data': table_data,
                            'bbox': tab.bbox
                        })
            
            doc.close()
            return tables
            
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            return []
    
    def get_document_layout_analysis(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Analyze document layout and structure
        """
        try:
            if Path(file_path).suffix.lower() == '.pdf':
                return self._analyze_pdf_layout(file_path)
            else:
                return self._analyze_image_layout(file_path)
                
        except Exception as e:
            logger.error(f"Error in layout analysis: {e}")
            return {'error': str(e)}
    
    def _analyze_pdf_layout(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Analyze PDF layout structure"""
        doc = fitz.open(file_path)
        layout_info = {
            'pages': [],
            'total_pages': len(doc),
            'has_tables': False,
            'has_images': False,
            'text_blocks': 0
        }
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Get text blocks
            blocks = page.get_text("dict")["blocks"]
            text_blocks = [b for b in blocks if "lines" in b]
            image_blocks = [b for b in blocks if "ext" in b]
            
            # Find tables
            tables = page.find_tables()
            
            page_info = {
                'page_number': page_num + 1,
                'text_blocks': len(text_blocks),
                'image_blocks': len(image_blocks),
                'tables': len(tables),
                'bbox': page.rect
            }
            
            layout_info['pages'].append(page_info)
            layout_info['text_blocks'] += len(text_blocks)
            
            if tables:
                layout_info['has_tables'] = True
            if image_blocks:
                layout_info['has_images'] = True
        
        doc.close()
        return layout_info
    
    def _analyze_image_layout(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Analyze image layout using OCR data"""
        img = Image.open(file_path)
        
        # Get detailed OCR data
        ocr_data = pytesseract.image_to_data(
            img, 
            output_type=pytesseract.Output.DICT
        )
        
        # Analyze layout
        blocks = set(ocr_data['block_num'])
        paragraphs = set(ocr_data['par_num'])
        lines = set(ocr_data['line_num'])
        
        return {
            'image_dimensions': {'width': img.width, 'height': img.height},
            'text_blocks': len(blocks),
            'paragraphs': len(paragraphs),
            'lines': len(lines),
            'words': len([w for w in ocr_data['text'] if w.strip()]),
            'layout_confidence': np.mean([c for c in ocr_data['conf'] if c > 0])
        }

# Global OCR processor instance
ocr_processor = AdvancedOCRProcessor()

# Convenience functions for backward compatibility
def extract_text_from_image(image_path: str) -> str:
    """Extract text from image file"""
    try:
        result = ocr_processor.extract_text_from_file(image_path)
        return result.get('text', '')
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        return ''

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file"""
    try:
        result = ocr_processor.extract_text_from_file(pdf_path)
        return result.get('text', '')
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        return ''

def process_document(file_path: str) -> Dict[str, Any]:
    """Process any supported document type"""
    return ocr_processor.extract_text_from_file(file_path)
