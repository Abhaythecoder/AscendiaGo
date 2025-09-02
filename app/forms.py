# itineraries/forms.py
from django import forms

TRAVELER_TYPE_CHOICES = [
    ('solo', 'Solo'),
    ('couple', 'Couple'),
    ('family', 'Family with Kids'),
    ('friends', 'Couple of Friends'),
    ('business', 'Business'),
    ('other', 'Other'),
]

BUDGET_CHOICES = [
    ('low', 'Economy'),
    ('mid', 'Mid-range'),
    ('high', 'Luxury'),
]

FOOD_PREFERENCE_CHOICES = [
    ('vegetarian', 'Vegetarian'),
    ('vegan', 'Vegan'),
    ('halal', 'Halal'),
    ('kosher', 'Kosher'),
    ('gluten_free', 'Gluten-Free'),
    ('seafood', 'Seafood'),
    ('italian', 'Italian'),
    ('asian', 'Asian'),
    ('local', 'Local Cuisine'),
    ('none', 'No Specific Preference'),
]

INTEREST_CHOICES = [
    ('history', 'History'),
    ('art', 'Art & Culture'),
    ('nature', 'Nature & Outdoors'),
    ('adventure', 'Adventure Sports'),
    ('shopping', 'Shopping'),
    ('nightlife', 'Nightlife'),
    ('relaxing', 'Relaxing'),
    ('foodie', 'Foodie Exploration'),
    ('museums', 'Museums'),
    ('photography', 'Photography'),
]

class ItineraryForm(forms.Form):
    city = forms.CharField(
        label="Destination City",
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'e.g., Paris, Tokyo'})
    )
    start_date = forms.DateField(
        label="Start Date",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    # Use TimeField to accept any time, not just fixed choices
    start_time = forms.TimeField(
        label="Start Time of Day",
        widget=forms.TimeInput(attrs={'type': 'time'})
    )
    end_date = forms.DateField(
        label="End Date",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    # Use TimeField to accept any time
    end_time = forms.TimeField(
        label="End Time of Day",
        widget=forms.TimeInput(attrs={'type': 'time'})
    )
    starting_point = forms.CharField(
        label="Starting Point (optional, e.g., your hotel or arrival airport)",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g., Charles de Gaulle Airport'})
    )
    ending_point = forms.CharField(
        label="Ending Point (optional, e.g., your departure airport)",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g., Gare du Nord'})
    )
    # Corrected the budget choices to match what your HTML is sending
    budget = forms.ChoiceField(
        label="Budget Level",
        choices=BUDGET_CHOICES,
        widget=forms.RadioSelect
    )
    traveler_type = forms.ChoiceField(
        label="Who are you traveling with?",
        choices=TRAVELER_TYPE_CHOICES,
        widget=forms.Select
    )
    food_preferences = forms.MultipleChoiceField(
        label="Food Preferences (select all that apply)",
        choices=FOOD_PREFERENCE_CHOICES,
        widget=forms.SelectMultiple,
        required=False
    )
    interests = forms.MultipleChoiceField(
        label="Interests (select all that apply)",
        choices=INTEREST_CHOICES,
        widget=forms.SelectMultiple,
        required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_date and end_date and start_time and end_time:
            # Combine date and time for full datetime objects for comparison
            from datetime import datetime
            
            start_datetime = datetime.combine(start_date, start_time)
            end_datetime = datetime.combine(end_date, end_time)

            if start_datetime >= end_datetime:
                self.add_error('end_date', "End date and time must be after Start date and time.")
                self.add_error('end_time', "End date and time must be after Start date and time.")
        return cleaned_data