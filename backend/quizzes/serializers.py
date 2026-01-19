from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Quiz, Question, QuestionOption, QuizStatistics

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ['id', 'option_text', 'option_order']

class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'correct_answer', 'correct_answer_text', 'question_type', 'order', 'options']

class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'created_at', 'extracted_text', 'user', 'questions']


class QuizStatisticsSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    
    class Meta:
        model = QuizStatistics
        fields = ['id', 'quiz', 'quiz_title', 'correct_answers', 'total_questions', 'score', 'attempted_at']
        read_only_fields = ['id', 'attempted_at']