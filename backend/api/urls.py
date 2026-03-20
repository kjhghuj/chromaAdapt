from django.urls import path
from . import views

urlpatterns = [
    path("", views.root),
    path("analyze", views.analyze_image),
    path("analyze-edit", views.analyze_edit_image),
    path("secondary-plan", views.generate_secondary_plan),
    path("color-mapping", views.create_color_mapping),
    path("color-adaptation", views.color_adaptation),
    path("translate", views.translate_image),
    path("generate", views.generate_image_view),
    path("edit", views.edit_image),
]
