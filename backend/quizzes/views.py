from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Quiz, Question, QuestionOption, QuizAttempt, QuizStatistics
from .serializers import QuizSerializer, QuestionSerializer, QuizStatisticsSerializer
from .utils.pdf_extractor import PDFExtractor
from .utils.image_extractor import ImageExtractor
from .utils.quiz_generator import QuizGenerator
import pytesseract
import json
import random

# Configure tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def landing_page(request):
    return render(request, 'quiz_app/landing.html')

def upload_page(request):
    return render(request, 'quiz_app/upload.html')

@csrf_exempt
def process_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        file_type = uploaded_file.content_type
        
        try:
            # Save file temporarily
            file_path = default_storage.save(f'temp/{uploaded_file.name}', uploaded_file)
            full_path = default_storage.path(file_path)
            
            # Extract text based on file type
            if 'pdf' in file_type:
                pdf_extractor = PDFExtractor()
                text = pdf_extractor.extract_from_file_path(full_path)
            elif 'image' in file_type:
                img_extractor = ImageExtractor()
                text = img_extractor.extract_from_file_path(full_path)
            else:
                return JsonResponse({'error': 'Unsupported file type'}, status=400)
            
            # Generate quiz questions
            quiz_generator = QuizGenerator(num_questions=5)
            questions_data = quiz_generator.generate_quiz(text)
            
            # Create quiz in database
            quiz = Quiz.objects.create(
                title=f"Quiz from {uploaded_file.name}",
                extracted_text=text,
                user=request.user if request.user.is_authenticated else None
            )
            
            # Create questions and options
            for idx, q_data in enumerate(questions_data):
                question = Question.objects.create(
                    quiz=quiz,
                    question_text=q_data['question'],
                    correct_answer=q_data['correctAnswer'],
                    order=idx
                )
                
                for opt_idx, option in enumerate(q_data['options']):
                    QuestionOption.objects.create(
                        question=question,
                        option_text=option,
                        option_order=opt_idx
                    )
            
            # Clean up temp file
            default_storage.delete(file_path)
            
            return JsonResponse({
                'quiz_id': quiz.id,
                'redirect_url': f'/quiz/{quiz.id}/'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def quiz_page(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()
    
    questions_data = []
    for question in questions:
        options = [opt.option_text for opt in question.options.all()]
        questions_data.append({
            'id': question.id,
            'question': question.question_text,
            'options': options,
            'correctAnswer': question.correct_answer
        })
    
    context = {
        'quiz': quiz,
        'questions_json': json.dumps(questions_data),
        'extracted_text': quiz.extracted_text
    }
    return render(request, 'quiz_app/quiz.html', context)

@csrf_exempt
def submit_quiz(request, quiz_id):
    if request.method == 'POST':
        quiz = get_object_or_404(Quiz, id=quiz_id)
        data = json.loads(request.body)
        answers = data.get('answers', {})
        
        # Calculate score
        score = 0
        questions = quiz.questions.all()
        for question in questions:
            if str(question.id) in answers:
                if answers[str(question.id)] == question.correct_answer:
                    score += 1
        
        total_questions = questions.count()
        percentage = round((score / total_questions) * 100, 2) if total_questions > 0 else 0
        
        # Save attempt
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=request.user if request.user.is_authenticated else None,
            score=score,
            total_questions=total_questions,
            answers=answers
        )
        
        # Save statistics if user is authenticated
        if request.user.is_authenticated:
            QuizStatistics.objects.create(
                user=request.user,
                quiz=quiz,
                correct_answers=score,
                total_questions=total_questions,
                score=percentage
            )
        
        return JsonResponse({
            'score': score,
            'total': total_questions,
            'percentage': attempt.get_percentage()
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# REST API Views for frontend integration
class QuizListCreateView(generics.ListCreateAPIView):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class QuizDetailView(generics.RetrieveAPIView):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]
    queryset = Quiz.objects.all()


class QuizSubmitView(APIView):
    """API endpoint for submitting quiz results"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            quiz = get_object_or_404(Quiz, id=pk)
            data = request.data
            
            score = data.get('score', 0)
            total_questions = data.get('total_questions', 0)
            answers = data.get('answers', {})
            
            # Calculate percentage
            percentage = round((score / total_questions) * 100, 2) if total_questions > 0 else 0
            
            # Save to QuizAttempt
            QuizAttempt.objects.create(
                quiz=quiz,
                user=request.user,
                score=score,
                total_questions=total_questions,
                answers=answers
            )
            
            # Save to QuizStatistics
            QuizStatistics.objects.create(
                user=request.user,
                quiz=quiz,
                correct_answers=score,
                total_questions=total_questions,
                score=percentage
            )
            
            return Response({
                'status': 'success',
                'score': score,
                'total': total_questions,
                'percentage': percentage
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class QuestionCreateView(generics.CreateAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]


class FileUploadView(APIView):
    """REST API endpoint for file upload (used by frontend)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        print(f"DEBUG: FileUploadView.post() called")
        print(f"DEBUG: request.FILES keys: {request.FILES.keys()}")
        print(f"DEBUG: request.POST keys: {request.POST.keys()}")
        try:
            if not request.user or not request.user.is_authenticated:
                return Response({'detail': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

            if 'file' not in request.FILES:
                print(f"DEBUG: No file in request.FILES")
                return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
            
            uploaded_file = request.FILES['file']
            allowed_types = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
            
            if uploaded_file.content_type not in allowed_types:
                return Response({'error': f'Invalid file type: {uploaded_file.content_type}. Please upload PDF or image.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if uploaded_file.size > 16 * 1024 * 1024:
                return Response({'error': 'File size must be less than 16MB'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get parameters from request
            num_questions = request.POST.get('num_questions', 5)
            try:
                num_questions = int(num_questions)
                if num_questions < 3 or num_questions > 20:
                    num_questions = 5
            except (ValueError, TypeError):
                num_questions = 5
            
            ai_notes = request.POST.get('ai_notes', '')
            custom_title = request.POST.get('custom_title', '')
            question_type = request.POST.get('question_type', 'multiple_choice')
            question_mix_raw = request.POST.get('question_mix')

            # Determine question mix
            question_mix = {}
            if question_mix_raw:
                try:
                    import json
                    parsed = json.loads(question_mix_raw)
                    if not isinstance(parsed, dict):
                        return Response({'error': 'question_mix must be a JSON object'}, status=status.HTTP_400_BAD_REQUEST)
                    for key, val in parsed.items():
                        try:
                            count = int(val)
                        except (ValueError, TypeError):
                            count = 0
                        if count < 0:
                            count = 0
                        if count > 0:
                            question_mix[str(key)] = count
                    total_from_mix = sum(question_mix.values())
                    if total_from_mix <= 0:
                        return Response({'error': 'Total number of questions must be greater than 0'}, status=status.HTTP_400_BAD_REQUEST)
                    if total_from_mix > 20:
                        return Response({'error': 'Total number of questions must not exceed 20'}, status=status.HTTP_400_BAD_REQUEST)
                    num_questions = total_from_mix
                except Exception:
                    return Response({'error': 'Invalid question_mix format'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Fallback: single type with num_questions
                question_mix = {question_type: num_questions}
            
            # Save file temporarily
            file_path = default_storage.save(f'temp/{uploaded_file.name}', uploaded_file)
            full_path = default_storage.path(file_path)
            
            try:
                # Extract text
                if 'pdf' in uploaded_file.content_type:
                    extractor = PDFExtractor()
                    text = extractor.extract_from_file_path(full_path)
                else:
                    extractor = ImageExtractor()
                    text = extractor.extract_from_file_path(full_path)
                
                if not text or len(text.strip()) < 20:
                    return Response({'error': 'Could not extract text from file. Please ensure the file contains readable text.'}, status=status.HTTP_400_BAD_REQUEST)
                
                # Generate questions with user-specified mix and AI notes
                questions_data = []
                for qt, count in question_mix.items():
                    if count <= 0:
                        continue
                    generator = QuizGenerator(num_questions=count)
                    generated = generator.generate_quiz(text, ai_notes=ai_notes, question_type=qt)
                    questions_data.extend(generated)

                if not questions_data:
                    return Response({'error': 'Could not generate questions from the extracted text.'}, status=status.HTTP_400_BAD_REQUEST)

                # Randomize question order across types
                random.shuffle(questions_data)
                
                # Create quiz with custom title if provided
                quiz_title = custom_title if custom_title.strip() else f"Quiz from {uploaded_file.name}"
                quiz = Quiz.objects.create(
                    title=quiz_title,
                    extracted_text=text,
                    user=request.user
                )
                
                # Create questions
                for idx, q_data in enumerate(questions_data):
                    question = Question.objects.create(
                        quiz=quiz,
                        question_text=q_data['question'],
                        correct_answer=q_data.get('correctAnswer'),
                        correct_answer_text=q_data.get('correctAnswerText'),
                        question_type=q_data.get('question_type', question_type),
                        order=idx
                    )
                    for opt_idx, option in enumerate(q_data.get('options', [])):
                        QuestionOption.objects.create(
                            question=question,
                            option_text=option,
                            option_order=opt_idx
                        )
                
                return Response({'quiz_id': quiz.id}, status=status.HTTP_201_CREATED)
                
            finally:
                # Always clean up temp file
                try:
                    default_storage.delete(file_path)
                except:
                    pass
                    
        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"DEBUG: Exception occurred: {error_msg}")
            traceback.print_exc()  # Log to console for debugging
            return Response({'error': f'Server error: {error_msg}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class QuizAttemptsListView(generics.ListAPIView):
    """API endpoint to retrieve user's quiz attempts"""
    serializer_class = None  # We'll return custom response
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        attempts = QuizAttempt.objects.filter(user=request.user).values(
            'id', 'score', 'total_questions', 'completed_at'
        ).order_by('-completed_at')
        
        return Response(list(attempts), status=status.HTTP_200_OK)


class QuizStatisticsListView(generics.ListAPIView):
    """API endpoint to retrieve user's quiz statistics"""
    serializer_class = QuizStatisticsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return QuizStatistics.objects.filter(user=self.request.user).order_by('-attempted_at')