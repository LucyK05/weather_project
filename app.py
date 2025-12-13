from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Replace with your actual WeatherAPI.com API key
API_KEY = 'cbfa8daa7a884947bd7212728251312'

@app.route('/')
def index():
    location = request.args.get('location')
    unit = request.args.get('unit', 'c')  # 'c' for Celsius, 'f' for Fahrenheit
    error = None
    weather = None

    if location:
        url = f"http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={location}&days=7"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'error' in data:
                error = data['error']['message']
            else:
                weather = data
        else:
            error = "Failed to fetch weather data."

    return render_template(
        'index.html',
        weather=weather,
        error=error,
        location=location or '',
        unit=unit
    )

if __name__ == '__main__':
    app.run(debug=True)