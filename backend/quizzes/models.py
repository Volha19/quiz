from django.db import models
from django.contrib.auth.models import User


class Quiz(models.Model):
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return self.title

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    # Default to 0; allow null for open-ended questions
    correct_answer = models.IntegerField(null=True, blank=True, default=0)
    # Store textual answer for open-ended questions
    correct_answer_text = models.TextField(null=True, blank=True)
    # Keep question type to satisfy existing DB NOT NULL constraint; default to multiple choice
    question_type = models.CharField(max_length=50, default='multiple_choice')
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.question_text[:50]

class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=500)
    option_order = models.IntegerField()
    
    class Meta:
        ordering = ['option_order']
    
    def __str__(self):
        return self.option_text[:50]

class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)
    answers = models.JSONField()  # Store user's answers
    
    def get_percentage(self):
        return round((self.score / self.total_questions) * 100)


class QuizStatistics(models.Model):
    """Tracks user performance statistics for each quiz attempt"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_statistics')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='statistics')
    correct_answers = models.IntegerField()  # Number of correct answers
    total_questions = models.IntegerField()  # Total questions in the quiz
    score = models.FloatField()  # Percentage score (0-100)
    attempted_at = models.DateTimeField(auto_now_add=True)  # When quiz was taken
    
    class Meta:
        ordering = ['-attempted_at']
        verbose_name = 'Quiz Statistics'
        verbose_name_plural = 'Quiz Statistics'
    
    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.score}%"
    
    def calculate_score(self):
        """Calculate percentage score based on correct answers"""
        if self.total_questions > 0:
            return round((self.correct_answers / self.total_questions) * 100, 2)
        return 0