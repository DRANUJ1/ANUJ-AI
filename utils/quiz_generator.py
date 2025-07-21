"""
Quiz Generator for Anuj Bot
Generates quizzes from PDF content using AI
"""

import os
import re
import logging
import random
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import PyPDF2
import pdfplumber
from openai import OpenAI
import nltk
from textblob import TextBlob

from config.settings import MAX_QUIZ_QUESTIONS, OPENAI_API_KEY
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class QuizGenerator:
    def __init__(self):
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        self.db_manager = DatabaseManager()
        
        # Download required NLTK data
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
        except:
            pass
    
    async def generate_from_pdf(self, pdf_path: str, user_id: int = None) -> Dict:
        """Generate quiz from PDF content"""
        try:
            # Extract text from PDF
            text_content = self.extract_text_from_pdf(pdf_path)
            
            if not text_content or len(text_content.strip()) < 100:
                logger.warning(f"Insufficient text content in PDF: {pdf_path}")
                return {'success': False, 'error': 'PDF contains insufficient readable text'}
            
            # Generate quiz questions
            questions = await self.generate_questions_from_text(text_content)
            
            if not questions:
                return {'success': False, 'error': 'Could not generate questions from content'}
            
            # Store quiz in database if user_id provided
            quiz_id = None
            if user_id:
                quiz_title = f"Quiz from {Path(pdf_path).stem}"
                quiz_id = self.db_manager.add_quiz(
                    user_id=user_id,
                    title=quiz_title,
                    questions=questions,
                    source_file=pdf_path
                )
            
            return {
                'success': True,
                'quiz_id': quiz_id,
                'questions': questions,
                'total_questions': len(questions),
                'source_file': pdf_path
            }
            
        except Exception as e:
            logger.error(f"Error generating quiz from PDF {pdf_path}: {e}")
            return {'success': False, 'error': str(e)}
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using multiple methods"""
        text_content = ""
        
        # Method 1: Try pdfplumber first (better for complex layouts)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
        except Exception as e:
            logger.warning(f"pdfplumber failed for {pdf_path}: {e}")
        
        # Method 2: Fallback to PyPDF2 if pdfplumber fails
        if not text_content.strip():
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_content += page_text + "\n"
            except Exception as e:
                logger.warning(f"PyPDF2 failed for {pdf_path}: {e}")
        
        # Clean and normalize text
        text_content = self.clean_text(text_content)
        
        logger.info(f"Extracted {len(text_content)} characters from {pdf_path}")
        return text_content
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers patterns
        text = re.sub(r'\n\d+\n', '\n', text)
        text = re.sub(r'\nPage \d+\n', '\n', text)
        
        # Fix common OCR errors
        text = text.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
        
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    async def generate_questions_from_text(self, text: str, num_questions: int = None) -> List[Dict]:
        """Generate quiz questions from text using AI"""
        if not num_questions:
            num_questions = min(MAX_QUIZ_QUESTIONS, max(3, len(text) // 500))
        
        try:
            # Split text into chunks for processing
            chunks = self.split_text_into_chunks(text, max_chunk_size=3000)
            all_questions = []
            
            for i, chunk in enumerate(chunks[:3]):  # Process max 3 chunks
                chunk_questions = await self.generate_questions_from_chunk(chunk, num_questions // len(chunks[:3]) + 1)
                all_questions.extend(chunk_questions)
            
            # Limit to requested number of questions
            if len(all_questions) > num_questions:
                all_questions = random.sample(all_questions, num_questions)
            
            return all_questions
            
        except Exception as e:
            logger.error(f"Error generating questions from text: {e}")
            return []
    
    def split_text_into_chunks(self, text: str, max_chunk_size: int = 3000) -> List[str]:
        """Split text into manageable chunks"""
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) < max_chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def generate_questions_from_chunk(self, text_chunk: str, num_questions: int = 3) -> List[Dict]:
        """Generate questions from a text chunk using OpenAI"""
        try:
            prompt = f"""
Based on the following text, generate {num_questions} multiple choice questions. Each question should:
1. Test understanding of key concepts
2. Have 4 options (A, B, C, D)
3. Have exactly one correct answer
4. Be clear and unambiguous
5. Be in Hindi-English mixed style (Hinglish) suitable for Indian students

Text:
{text_chunk}

Format your response as JSON with this structure:
[
  {{
    "question": "Question text in Hinglish",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "A",
    "explanation": "Brief explanation in Hinglish"
  }}
]
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert quiz generator for Indian students. Generate questions in Hindi-English mixed style (Hinglish)."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            import json
            try:
                questions_data = json.loads(response_text)
                
                # Validate and format questions
                formatted_questions = []
                for q_data in questions_data:
                    if self.validate_question(q_data):
                        formatted_questions.append({
                            'question': q_data['question'],
                            'options': q_data['options'],
                            'answer': q_data['correct_answer'],
                            'explanation': q_data.get('explanation', ''),
                            'difficulty': 'medium',
                            'type': 'multiple_choice'
                        })
                
                return formatted_questions
                
            except json.JSONDecodeError:
                # Fallback: parse manually if JSON parsing fails
                return self.parse_questions_manually(response_text)
            
        except Exception as e:
            logger.error(f"Error generating questions from chunk: {e}")
            return []
    
    def validate_question(self, question_data: Dict) -> bool:
        """Validate question format"""
        required_fields = ['question', 'options', 'correct_answer']
        
        if not all(field in question_data for field in required_fields):
            return False
        
        if len(question_data['options']) != 4:
            return False
        
        if question_data['correct_answer'] not in ['A', 'B', 'C', 'D']:
            return False
        
        return True
    
    def parse_questions_manually(self, response_text: str) -> List[Dict]:
        """Manually parse questions if JSON parsing fails"""
        questions = []
        
        # Simple regex-based parsing as fallback
        question_pattern = r'(?:Question|Q\d+)[:\.]?\s*(.+?)(?=Options?|A\.|1\.)'
        options_pattern = r'[ABCD1-4][\.\)]\s*(.+?)(?=[ABCD1-4][\.\)]|Answer|Correct)'
        answer_pattern = r'(?:Answer|Correct)[:\s]*([ABCD])'
        
        try:
            question_matches = re.findall(question_pattern, response_text, re.IGNORECASE | re.DOTALL)
            
            for i, question_text in enumerate(question_matches):
                # Extract options for this question
                question_section = response_text[response_text.find(question_text):response_text.find(question_text) + 500]
                option_matches = re.findall(options_pattern, question_section, re.IGNORECASE)
                answer_match = re.search(answer_pattern, question_section, re.IGNORECASE)
                
                if len(option_matches) >= 4 and answer_match:
                    questions.append({
                        'question': question_text.strip(),
                        'options': option_matches[:4],
                        'answer': answer_match.group(1).upper(),
                        'explanation': '',
                        'difficulty': 'medium',
                        'type': 'multiple_choice'
                    })
        
        except Exception as e:
            logger.error(f"Error in manual parsing: {e}")
        
        return questions
    
    def generate_simple_questions(self, text: str, num_questions: int = 5) -> List[Dict]:
        """Generate simple questions without AI (fallback method)"""
        questions = []
        
        try:
            # Extract sentences
            blob = TextBlob(text)
            sentences = [str(sentence) for sentence in blob.sentences if len(str(sentence)) > 20]
            
            if len(sentences) < num_questions:
                num_questions = len(sentences)
            
            selected_sentences = random.sample(sentences, min(num_questions, len(sentences)))
            
            for i, sentence in enumerate(selected_sentences):
                # Create fill-in-the-blank questions
                words = sentence.split()
                if len(words) > 5:
                    # Remove a key word (not articles, prepositions)
                    key_words = [w for w in words if len(w) > 3 and w.lower() not in ['the', 'and', 'for', 'are', 'but']]
                    
                    if key_words:
                        target_word = random.choice(key_words)
                        question_text = sentence.replace(target_word, "______")
                        
                        # Generate options
                        options = [target_word]
                        # Add some random words as distractors
                        other_words = [w for w in key_words if w != target_word]
                        options.extend(random.sample(other_words, min(3, len(other_words))))
                        
                        # Pad with generic options if needed
                        while len(options) < 4:
                            options.append(f"Option {len(options) + 1}")
                        
                        random.shuffle(options)
                        correct_index = options.index(target_word)
                        
                        questions.append({
                            'question': f"Fill in the blank: {question_text}",
                            'options': options,
                            'answer': chr(65 + correct_index),  # A, B, C, D
                            'explanation': f"The correct word is '{target_word}'",
                            'difficulty': 'easy',
                            'type': 'fill_blank'
                        })
            
        except Exception as e:
            logger.error(f"Error generating simple questions: {e}")
        
        return questions
    
    def get_quiz_by_id(self, quiz_id: int) -> Optional[Dict]:
        """Get quiz by ID from database"""
        try:
            import sqlite3
            with self.db_manager.lock:
                conn = sqlite3.connect(self.db_manager.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, user_id, title, questions, created_at, 
                           total_questions, source_file, difficulty, subject
                    FROM quizzes WHERE id = ?
                ''', (quiz_id,))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    import json
                    return {
                        'id': row[0],
                        'user_id': row[1],
                        'title': row[2],
                        'questions': json.loads(row[3]),
                        'created_at': row[4],
                        'total_questions': row[5],
                        'source_file': row[6],
                        'difficulty': row[7],
                        'subject': row[8]
                    }
                
        except Exception as e:
            logger.error(f"Error getting quiz {quiz_id}: {e}")
        
        return None
    
    def get_user_quizzes(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's quizzes"""
        try:
            import sqlite3
            with self.db_manager.lock:
                conn = sqlite3.connect(self.db_manager.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, title, created_at, total_questions, difficulty, subject
                    FROM quizzes 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (user_id, limit))
                
                rows = cursor.fetchall()
                conn.close()
                
                quizzes = []
                for row in rows:
                    quizzes.append({
                        'id': row[0],
                        'title': row[1],
                        'created_at': row[2],
                        'total_questions': row[3],
                        'difficulty': row[4],
                        'subject': row[5]
                    })
                
                return quizzes
                
        except Exception as e:
            logger.error(f"Error getting quizzes for user {user_id}: {e}")
            return []
    
    def format_quiz_for_display(self, quiz_data: Dict) -> str:
        """Format quiz for display in Telegram"""
        if not quiz_data or not quiz_data.get('questions'):
            return "❌ Quiz data not available"
        
        quiz_text = f"🧠 **{quiz_data.get('title', 'Quiz')}**\n\n"
        
        questions = quiz_data['questions']
        for i, question in enumerate(questions, 1):
            quiz_text += f"**Q{i}.** {question['question']}\n\n"
            
            for j, option in enumerate(question['options']):
                letter = chr(65 + j)  # A, B, C, D
                quiz_text += f"{letter}. {option}\n"
            
            quiz_text += f"\n**Answer:** {question['answer']}\n"
            
            if question.get('explanation'):
                quiz_text += f"**Explanation:** {question['explanation']}\n"
            
            quiz_text += "\n" + "─" * 30 + "\n\n"
        
        return quiz_text
    
    async def generate_quiz_variations(self, original_quiz_id: int, num_variations: int = 3) -> List[Dict]:
        """Generate variations of an existing quiz"""
        try:
            original_quiz = self.get_quiz_by_id(original_quiz_id)
            if not original_quiz:
                return []
            
            variations = []
            for i in range(num_variations):
                # Shuffle options and adjust questions slightly
                varied_questions = []
                for question in original_quiz['questions']:
                    varied_question = question.copy()
                    
                    # Shuffle options
                    options = question['options'].copy()
                    correct_answer_text = options[ord(question['answer']) - 65]
                    random.shuffle(options)
                    new_correct_index = options.index(correct_answer_text)
                    varied_question['answer'] = chr(65 + new_correct_index)
                    varied_question['options'] = options
                    
                    varied_questions.append(varied_question)
                
                # Shuffle question order
                random.shuffle(varied_questions)
                
                variations.append({
                    'title': f"{original_quiz['title']} - Variation {i+1}",
                    'questions': varied_questions,
                    'total_questions': len(varied_questions),
                    'difficulty': original_quiz['difficulty'],
                    'subject': original_quiz['subject']
                })
            
            return variations
            
        except Exception as e:
            logger.error(f"Error generating quiz variations: {e}")
            return []

