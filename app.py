from flask import Flask, request, jsonify
from PIL import Image, ImageOps
import io
import sys
import os
import base64


app = Flask(__name__)

sys.path.append(os.path.abspath("./rembg"))

from rembg import remove

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/process", methods=["POST"])
def process():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    input_file = request.files["image"]
    if input_file.filename == "":
        return jsonify({"error": "No image selected"}), 400

    try:
        # Open the uploaded image
        input_image = Image.open(input_file).convert("RGBA")

        # Get transformation values from the request
        scale = float(request.form.get("scale", 1))
        posX = float(request.form.get("posX", 0))
        posY = float(request.form.get("posY", 0))

        # Remove the background
        input_bytes = io.BytesIO()
        input_image.save(input_bytes, format="PNG")
        input_bytes = input_bytes.getvalue()
        output_bytes = remove(input_bytes)

        # Load the processed image
        processed_image = Image.open(io.BytesIO(output_bytes)).convert("RGBA")

        # Load the frame background
        frame_background = Image.open("static/Template.jpg").convert("RGBA")
        frame_width, frame_height = frame_background.size

        # Resize the processed image according to the scale
        processed_width, processed_height = processed_image.size
        resized_image = processed_image.resize(
            (int(processed_width * scale), int(processed_height * scale)), Image.Resampling.LANCZOS
        )

        # Calculate the position offsets based on the frame and user input
        offset_x = int((frame_width - resized_image.size[0]) / 2 + posX)
        offset_y = int((frame_height - resized_image.size[1]) / 2 + posY)

        # Composite the processed image onto the frame background
        frame_background.paste(resized_image, (offset_x, offset_y), resized_image)

        # Save the final image with the frame
        output_buffer = io.BytesIO()
        frame_background.save(output_buffer, format="PNG")
        output_buffer.seek(0)

        # Convert the final image to Base64 for download
        base64_image = base64.b64encode(output_buffer.getvalue()).decode("utf-8")

        return jsonify({"image": f"data:image/png;base64,{base64_image}"})

    except Exception as e:
        return jsonify({"error": f"Processing error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
