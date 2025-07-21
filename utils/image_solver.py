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
import easyocr
from openai import OpenAI

from config.settings import MAX_IMAGE_SIZE, SOLUTION_FONT_SIZE, SOLUTION_COLOR, OPENAI_API_KEY

logger = logging.getLogger(__name__)

class ImageSolver:
    def __init__(self):
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        self.ocr_reader = easyocr.Reader(['en', 'hi'])  # English and Hindi
        
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
            # Method 1: EasyOCR (better for handwritten text)
            results = self.ocr_reader.readtext(image)
            easyocr_text = " ".join([result[1] for result in results if result[2] > 0.5])
            
            if easyocr_text.strip():
                extracted_text = easyocr_text
            
            # Method 2: Tesseract (fallback)
            if not extracted_text.strip():
                # Convert to PIL Image for Tesseract
                pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                tesseract_text = pytesseract.image_to_string(pil_image, lang='eng+hin')
                
                if tesseract_text.strip():
                    extracted_text = tesseract_text
            
            # Clean extracted text
            extracted_text = self.clean_extracted_text(extracted_text)
            
            logger.info(f"Extracted text: {extracted_text[:100]}...")
            return extracted_text
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""
    
    def clean_extracted_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors
        replacements = {
            '0': 'O',  # Sometimes 0 is confused with O
            'l': '1',  # Sometimes l is confused with 1
            'S': '5',  # Sometimes S is confused with 5
        }
        
        # Apply replacements cautiously (only in mathematical contexts)
        if any(char in text for char in '+-*/=()[]{}'):
            for old, new in replacements.items():
                # Only replace if surrounded by numbers or operators
                text = re.sub(f'(?<=[0-9+\\-*/=()\\[\\]{{}}]){old}(?=[0-9+\\-*/=()\\[\\]{{}}])', new, text)
        
        return text.strip()
    
    async def analyze_and_solve(self, problem_text: str) -> Optional[Dict]:
        """Analyze problem and get solution using AI"""
        try:
            prompt = f"""
You are a helpful tutor solving a student's doubt. The problem text extracted from an image is:

"{problem_text}"

Please:
1. Identify what type of problem this is (math, physics, chemistry, etc.)
2. Provide a step-by-step solution in Hindi-English mixed style (Hinglish)
3. Keep the solution concise but complete
4. Use simple language suitable for students
5. If it's a math problem, show calculations clearly

Format your response as JSON:
{{
    "problem_type": "math/physics/chemistry/other",
    "solution_steps": [
        "Step 1: ...",
        "Step 2: ...",
        "Step 3: ..."
    ],
    "final_answer": "Final answer here",
    "explanation": "Brief explanation in Hinglish"
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert tutor who explains problems in Hindi-English mixed style (Hinglish) for Indian students."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            try:
                solution_data = json.loads(response_text)
                return solution_data
            except json.JSONDecodeError:
                # Fallback parsing
                return self.parse_solution_manually(response_text)
            
        except Exception as e:
            logger.error(f"Error analyzing problem: {e}")
            return None
    
    def parse_solution_manually(self, response_text: str) -> Dict:
        """Manually parse solution if JSON parsing fails"""
        try:
            # Extract solution steps
            import re
            steps = re.findall(r'Step \d+:(.+?)(?=Step \d+:|Final|$)', response_text, re.DOTALL)
            steps = [step.strip() for step in steps if step.strip()]
            
            # Extract final answer
            final_answer_match = re.search(r'(?:Final answer|Answer)[:\s]*(.+?)(?:\n|$)', response_text, re.IGNORECASE)
            final_answer = final_answer_match.group(1).strip() if final_answer_match else ""
            
            return {
                "problem_type": "general",
                "solution_steps": steps,
                "final_answer": final_answer,
                "explanation": "Solution provided step by step"
            }
            
        except Exception as e:
            logger.error(f"Error in manual parsing: {e}")
            return {
                "problem_type": "general",
                "solution_steps": ["Solution analysis in progress..."],
                "final_answer": "Please check the problem again",
                "explanation": "Unable to parse solution"
            }
    
    async def create_solved_image(self, original_image_path: str, solution_data: Dict, problem_text: str) -> str:
        """Create image with handwritten-style solution overlay"""
        try:
            # Load original image
            original_image = Image.open(original_image_path)
            
            # Create a copy for drawing
            solved_image = original_image.copy()
            draw = ImageDraw.Draw(solved_image)
            
            # Get image dimensions
            img_width, img_height = solved_image.size
            
            # Choose random handwriting style
            pen_color = random.choice(self.pen_colors)
            
            # Find suitable area for solution (usually bottom or right side)
            solution_area = self.find_solution_area(solved_image, problem_text)
            
            # Draw solution with handwriting effect
            self.draw_handwritten_solution(
                draw, 
                solution_data, 
                solution_area, 
                pen_color,
                img_width,
                img_height
            )
            
            # Add some handwriting imperfections for realism
            solved_image = self.add_handwriting_effects(solved_image)
            
            # Save solved image
            output_path = original_image_path.replace('.', '_solved.')
            solved_image.save(output_path, quality=95)
            
            logger.info(f"Created solved image: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating solved image: {e}")
            return None
    
    def find_solution_area(self, image: Image.Image, problem_text: str) -> Dict:
        """Find suitable area to write solution"""
        img_width, img_height = image.size
        
        # Convert to numpy array for analysis
        img_array = np.array(image)
        
        # Find areas with less content (more white space)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Divide image into regions and find the one with most white space
        regions = [
            {'name': 'bottom', 'area': (0, img_height//2, img_width, img_height)},
            {'name': 'right', 'area': (img_width//2, 0, img_width, img_height)},
            {'name': 'top_right', 'area': (img_width//2, 0, img_width, img_height//2)},
            {'name': 'bottom_left', 'area': (0, img_height//2, img_width//2, img_height)}
        ]
        
        best_region = regions[0]  # Default to bottom
        max_white_space = 0
        
        for region in regions:
            x1, y1, x2, y2 = region['area']
            region_gray = gray[y1:y2, x1:x2]
            white_pixels = np.sum(region_gray > 200)  # Count white-ish pixels
            
            if white_pixels > max_white_space:
                max_white_space = white_pixels
                best_region = region
        
        return {
            'area': best_region['area'],
            'name': best_region['name']
        }
    
    def draw_handwritten_solution(self, draw: ImageDraw.Draw, solution_data: Dict, 
                                solution_area: Dict, pen_color: Tuple, 
                                img_width: int, img_height: int):
        """Draw solution with handwriting-like appearance"""
        try:
            x1, y1, x2, y2 = solution_area['area']
            
            # Calculate available space
            available_width = x2 - x1 - 20  # 20px margin
            available_height = y2 - y1 - 20
            
            # Font size based on available space
            font_size = min(24, available_width // 25, available_height // 15)
            
            # Try to load a handwriting-like font
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Starting position
            current_y = y1 + 10
            line_height = font_size + 5
            
            # Draw solution title
            title_text = "✓ Solution:"
            draw.text((x1 + 10, current_y), title_text, fill=pen_color, font=font)
            current_y += line_height + 5
            
            # Draw solution steps
            steps = solution_data.get('solution_steps', [])
            for i, step in enumerate(steps[:4]):  # Limit to 4 steps to fit
                if current_y + line_height > y2 - 10:
                    break
                
                # Add slight randomness to make it look handwritten
                x_offset = random.randint(-2, 2)
                y_offset = random.randint(-1, 1)
                
                step_text = f"{i+1}. {step[:60]}..."  # Truncate long steps
                
                # Word wrap for long text
                words = step_text.split()
                current_line = ""
                
                for word in words:
                    test_line = current_line + word + " "
                    # Rough text width estimation
                    if len(test_line) * (font_size * 0.6) > available_width:
                        if current_line:
                            draw.text((x1 + 10 + x_offset, current_y + y_offset), 
                                    current_line.strip(), fill=pen_color, font=font)
                            current_y += line_height
                            current_line = word + " "
                        else:
                            current_line = test_line
                    else:
                        current_line = test_line
                
                if current_line and current_y + line_height <= y2 - 10:
                    draw.text((x1 + 10 + x_offset, current_y + y_offset), 
                            current_line.strip(), fill=pen_color, font=font)
                    current_y += line_height
            
            # Draw final answer if space available
            final_answer = solution_data.get('final_answer', '')
            if final_answer and current_y + line_height * 2 <= y2 - 10:
                current_y += 5
                answer_text = f"Answer: {final_answer}"
                
                # Highlight the answer
                highlight_color = (255, 255, 0, 100)  # Yellow highlight
                bbox = draw.textbbox((x1 + 10, current_y), answer_text, font=font)
                draw.rectangle(bbox, fill=highlight_color)
                
                draw.text((x1 + 10, current_y), answer_text, fill=(0, 0, 0), font=font)
            
        except Exception as e:
            logger.error(f"Error drawing handwritten solution: {e}")
    
    def add_handwriting_effects(self, image: Image.Image) -> Image.Image:
        """Add subtle effects to make solution look more handwritten"""
        try:
            # Add very slight blur to simulate pen ink
            blurred = image.filter(ImageFilter.GaussianBlur(radius=0.3))
            
            # Blend original with blurred for subtle effect
            result = Image.blend(image, blurred, alpha=0.1)
            
            # Add very slight noise for paper texture
            enhancer = ImageEnhance.Contrast(result)
            result = enhancer.enhance(1.02)
            
            return result
            
        except Exception as e:
            logger.error(f"Error adding handwriting effects: {e}")
            return image
    
    def detect_problem_type(self, text: str) -> str:
        """Detect the type of problem from text"""
        text_lower = text.lower()
        
        # Math indicators
        math_keywords = ['solve', 'find', 'calculate', 'equation', 'integral', 'derivative', 
                        'limit', 'sum', 'product', '+', '-', '*', '/', '=', 'x', 'y']
        
        # Physics indicators
        physics_keywords = ['force', 'velocity', 'acceleration', 'mass', 'energy', 'power',
                           'momentum', 'friction', 'gravity', 'motion', 'wave', 'frequency']
        
        # Chemistry indicators
        chemistry_keywords = ['reaction', 'molecule', 'atom', 'bond', 'acid', 'base',
                             'ph', 'molarity', 'element', 'compound', 'ion']
        
        math_score = sum(1 for keyword in math_keywords if keyword in text_lower)
        physics_score = sum(1 for keyword in physics_keywords if keyword in text_lower)
        chemistry_score = sum(1 for keyword in chemistry_keywords if keyword in text_lower)
        
        if math_score >= physics_score and math_score >= chemistry_score:
            return 'math'
        elif physics_score >= chemistry_score:
            return 'physics'
        elif chemistry_score > 0:
            return 'chemistry'
        else:
            return 'general'
    
    def get_solution_template(self, problem_type: str) -> Dict:
        """Get solution template based on problem type"""
        templates = {
            'math': {
                'steps': ['Given information ko identify karo', 'Formula apply karo', 'Calculate karo'],
                'format': 'mathematical'
            },
            'physics': {
                'steps': ['Given values note karo', 'Appropriate formula choose karo', 'Substitute and solve karo'],
                'format': 'scientific'
            },
            'chemistry': {
                'steps': ['Reaction identify karo', 'Balanced equation likho', 'Calculate karo'],
                'format': 'chemical'
            },
            'general': {
                'steps': ['Problem analyze karo', 'Solution approach decide karo', 'Step by step solve karo'],
                'format': 'general'
            }
        }
        
        return templates.get(problem_type, templates['general'])
    
    def validate_solution(self, solution_data: Dict) -> bool:
        """Validate solution data"""
        required_fields = ['problem_type', 'solution_steps', 'final_answer']
        
        if not all(field in solution_data for field in required_fields):
            return False
        
        if not solution_data['solution_steps'] or not solution_data['final_answer']:
            return False
        
        return True

