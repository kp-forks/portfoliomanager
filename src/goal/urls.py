from django.urls import path

from .views import (
    GoalListView,
    GoalDetailView,
    GoalDeleteView,
    add_goal,
    add_retirement_goal,
    ChartData
)

app_name = 'goals'

urlpatterns = [
    path('', GoalListView.as_view(), name='goal-list'),
    path('create/', add_goal, name='goal-add'),
    path('create-retirement/', add_retirement_goal, name='goal-add-retirement'),
    path('<id>/', GoalDetailView.as_view(), name='goal-detail'),
    path('<id>/delete/', GoalDeleteView.as_view(), name='goal-delete'),
    path('api/chart/data/<id>', ChartData.as_view())

]