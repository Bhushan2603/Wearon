from flask import Flask, request, jsonify, send_from_directory
from gradio_client import Client, file
from flask_cors import CORS
import os
import traceback
import shutil
import base64

app = Flask(__name__)
CORS(app)

client = Client("yisol/IDM-VTON")

# Directory to save uploaded and processed files
UPLOAD_FOLDER = 'static/uploads'
RESULT_FOLDER = 'static/results'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(RESULT_FOLDER):
    os.makedirs(RESULT_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

@app.route('/process', methods=['POST'])
def predict():
    try:
        # Get the product image URL from the request
        product_image_url = request.form.get('product_image_url')
        
        # Handle the uploaded model image
        if 'model_image' not in request.files:
            return jsonify(error='No model image file provided'), 400

        model_image = request.files['model_image']
        if model_image.filename == '':
            return jsonify(error='No selected file'), 400

        # Save the uploaded file to the upload directory
        filename = os.path.join(app.config['UPLOAD_FOLDER'], model_image.filename)
        model_image.save(filename)

        base_path = os.getcwd()
        full_filename = os.path.normpath(os.path.join(base_path, filename))

        print("Product image = ", product_image_url)
        print("Model image = ", full_filename)
        
        # Perform prediction
        try:
            result = client.predict(
                dict={"background": file(full_filename), "layers": [], "composite": None},
                garm_img=file(product_image_url),
                garment_des="Hello!!",
                is_checked=True,
                is_checked_crop=False,
                denoise_steps=30,
                seed=42,
                api_name="/tryon"
            )
        except Exception as e:
            traceback.print_exc()
            raise

        print(result)
        # Extract the path of the first output image
        output_image_path = result[0]

        # Copy the output image to the RESULT_FOLDER
        output_image_filename = os.path.basename(output_image_path)
        local_output_path = os.path.join(app.config['RESULT_FOLDER'], output_image_filename)
        shutil.copy(output_image_path, local_output_path)

        # Remove the uploaded file after processing
        os.remove(filename)

        # Encode the output image in base64
        with open(local_output_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Return the output image in JSON format
        return jsonify(image=encoded_image), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

 