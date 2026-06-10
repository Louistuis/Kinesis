import os

# API Configuration
GEMINI_AUTH_MODE = os.environ.get("GEMINI_AUTH_MODE", "apikey")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_AUTH_MODE == "apikey" and not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required when using API Key auth.")

MODEL_NAME = "gemini-3-flash-preview"
KINESIS_VERSION = "1.1.4"

def get_genai_client():
    from google import genai
    if GEMINI_AUTH_MODE == "gemini-cli":
        import json
        from google.oauth2.credentials import Credentials
        creds_path = os.path.expanduser("~/.gemini/oauth_creds.json")
        try:
            with open(creds_path, 'r') as f:
                data = json.load(f)
            creds = Credentials(token=data['access_token'])
            return genai.Client(credentials=creds)
        except Exception as e:
            raise RuntimeError(f"Failed to load Gemini CLI credentials from {creds_path}: {e}")
    elif GEMINI_AUTH_MODE == "oauth":
        return genai.Client()
    else:
        return genai.Client(api_key=GEMINI_API_KEY)

# Resolution and Scaling Config
TARGET_MAX_WIDTH = 1512 # Full MacBook logical width for pixel-perfect precision
WAIT_TIME_SECONDS = 0.5

# Speed presets for /speed command
SPEED_PRESETS = {
    "fast": 0.2,
    "normal": 0.5,
    "slow": 1.5,
}

# Estimated cost per API call (Gemini 3 Flash pricing rough estimate)
COST_PER_API_CALL = 0.0005

def calculate_scaling_factor(original_width: int, target_width: int = TARGET_MAX_WIDTH) -> float:
    """
    factor = target width / original width
    """
    if original_width <= target_width:
        return 1.0
    return target_width / original_width

def model_to_native_coords(x_model: int, y_model: int, logical_width: int, logical_height: int) -> tuple[int, int]:
    """
    Gemini 2.5 Computer Use natively outputs coordinates in a normalized 1000x1000 grid.
    We map these directly to the PyAutoGUI logical screen dimensions.
    """
    x_native = int((x_model / 1000.0) * logical_width)
    y_native = int((y_model / 1000.0) * logical_height)
    return x_native, y_native

def native_to_model_coords(x_native: int, y_native: int, logical_width: int, logical_height: int) -> tuple[int, int]:
    x_model = int((x_native / logical_width) * 1000.0)
    y_model = int((y_native / logical_height) * 1000.0)
    return x_model, y_model
