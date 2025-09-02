# taramgo/app/views.py

from django.shortcuts import render
from .forms import ItineraryForm
import os
import json
import httpx
import logging

# Set up proper logging
logger = logging.getLogger(__name__)

# --- Gemini API Configuration ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("FATAL: GEMINI_API_KEY not found in your .env file.")

# Use the correct model name for Gemini
GEMINI_MODEL_NAME = "gemini-1.5-flash"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL_NAME}:generateContent"


def _render_itinerary_page(request, itinerary_data, city, error_message=None):
    """
    Re-usable function to render the itinerary page.
    It now passes the itinerary data as both a Python object (for Django loops)
    and a JSON string (for the JavaScript part).
    """
    map_data = []
    if not error_message and itinerary_data:
        logger.debug(f"Building map data for {len(itinerary_data)} days.")
        for day_index, day_plan in enumerate(itinerary_data):
            for activity in day_plan.get('activities', []):
                activity_id = activity.get('id', 'No ID')
                try:
                    if activity.get('type') == 'Visit' and 'latitude' in activity and 'longitude' in activity:
                        map_data.append({'lat': float(activity['latitude']), 'lon': float(activity['longitude']), 'popupText': activity.get('location_name', ''), 'activityId': activity_id, 'type': 'Visit', 'dayIndex': day_index})
                    elif activity.get('type') == 'Travel' and 'start_point_lat' in activity and 'end_point_lat' in activity:
                        map_data.append({'lat': float(activity['start_point_lat']), 'lon': float(activity['start_point_lon']), 'popupText': f"Start: {activity.get('start_point_location', '')}", 'activityId': f"{activity_id}-start", 'type': 'Travel', 'dayIndex': day_index})
                        map_data.append({'lat': float(activity['end_point_lat']), 'lon': float(activity['end_point_lon']), 'popupText': f"End: {activity.get('end_point_location', '')}", 'activityId': f"{activity_id}-end", 'type': 'Travel', 'dayIndex': day_index})
                except (ValueError, TypeError, KeyError) as e:
                    logger.error(f"Skipping map point for activity '{activity_id}' due to invalid data: {e}")
        logger.debug(f"Finished building map_data. Total points: {len(map_data)}")

    context = {
        'form_data': {'city': city},
        'itinerary_data': itinerary_data,  # Passed as a Python object for Django template loops
        'itinerary_json': json.dumps(itinerary_data), # CORRECTLY passed as a JSON string for the script tag
        'map_points_json': json.dumps(map_data),
        'error_message': error_message
    }

    # 👇 Add this to see raw JSON in your terminal
    print("=== RAW ITINERARY JSON ===")
    print(json.dumps(itinerary_data, indent=2))

    return render(request, 'app/itinerary_result.html', context)


async def generate_itinerary_view(request):
    if request.method == 'POST':
        form = ItineraryForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            city = cleaned_data['city']
            start_date_obj = cleaned_data['start_date']
            start_time_str = cleaned_data['start_time']
            end_date_obj = cleaned_data['end_date']
            ending_point = cleaned_data.get('ending_point', 'a major departure hub')
            duration_days = (end_date_obj - start_date_obj).days + 1
            itinerary_generated_data = []
            error_message = None

            # --- MODIFIED PROMPT ---
            # The prompt has been updated to be extremely specific about the requirement
            # for latitude and longitude coordinates for every single activity.
            prompt = f"""
            
            Generate a detailed travel itinerary for a {duration_days}-day trip to {city}.
            The traveler is a {cleaned_data['traveler_type']} with a {cleaned_data['budget']} budget.
            Their interests are: {", ".join(cleaned_data['interests']) if cleaned_data['interests'] else "General sightseeing"}.
            The trip starts on {start_date_obj.strftime('%Y-%m-%d')} at {start_time_str} and ends on {end_date_obj.strftime('%Y-%m-%d')} at {cleaned_data['end_time']}.
            The user must end up at {ending_point}.
            All Cost Should be in the Local currency of the Country.

            **DESCRIPTION FORMAT RULES**:
            - Every activity description must be **concise, 3–4 bullet points only**.
            - Write them like checklist items (e.g., "- Explore temple", "- Take photos").
            - Do NOT write paragraphs, long explanations, or guides. Keep it short and practical.

            **CRITICAL INSTRUCTION**: For every single activity, whether it is a 'Visit' or a 'Travel' type, you MUST provide precise latitude and longitude coordinates. This is a mandatory requirement.
            - For 'Visit' activities, you MUST populate the `latitude` and `longitude` fields.
            - For 'Travel' activities, you MUST populate all four coordinate fields: `start_point_lat`, `start_point_lon`, `end_point_lat`, and `end_point_lon`.
            Do not leave any of these coordinate fields empty, null, or 0 unless the location is a general area that cannot be mapped. The response is not useful without these coordinates.
            """

            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseSchema": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "day": {"type": "STRING"},
                                "date": {"type": "STRING"},
                                "activities": {
                                    "type": "ARRAY",
                                    "items": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "id": {"type": "STRING"},
                                            "type": {"type": "STRING", "enum": ["Visit", "Travel"]},
                                            "time_slot": {"type": "STRING"},
                                            "description": {"type": "STRING"},
                                            "location_name": {"type": "STRING"},
                                            "latitude": {"type": "NUMBER"},
                                            "longitude": {"type": "NUMBER"},
                                            "cost_estimate": {"type": "STRING"},
                                            "transport_mode_details": {"type": "STRING"},
                                            "start_point_location": {"type": "STRING"},
                                            "end_point_location": {"type": "STRING"},
                                            "start_point_lat": {"type": "NUMBER"},
                                            "start_point_lon": {"type": "NUMBER"},
                                            "end_point_lat": {"type": "NUMBER"},
                                            "end_point_lon": {"type": "NUMBER"}
                                        },
                                        "required": ["id", "type", "time_slot", "description"]
                                    }
                                }
                            },
                            "required": ["day", "date", "activities"]
                        }
                    }
                }
            }
            
            try:
                logger.debug(f"Sending payload to Gemini: {json.dumps(payload, indent=2)}")
                async with httpx.AsyncClient(timeout=90.0) as client:
                    response = await client.post(
                        f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                        json=payload
                    )
                    response.raise_for_status()

                response_data = response.json()
                itinerary_generated_data = json.loads(response_data['candidates'][0]['content']['parts'][0]['text'])

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error from Gemini API: {e.response.status_code}")
                logger.error(f"Gemini's exact error message: {e.response.text}")
                error_message = f"Gemini API returned an error ({e.response.status_code}). Please check the server logs."
            except (json.JSONDecodeError, KeyError):
                logger.error("Failed to decode or parse JSON from Gemini's response.", exc_info=True)
                error_message = "The model's response was not valid or had an unexpected structure. Please try again."
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}", exc_info=True)
                error_message = f"An unexpected error occurred: {e}"

            return _render_itinerary_page(request, itinerary_generated_data, city, error_message)
        else:
            logger.warning(f"Form validation failed. Errors: {form.errors.as_json()}")
            return render(request, 'app/itinerary_form.html', {'form': form})
    else:
        form = ItineraryForm()
        return render(request, 'app/itinerary_form.html', {'form': form})

def itinerary_view(request):
    # wherever you call Gemini API
    itinerary_json = get_itinerary_from_gemini(...)

    # print raw json in your terminal
    print("=== RAW ITINERARY JSON ===")
    print(itinerary_json)

    return render(request, "itinerary_result.html", {
        "itinerary_json": itinerary_json,
        "form_data": form_data
    })