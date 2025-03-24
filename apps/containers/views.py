import os
from dotenv import load_dotenv
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from web_project import TemplateLayout
from retell import Retell

# Load environment variables
load_dotenv()

client = Retell(
    api_key="key_af612dbafebc643d7491e2a407fd",  # .env içinde veya güvenli bir yerde saklayın
)

web_call_response = client.call.create_web_call(
    agent_id="agent_19a676d6a7174ae1204489cc12",
)
print(web_call_response.agent_id)


class ContainersView(TemplateView):
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        try:
            call_responses = client.call.list()
            context["call_responses"] = call_responses
        except Exception as e:
            print(f"Error fetching calls: {str(e)}")
            context["call_responses"] = []
        return context


def convert_transcript_object_word(word):
    try:
        return {"word": getattr(word, "word", ""), "start": getattr(word, "start", 0), "end": getattr(word, "end", 0)}
    except AttributeError:
        return {}


def convert_transcript_object(obj):
    try:
        return {
            "content": getattr(obj, "content", ""),
            "role": getattr(obj, "role", ""),
            "words": [convert_transcript_object_word(word) for word in getattr(obj, "words", [])],
            "metadata": getattr(obj, "metadata", {}),
        }
    except AttributeError:
        return {}


def get_call_details(request, call_id):
    try:
        call_response = client.call.retrieve(call_id)

        call_response_dict = {
            "call_type": getattr(call_response, "call_type", ""),
            "call_id": getattr(call_response, "call_id", ""),
            "agent_id": getattr(call_response, "agent_id", ""),
            "call_status": getattr(call_response, "call_status", ""),
            "transcript": getattr(call_response, "transcript", ""),
            "recording_url": getattr(call_response, "recording_url", ""),
            "public_log_url": getattr(call_response, "public_log_url", ""),
            "duration": getattr(call_response.call_cost, "total_duration_seconds", 0),
            "call_analysis": {
                "call_summary": getattr(call_response.call_analysis, "call_summary", ""),
                "user_sentiment": getattr(call_response.call_analysis, "user_sentiment", ""),
            },
        }
        print(call_response_dict)
        return JsonResponse(call_response_dict)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def start_call(request):
    try:
        data = json.loads(request.body)
        agent_id = data.get("agent_id")

        # Initialize call using Retell client's start method instead of create
        call_response = client.call.start(
            agent_id=agent_id,
            customer_number="+11234567890",  # Replace with actual test number
            agent_number="+10987654321",  # Replace with actual test number
        )

        return JsonResponse({"success": True, "call_id": call_response.call_id})
    except Exception as e:
        print(f"Error starting call: {str(e)}")  # Add logging for debugging
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def start_web_call(request):
    try:
        data = json.loads(request.body)
        agent_id = os.getenv("RETELL_AGENT_ID")

        if not agent_id:
            raise ValueError("RETELL_AGENT_ID not configured in environment")

        print(f"Creating web call for agent: {agent_id}")
        web_call_response = client.call.create_web_call(
            agent_id=agent_id,
            metadata={"user_name": data.get("user_name", "Anonymous"), "language": "tr", "auto_connect": True},
        )

        print(f"Web call response: {web_call_response}")

        # Check for access token and construct join URL
        access_token = getattr(web_call_response, "access_token", None)
        call_id = getattr(web_call_response, "call_id", None)

        if not access_token or not call_id:
            raise ValueError("Missing required attributes from Retell API response")

        # Update the URL to use the correct domain
        join_url = f"https://api.retellai.com/call/{call_id}?token={access_token}"

        response_data = {
            "success": True,
            "call_id": call_id,
            "agent_id": agent_id,
            "web_call_url": join_url,
            "access_token": access_token,
        }

        print(f"Returning response: {response_data}")
        return JsonResponse(response_data)

    except Exception as e:
        error_msg = f"Error creating web call: {str(e)}"
        print(error_msg)
        if "web_call_response" in locals():
            print(f"Available attributes: {dir(web_call_response)}")
        return JsonResponse({"success": False, "error": error_msg}, status=500)
