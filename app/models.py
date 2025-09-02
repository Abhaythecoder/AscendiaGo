# # taramgo/app/models.py
from django.db import models

# class Itinerary(models.Model):
#     # Use Django's built-in JSONField, which is compatible with SQLite
#     itinerary_data = models.JSONField()
    
#     # Optional metadata fields
#     city = models.CharField(max_length=255)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"Itinerary for {self.city} created at {self.created_at.strftime('%Y-%m-%d')}"