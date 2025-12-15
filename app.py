from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_key'  # Change this in production!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# WeatherAPI key - loaded securely from .env
API_KEY='cbfa8daa7a884947bd7212728251312'

# Model for saved locations
class SavedLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)      # User-defined name (e.g., "Home")
    query = db.Column(db.String(200), nullable=False)     # Location string for API (e.g., "London")

    def __repr__(self):
        return f'<SavedLocation {self.name}: {self.query}>'

# Create database tables on startup
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/weather', methods=['GET', 'POST'])
def weather():
    location = request.args.get('location') or request.form.get('location')
    unit = request.args.get('unit', 'c')
    weather = None
    error = None

    # Handle saving a location
    if request.method == 'POST' and 'save_location' in request.form:
        name = request.form.get('save_name', '').strip()
        if not name:
            flash('Please enter a name for the saved location.', 'danger')
        elif not location:
            flash('No location to save. Search for a location first.', 'danger')
        else:
            # Check for duplicate (by query string)
            stmt = select(SavedLocation).filter_by(query=location)
            existing = db.session.execute(stmt).scalar_one_or_none()

            if existing:
                flash(f'Location "{existing.name}" (query: {location}) is already saved.', 'warning')
            else:
                new_loc = SavedLocation(name=name, query=location)
                db.session.add(new_loc)
                db.session.commit()
                flash(f'Location "{name}" saved successfully!', 'success')
        return redirect(url_for('weather', location=location, unit=unit))

    # Fetch weather data
    if location:
        url = f"http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={location}&days=8"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'error' in data:
                error = data['error']['message']
            else:
                weather = data
        else:
            error = "Failed to fetch weather data from the API."

    return render_template(
        'weather.html',
        weather=weather,
        error=error,
        location=location or '',
        unit=unit
    )

@app.route('/locations')
def locations():
    # Get all saved locations
    saved_locations = db.session.execute(select(SavedLocation)).scalars().all()
    locations_data = []

    for loc in saved_locations:
        url = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={loc.query}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            locations_data.append({
                'id': loc.id,
                'name': loc.name,
                'query': loc.query,
                'current': data.get('current'),
                'location': data.get('location'),
                'error': None
            })
        else:
            locations_data.append({
                'id': loc.id,
                'name': loc.name,
                'query': loc.query,
                'current': None,
                'location': None,
                'error': 'Unable to fetch current weather'
            })

    return render_template('locations.html', locations=locations_data)

@app.route('/delete_location/<int:loc_id>', methods=['POST'])
def delete_location(loc_id):
    # Modern replacement for the old .query.get_or_404()
    location_to_delete = db.session.get(SavedLocation, loc_id)

    if location_to_delete is None:
        flash('Location not found.', 'danger')
        return redirect(url_for('locations'))

    db.session.delete(location_to_delete)
    db.session.commit()
    flash(f'Location "{location_to_delete.name}" has been deleted.', 'success')
    return redirect(url_for('locations'))

if __name__ == '__main__':
    app.run(debug=True)