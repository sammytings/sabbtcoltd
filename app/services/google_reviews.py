import logging

import requests

from django.conf import settings
from django.core.cache import cache


logger = logging.getLogger(__name__)


GOOGLE_PLACES_API_URL = "https://places.googleapis.com/v1"

# Cache Google reviews for 6 hours.
# This prevents an API request on every homepage visit.
CACHE_KEY = "sabbtco_google_reviews"
CACHE_TIMEOUT = 60 * 60 * 6


def _get_api_key():
    """
    Get the Google Places API key from Django settings.
    """

    return getattr(
        settings,
        "GOOGLE_PLACES_API_KEY",
        "",
    )


def _get_headers(field_mask):
    """
    Build headers required by Google Places API (New).
    """

    api_key = _get_api_key()

    return {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": field_mask,
    }


def find_sabbtco_place():
    """
    Find the SABBTCo Google Business Profile.

    We use Google's Text Search API instead of guessing
    the Place ID from a shortened Google Maps URL.
    """

    api_key = _get_api_key()

    if not api_key:
        logger.warning(
            "GOOGLE_PLACES_API_KEY is not configured."
        )
        return None

    url = (
        f"{GOOGLE_PLACES_API_URL}"
        "/places:searchText"
    )

    payload = {
        "textQuery": "SABBTCo",
        "pageSize": 5,
    }

    field_mask = (
        "places.id,"
        "places.displayName,"
        "places.formattedAddress,"
        "places.googleMapsUri"
    )

    try:
        response = requests.post(
            url,
            json=payload,
            headers=_get_headers(field_mask),
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        places = data.get(
            "places",
            []
        )

        if not places:
            logger.warning(
                "No Google Places result found for SABBTCo."
            )
            return None

        # Google returns results ordered by relevance.
        place = places[0]

        logger.info(
            "SABBTCo Google Place found: %s | %s",
            place.get(
                "displayName",
                {}).get(
                    "text",
                    "Unknown",
                ),
            place.get(
                "id",
                "No ID",
            ),
        )

        return place

    except requests.RequestException as exc:
        logger.error(
            "Google Places Text Search failed: %s",
            exc,
        )

        return None


def get_sabbtco_reviews():
    """
    Fetch SABBTCo's Google rating and reviews.

    Results are cached for six hours.
    """

    cached_reviews = cache.get(
        CACHE_KEY
    )

    if cached_reviews is not None:
        return cached_reviews

    empty_result = {
        "available": False,
        "name": "SABBTCo",
        "rating": None,
        "review_count": None,
        "reviews": [],
        "google_maps_url": (
            "https://www.google.com/maps/"
            "search/?api=1&query=SABBTCo"
        ),
    }

    api_key = _get_api_key()

    if not api_key:
        logger.warning(
            "Google Places API key is missing."
        )

        return empty_result

    place = find_sabbtco_place()

    if not place:
        return empty_result

    place_id = place.get("id")

    if not place_id:
        logger.warning(
            "Google returned SABBTCo without a Place ID."
        )

        return empty_result

    url = (
        f"{GOOGLE_PLACES_API_URL}"
        f"/places/{place_id}"
    )

    field_mask = (
        "id,"
        "displayName,"
        "rating,"
        "userRatingCount,"
        "googleMapsUri,"
        "reviews"
    )

    try:
        response = requests.get(
            url,
            headers=_get_headers(field_mask),
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        reviews = []

        for review in data.get(
            "reviews",
            []
        ):

            author = review.get(
                "authorAttribution",
                {}
            )

            review_text_data = review.get(
                "text",
                {}
            )

            if isinstance(
                review_text_data,
                dict,
            ):
                review_text = (
                    review_text_data.get(
                        "text",
                        ""
                    )
                )
            else:
                review_text = ""

            review_item = {
                "name": author.get(
                    "displayName",
                    "Google User",
                ),

                "profile_photo": author.get(
                    "photoUri",
                    "",
                ),

                "profile_url": author.get(
                    "uri",
                    "",
                ),

                "rating": review.get(
                    "rating",
                    0,
                ),

                "text": review_text,

                "relative_time": review.get(
                    "relativePublishTimeDescription",
                    "",
                ),

                "google_maps_url": review.get(
                    "googleMapsUri",
                    data.get(
                        "googleMapsUri",
                        "",
                    ),
                ),
            }

            reviews.append(
                review_item
            )

        result = {
            "available": True,

            "name": data.get(
                "displayName",
                {}).get(
                    "text",
                    "SABBTCo",
                ),

            "rating": data.get(
                "rating",
                0,
            ),

            "review_count": data.get(
                "userRatingCount",
                0,
            ),

            "google_maps_url": data.get(
                "googleMapsUri",
                "",
            ),

            "reviews": reviews,
        }

        cache.set(
            CACHE_KEY,
            result,
            CACHE_TIMEOUT,
        )

        logger.info(
            "Loaded %s Google reviews for SABBTCo.",
            len(reviews),
        )

        return result

    except requests.RequestException as exc:
        logger.error(
            "Google Places Details failed: %s",
            exc,
        )

        return empty_result