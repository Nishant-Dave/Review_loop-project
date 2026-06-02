import os
import json
import logging
from django.conf import settings
from groq import Groq

logger = logging.getLogger('reviews')

def analyze_negative_feedback(feedback):
    """
    Analyzes negative customer feedback using the Groq API.
    Extracts sentiment, emotion, urgency, and generates three potential reply options.
    
    If the API call fails or the GROQ_API_KEY is not set, returns a fallback JSON response.
    """
    # Extract details from the feedback instance
    rating = feedback.rating
    issue = feedback.issue or "General"
    comment = feedback.comment or ""
    cafe_name = feedback.cafe.name if feedback.cafe else "Our Cafe"

    # Get API key from django settings or environment variable
    api_key = getattr(settings, 'GROQ_API_KEY', os.getenv('GROQ_API_KEY'))

    # Fallback response in case of any failures
    fallback_response = {
        "sentiment": "Negative",
        "emotion": "Disappointed",
        "urgency": "Medium",
        "reply_1": f"Hi, thank you for letting us know about the issue with {issue.lower()}. We sincerely apologize and hope to make things right.",
        "reply_2": f"Hello, we are sorry your experience at {cafe_name} did not meet expectations. We are addressing the issue with {issue.lower()} immediately.",
        "reply_3": f"We appreciate your feedback regarding our {issue.lower()}. We are taking steps to ensure this does not happen again."
    }

    if not api_key:
        logger.warning("GROQ_API_KEY is not set. Returning fallback response.")
        return fallback_response

    try:
        # Initialize Groq client
        client = Groq(api_key=api_key)

        # Call Groq API in JSON mode
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI assistant analyzing customer feedback for a cafe. "
                        "Output your response as a JSON object containing keys: "
                        "'sentiment', 'emotion', 'urgency', 'reply_1', 'reply_2', and 'reply_3'. "
                        "All three replies must be written as polite, professional, and empathetic response drafts "
                        "from the cafe owner directly to the customer. Customize them based on the specific issue mentioned."
                    )
                },
                {
                    "role": "user",
                    "content": f"Cafe Name: {cafe_name}\nRating: {rating}\nIssue: {issue}\nComment: {comment}"
                }
            ],
            model="llama3-8b-8192",
            response_format={"type": "json_object"}
        )

        response_content = chat_completion.choices[0].message.content
        result = json.loads(response_content)

        # Validate that all required keys are in the JSON response
        required_keys = ["sentiment", "emotion", "urgency", "reply_1", "reply_2", "reply_3"]
        for key in required_keys:
            if key not in result:
                result[key] = fallback_response[key]

        return result

    except Exception as e:
        logger.error(f"Error during Groq API negative feedback analysis: {e}")
        return fallback_response
