from flask import Flask, render_template, request, redirect, send_from_directory, url_for, session
import json
import uuid
import os
from datetime import timedelta
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

app = Flask(__name__)
app.secret_key = 'tomato_disease_app_secret_2024'
app.permanent_session_lifetime = timedelta(days=7)

UPLOAD_DIR = 'uploadimages'
os.makedirs(UPLOAD_DIR, exist_ok=True)

CLASS_NAMES = [
    'Tomato___Bacterial_spot',
    'Tomato___Early_blight',
    'Tomato___Late_blight',
    'Tomato___Leaf_Mold',
    'Tomato___Septoria_leaf_spot',
    'Tomato___Spider_mites Two-spotted_spider_mite',
    'Tomato___Target_Spot',
    'Tomato___Tomato_Yellow_Leaf_Curl_Virus',
    'Tomato___Tomato_mosaic_virus',
    'Tomato___healthy',
]

CONFIDENCE_THRESHOLD = 0.70
MODEL_PATH = 'models/tomato_disease.pth'

with open('plant_disease.json', 'r', encoding='utf-8') as file:
    plant_disease = json.load(file)


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def load_model():
    model = models.resnet50(weights=None)
    model.fc = nn.Linear(model.fc.in_features, len(CLASS_NAMES))
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.to(device)
    model.eval()
    return model

model = load_model()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

@app.route('/uploadimages/<path:filename>')
def uploaded_images(filename):
    return send_from_directory(UPLOAD_DIR, filename)

@app.route('/', methods=['GET'])
def home():
    farmer_name = session.get('farmer_name', None)
    return render_template('home.html', farmer_name=farmer_name)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        farmer_name = request.form.get('farmer_name', '').strip()
        if farmer_name:
            session.permanent = True
            session['farmer_name'] = farmer_name
            return redirect('/')
        return render_template('signup.html', error='Please enter your name')
    return render_template('signup.html')

@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect('/')

@app.route('/information', methods=['GET'])
def information():
    return render_template('information.html')


def model_predict(image_path):
    img = Image.open(image_path).convert('RGB')
    tensor = transform(img).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.softmax(outputs, dim=1)
        confidence, predicted_idx = torch.max(probs, 1)

    confidence_value = float(confidence.item())
    predicted_idx = int(predicted_idx.item())
    prediction_label = plant_disease[predicted_idx]

    result = {
        'confidence': confidence_value,
        'confidence_percent': confidence_value * 100,
        'label': prediction_label,
        'predicted_idx': predicted_idx,
        'status': 'success',
    }

    if confidence_value < CONFIDENCE_THRESHOLD:
        result['status'] = 'low_confidence'
        result['message'] = f'Image quality issue - Confidence only {confidence_value * 100:.1f}%. Please upload a clear, well-lit image.'

    return result

@app.route('/upload/', methods=['POST', 'GET'])
def uploadimage():
    if request.method == "POST":
        if 'img' not in request.files:
            return redirect('/')
        
        image = request.files['img']
        if image.filename == '':
            return redirect('/')
        
        temp_name = f"uploadimages/temp_{uuid.uuid4().hex}"
        image.save(f'{temp_name}_{image.filename}')
        print(f'{temp_name}_{image.filename}')
        
        prediction_result = model_predict(f'./{temp_name}_{image.filename}')
        farmer_name = session.get('farmer_name', None)
        
        return render_template(
            'home.html',
            result=True,
            imagepath=f'/{temp_name}_{image.filename}',
            prediction_result=prediction_result,
            farmer_name=farmer_name
        )
    else:
        return redirect('/')

if __name__ == "__main__":
    os.makedirs('uploadimages', exist_ok=True)
    app.run(debug=True)