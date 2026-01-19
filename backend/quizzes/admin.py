from django.contrib import admin
from .models import Quiz, Question, QuestionOption, QuizAttempt, QuizStatistics

class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 1

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'created_at', 'question_count']
    list_filter = ['created_at', 'user']
    search_fields = ['title']
    inlines = [QuestionInline]
    
    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Questions'

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'quiz', 'correct_answer', 'order']
    list_filter = ['quiz', 'order']
    search_fields = ['question_text']
    inlines = [QuestionOptionInline]

@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ['option_text', 'question', 'option_order']
    list_filter = ['question__quiz']
    search_fields = ['option_text']

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'user', 'score', 'total_questions', 'get_percentage', 'completed_at']
    list_filter = ['completed_at', 'user', 'quiz']
    search_fields = ['quiz__title', 'user__username']
    readonly_fields = ['completed_at']

@admin.register(QuizStatistics)
class QuizStatisticsAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'user', 'correct_answers', 'total_questions', 'score', 'attempted_at']
    list_filter = ['attempted_at', 'user', 'quiz']
    search_fields = ['quiz__title', 'user__username']
    readonly_fields = ['attempted_at']