"""
Image Solver for Anuj Bot
Analyzes images with doubts and provides handwriting-style solutions
"""

import os
import cv2
import numpy as np
import logging
import random
import math
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import pytesseract

# Make easyocr optional
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("EasyOCR not available, using only Tesseract for OCR")

from openai import OpenAI

from config.settings import MAX_IMAGE_SIZE, SOLUTION_FONT_SIZE, SOLUTION_COLOR, OPENAI_API_KEY

logger = logging.getLogger(__name__)

class ImageSolver:
    def __init__(self):
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Initialize OCR reader if available
        if EASYOCR_AVAILABLE:
            self.ocr_reader = easyocr.Reader(['en', 'hi'])  # English and Hindi
        else:
            self.ocr_reader = None
        
        # Load handwriting-style fonts
        self.handwriting_fonts = self.load_handwriting_fonts()
        
        # Colors for handwritten solutions (various pen colors)
        self.pen_colors = [
            (0, 0, 255),      # Red
            (0, 100, 255),    # Orange-Red
            (255, 0, 0),      # Blue
            (0, 150, 0),      # Dark Green
            (128, 0, 128),    # Purple
            (255, 20, 147),   # Deep Pink
            (0, 0, 139),      # Dark Blue
        ]
    
    def load_handwriting_fonts(self) -> List[str]:
        """Load available handwriting-style fonts"""
        handwriting_fonts = []
        
        # Common handwriting fonts that might be available
        font_names = [
            "Comic Sans MS",
            "Brush Script MT",
            "Lucida Handwriting",
            "Segoe Print",
            "Bradley Hand ITC",
            "Kristen ITC",
            "Tempus Sans ITC"
        ]
        
        # Try to load system fonts
        for font_name in font_names:
            try:
                # This is a placeholder - in real implementation, you'd check system fonts
                handwriting_fonts.append(font_name)
            except:
                continue
        
        # Fallback to default if no handwriting fonts found
        if not handwriting_fonts:
            handwriting_fonts = ["DejaVu Sans"]
        
        return handwriting_fonts
    
    async def solve_doubt(self, image_path: str) -> Optional[str]:
        """Main method to solve doubt in image"""
        try:
            # Load and preprocess image
            image = self.load_and_preprocess_image(image_path)
            if image is None:
                return None
            
            # Extract text from image
            extracted_text = self.extract_text_from_image(image)
            
            if not extracted_text.strip():
                logger.warning(f"No text extracted from image: {image_path}")
                return None
            
            # Analyze the problem and get solution
            solution_data = await self.analyze_and_solve(extracted_text)
            
            if not solution_data:
                return None
            
            # Create solved image with handwritten solution
            solved_image_path = await self.create_solved_image(
                image_path, 
                solution_data,
                extracted_text
            )
            
            return solved_image_path
            
        except Exception as e:
            logger.error(f"Error solving doubt in image {image_path}: {e}")
            return None
    
    def load_and_preprocess_image(self, image_path: str) -> Optional[np.ndarray]:
        """Load and preprocess image for better OCR"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            # Resize if too large
            height, width = image.shape[:2]
            if width > MAX_IMAGE_SIZE[0] or height > MAX_IMAGE_SIZE[1]:
                scale = min(MAX_IMAGE_SIZE[0]/width, MAX_IMAGE_SIZE[1]/height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height))
            
            # Enhance image for better OCR
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Enhance contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # Convert back to BGR for consistency
            processed = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            
            return processed
            
        except Exception as e:
            logger.error(f"Error preprocessing image {image_path}: {e}")
            return None
    
    def extract_text_from_image(self, image: np.ndarray) -> str:
        """Extract text from image using OCR"""
        extracted_text = ""
        
        try:
            # Method 2: Tesseract (primary or fallback if EasyOCR not available)
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            tesseract_text = pytesseract.image_to_string(pil_image, lang=\'eng+hin\')
            
            if tesseract_text.strip():
                extracted_text = tesseract_text
                logger.info(f"Tesseract extracted text: {extracted_text[:100]}...")
            else:
                logger.warning("Tesseract extracted no text.")

            # Method 1: EasyOCR (better for handwritten text) - if available and Tesseract failed
            if EASYOCR_AVAILABLE and self.ocr_reader and not extracted_text.strip():
                results = self.ocr_reader.readtext(image)
                easyocr_text = " ".join([result[1] for result in results if result[2] > 0.5])
                
                if easyocr_text.strip():
                    extracted_text = easyocr_text
                    logger.info(f"EasyOCR extracted text: {easyocr_text[:100]}...")
                else:
                    logger.warning("EasyOCR extracted no text.")
            
            # Clean extracted text
            extracted_text = self.clean_extracted_text(extracted_text)
            
            logger.info(f"Extracted text: {extracted_text[:100]}...")
            return extracted_text
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""
