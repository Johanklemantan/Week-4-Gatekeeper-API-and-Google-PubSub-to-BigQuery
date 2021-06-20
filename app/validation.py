from flask_inputs import Inputs
from flask_inputs.validators import JsonSchema
from google.cloud import pubsub_v1

message_payload = {
    "type": "object",
    "properties": {
        "activities": {
            "type": "array",
            "items": {"anyOf": [{"$ref": "#/$defs/insert"}, {"$ref": "#/$defs/delete"}]},
            "minItems": 1
        }
    },
    "$defs": {
        "insert": {
            "type": "object",
            "required": ["operation", "table", "col_names", "col_types", "col_values"],
            "properties": {
                "operation": {"const": "insert"},
                "table": {"type": "string"},
                "col_names": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "col_types": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "col_values": {
                    "type": "array"
                }
            }
        },
        "delete": {
            "type": "object",
            "required": ["operation", "table", "old_value"],
            "properties": {
                "operation": {"const": "delete"},
                "table": {"type": "string"},
                "old_value": {
                    "type": "object",
                    "required": ["col_names", "col_types", "col_values"],
                    "properties": {
                        "col_names": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "col_types": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "col_values": {
                            "type": "array"
                        }
                    }
                }
            }
        }
    }
}


class MessageInputs(Inputs):
    json = [JsonSchema(schema=message_payload)]


project_id = "week-2-de-blank-space-johan"
topic_id = "week4topic"
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)

invalid_message = []


def validate_message(request):
    inputs = MessageInputs(request)
    if inputs.validate():
        future = publisher.publish(
            topic_path, str(request.data).encode("utf-8"))
        return print(future.result())
    else:
        invalid_message.append(inputs.errors[0])
        return "Invalid Message: " + str(len(invalid_message))
