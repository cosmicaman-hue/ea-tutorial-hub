"""
AI Integration Module for Quiz Generation
Supports OpenAI, Google Gemini, and Anthropic Claude
"""

import os
import json
from typing import List, Dict, Optional
import requests

class AIQuizGenerator:
    """Generate quizzes using multiple AI providers"""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.gemini_api_key = os.getenv('GOOGLE_API_KEY')
        self.claude_api_key = os.getenv('ANTHROPIC_API_KEY')
    
    def generate_with_openai(self, document_content: str, num_questions: int = 10, difficulty: str = 'medium') -> Dict:
        """Generate quiz using OpenAI GPT"""
        if not self.openai_api_key:
            return {'error': 'OpenAI API key not configured'}
        
        try:
            import openai
            openai.api_key = self.openai_api_key
            
            prompt = f"""Based on the following document, generate {num_questions} multiple choice quiz questions with difficulty level {difficulty}.

Document Content:
{document_content[:3000]}

Return ONLY valid JSON in this format:
{{
    "quiz_title": "Quiz Title",
    "description": "Brief description",
    "questions": [
        {{
            "question_text": "Question?",
            "question_type": "multiple_choice",
            "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
            "correct_answer": "A",
            "explanation": "Why this is correct"
        }}
    ]
}}"""
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=3000
            )
            
            quiz_json = response.choices[0].message.content
            return json.loads(quiz_json)
        
        except Exception as e:
            return {'error': f'OpenAI Error: {str(e)}'}
    
    def generate_with_gemini(self, document_content: str, num_questions: int = 10, difficulty: str = 'medium') -> Dict:
        """Generate quiz using Google Gemini"""
        if not self.gemini_api_key:
            return {'error': 'Google Gemini API key not configured'}
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)
            
            prompt = f"""Based on the following document, generate {num_questions} multiple choice quiz questions with difficulty level {difficulty}.

Document Content:
{document_content[:3000]}

Return ONLY valid JSON in this format:
{{
    "quiz_title": "Quiz Title",
    "description": "Brief description",
    "questions": [
        {{
            "question_text": "Question?",
            "question_type": "multiple_choice",
            "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
            "correct_answer": "A",
            "explanation": "Why this is correct"
        }}
    ]
}}"""
            
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            
            quiz_json = response.text
            return json.loads(quiz_json)
        
        except Exception as e:
            return {'error': f'Gemini Error: {str(e)}'}
    
    def generate_with_claude(self, document_content: str, num_questions: int = 10, difficulty: str = 'medium') -> Dict:
        """Generate quiz using Anthropic Claude"""
        if not self.claude_api_key:
            return {'error': 'Claude API key not configured'}
        
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.claude_api_key)
            
            prompt = f"""Based on the following document, generate {num_questions} multiple choice quiz questions with difficulty level {difficulty}.

Document Content:
{document_content[:3000]}

Return ONLY valid JSON in this format:
{{
    "quiz_title": "Quiz Title",
    "description": "Brief description",
    "questions": [
        {{
            "question_text": "Question?",
            "question_type": "multiple_choice",
            "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
            "correct_answer": "A",
            "explanation": "Why this is correct"
        }}
    ]
}}"""
            
            message = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=3000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            quiz_json = message.content[0].text
            return json.loads(quiz_json)
        
        except Exception as e:
            return {'error': f'Claude Error: {str(e)}'}
    
    def generate_quiz(self, document_content: str, num_questions: int = 10, 
                     difficulty: str = 'medium', ai_provider: str = 'openai') -> Dict:
        """
        Main method to generate quiz with specified AI provider
        
        Args:
            document_content: Text from uploaded document
            num_questions: Number of questions (max 50)
            difficulty: 'easy', 'medium', or 'hard'
            ai_provider: 'openai', 'gemini', or 'claude'
        
        Returns:
            Dictionary with quiz data or error
        """
        # Validate inputs
        if num_questions > 50:
            num_questions = 50
        if num_questions < 1:
            num_questions = 1
        
        if difficulty not in ['easy', 'medium', 'hard']:
            difficulty = 'medium'
        
        if not document_content or len(document_content.strip()) < 100:
            return {'error': 'Document must contain at least 100 characters'}
        
        # Route to appropriate AI provider
        if ai_provider.lower() == 'gemini':
            return self.generate_with_gemini(document_content, num_questions, difficulty)
        elif ai_provider.lower() == 'claude':
            return self.generate_with_claude(document_content, num_questions, difficulty)
        else:  # Default to OpenAI
            return self.generate_with_openai(document_content, num_questions, difficulty)
