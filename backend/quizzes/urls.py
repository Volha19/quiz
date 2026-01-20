from django.urls import path
from . import views

urlpatterns = [
    path('quizzes/', views.QuizListCreateView.as_view(), name='quiz-list-create'),
    path('quizzes/<int:pk>/', views.QuizDetailView.as_view(), name='quiz-detail'),
    path('quizzes/<int:pk>/submit/', views.QuizSubmitView.as_view(), name='quiz-submit'),
    path('questions/', views.QuestionCreateView.as_view(), name='question-create'),
    # Endpoint used by frontend: /api/quizzes/upload/
    path('quizzes/upload/', views.FileUploadView.as_view(), name='file-upload'),
    # Keep legacy shorter path for compatibility
    path('upload/', views.FileUploadView.as_view(), name='file-upload-legacy'),
    # Attempts endpoint for statistics
    path('attempts/', views.QuizAttemptsListView.as_view(), name='attempts-list'),
    # Statistics endpoint
    path('statistics/', views.QuizStatisticsListView.as_view(), name='statistics-list'),
    # Calendar data endpoint
    path('calendar/', views.QuizCalendarDataView.as_view(), name='calendar-data'),
]