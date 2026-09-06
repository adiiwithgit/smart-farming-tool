"""
AI vision layer for the Smart Farming Assistant.

All three functions below are currently placeholders (status: "not_implemented"),
returning generic guidance instead of a real prediction. They all share the
exact same signature — image_bytes in, dict out — so whichever model your
teammate finishes first can be wired in without touching main.py or the
frontend at all.

WHY THESE ARE STUBS RIGHT NOW:
We originally called Hugging Face's free hosted Inference API for a public
plant-disease model. As of testing on 2026-09-06, HF's platform changed:
most community-trained models (this one included) are no longer served by
any Inference Provider — the API returns
  {"error": "Model not supported by provider hf-inference"}
This isn't a bug in our code; it's a platform-side change affecting most
fine-tuned community models, not just this one specific model.

HOW TO WIRE IN YOUR TEAMMATE'S MODEL:
Pick whichever matches how they finish training:

  A) They give you a model file (.pth, .h5, .onnx, etc.)
     -> Load it once at module level (see commented example below), then
        replace the stub body with real preprocessing + inference.

  B) They host it on Hugging Face
     -> First confirm it's actually usable via Inference Providers: on the
        model's Hugging Face page, look for an "Inference Providers" widget
        on the right. If it says "This model is not currently available via
        any of the supported Inference Providers," the free hosted-API route
        won't work for it either — you'll need option A instead (running it
        locally) or a paid Inference Endpoint.

# Example for option A once you have a model file, e.g. backend/models/disease_model.pth:
#
# import torch
# from torchvision import models, transforms
# from PIL import Image
# import io
#
# _model = models.mobilenet_v2()
# _model.classifier[1] = torch.nn.Linear(_model.classifier[1].in_features, NUM_CLASSES)
# _model.load_state_dict(torch.load("models/disease_model.pth", map_location="cpu"))
# _model.eval()
#
# _transform = transforms.Compose([
#     transforms.Resize((224, 224)),
#     transforms.ToTensor(),
# ])
#
# async def diagnose_disease(image_bytes: bytes) -> dict:
#     image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
#     tensor = _transform(image).unsqueeze(0)
#     with torch.no_grad():
#         output = _model(tensor)
#         probs = torch.softmax(output, dim=1)[0]
#         top_idx = int(probs.argmax())
#         label = CLASS_NAMES[top_idx]  # your teammate's label list
#         confidence = round(float(probs[top_idx]) * 100, 1)
#     return {"status": "ok", "label": label, "confidence": confidence, "tip": _generic_tip(label)}
"""

from typing import Dict, Any

TREATMENT_HINTS = {
    "healthy": "No signs of disease — keep up current care and re-check weekly.",
    "blight": "Remove and destroy affected leaves. Apply a copper-based fungicide and avoid overhead watering.",
    "rust": "Apply sulfur or copper fungicide. Improve airflow between plants by spacing them out.",
    "spot": "Remove infected leaves, apply a broad-spectrum fungicide, and avoid wetting leaves when watering.",
    "mildew": "Improve air circulation, reduce humidity around plants, and apply a fungicide if it spreads.",
    "mold": "Improve drainage and airflow. Remove affected material and apply an appropriate fungicide.",
    "virus": "No cure for viral infections — remove and destroy the plant to prevent spread to others.",
    "rot": "Improve drainage, avoid overwatering, and remove affected roots/leaves immediately.",
}


def _generic_tip(label: str) -> str:
    label_lower = label.lower()
    for keyword, tip in TREATMENT_HINTS.items():
        if keyword in label_lower:
            return tip
    return "Monitor the plant closely and consult a local agricultural extension officer if symptoms spread."


async def diagnose_disease(image_bytes: bytes) -> Dict[str, Any]:
    """STUB — awaiting teammate's trained disease model. See module docstring for wiring instructions."""
    return {
        "status": "not_implemented",
        "message": "Disease detection model is still training — this is a placeholder response.",
        "label": "Unknown",
        "confidence": 0.0,
        "tip": "Look for discoloration, spots, or wilting patterns, and consult a local expert in the meantime.",
    }


async def detect_pest(image_bytes: bytes) -> Dict[str, Any]:
    """STUB — awaiting teammate's trained pest model. Same signature as diagnose_disease()."""
    return {
        "status": "not_implemented",
        "message": "Pest detection model is still training — this is a placeholder response.",
        "label": "Unknown",
        "confidence": 0.0,
        "tip": "Check leaves for holes, webbing, or visible insects, and consult a local expert in the meantime.",
    }


async def detect_nutrient_deficiency(image_bytes: bytes) -> Dict[str, Any]:
    """STUB — awaiting teammate's trained nutrient-deficiency model. Same signature as diagnose_disease()."""
    return {
        "status": "not_implemented",
        "message": "Nutrient deficiency model is still training — this is a placeholder response.",
        "label": "Unknown",
        "confidence": 0.0,
        "tip": "Yellowing between leaf veins often signals nitrogen or magnesium deficiency — a soil test will confirm.",
    }