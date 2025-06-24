from flask import Flask, request, jsonify, render_template_string
import threading
from datetime import datetime
import json
import os
import random

app = Flask(__name__)

# Thread-safe storage
location_data = {}
data_lock = threading.Lock()

# File path for storing districts
DISTRICTS_FILE = os.path.join(os.path.dirname(__file__), 'districts.json')

# Default polygon-based districts for Point Loma area
DEFAULT_DISTRICTS = {
    "Point Loma Naval Base": [
        [32.6967, -117.2186],
        [32.6967, -117.2050],
        [32.6850, -117.2050],
        [32.6850, -117.2186]
    ],
    "Sunset Cliffs": [
        [32.7150, -117.2550],
        [32.7150, -117.2350],
        [32.7050, -117.2350],
        [32.7050, -117.2550]
    ],
    "Liberty Station": [
        [32.7350, -117.2150],
        [32.7350, -117.1950],
        [32.7250, -117.1950],
        [32.7250, -117.2150]
    ],
    "Point Loma Village": [
        [32.7450, -117.2350],
        [32.7450, -117.2150],
        [32.7350, -117.2150],
        [32.7350, -117.2350]
    ]
}

def load_districts():
    """Load districts from file, or use defaults if file doesn't exist"""
    try:
        if os.path.exists(DISTRICTS_FILE):
            with open(DISTRICTS_FILE, 'r') as f:
                districts = json.load(f)
                print(f"Loaded {len(districts)} districts from {DISTRICTS_FILE}")
                return districts
        else:
            print("No districts file found, using defaults")
            return DEFAULT_DISTRICTS.copy()
    except Exception as e:
        print(f"Error loading districts file: {e}")
        print("Using default districts")
        return DEFAULT_DISTRICTS.copy()

def save_districts(districts):
    """Save districts to file"""
    try:
        with open(DISTRICTS_FILE, 'w') as f:
            json.dump(districts, f, indent=2)
        print(f"Saved {len(districts)} districts to {DISTRICTS_FILE}")
        return True
    except Exception as e:
        print(f"Error saving districts file: {e}")
        return False

# Load districts at startup
DISTRICTS = load_districts()

def point_in_polygon(lat, lng, polygon):
    """
    Improved ray casting algorithm to determine if a point is inside a polygon.
    polygon: list of [lat, lng] coordinates
    """
    if len(polygon) < 3:
        return False
    
    x, y = lng, lat
    n = len(polygon)
    inside = False
    
    # Use the standard ray casting algorithm
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i][1], polygon[i][0]  # lng, lat
        xj, yj = polygon[j][1], polygon[j][0]  # lng, lat
        
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    
    return inside

def get_district(lat, lng):
    """Determine which district a location belongs to using polygon containment"""
    print(f"Checking point ({lat}, {lng}) against {len(DISTRICTS)} districts")
    
    for district_name, polygon in DISTRICTS.items():
        try:
            is_inside = point_in_polygon(lat, lng, polygon)
            print(f"  District '{district_name}': {'INSIDE' if is_inside else 'outside'}")
            if is_inside:
                print(f"Point ({lat}, {lng}) found in district: {district_name}")
                return district_name
        except Exception as e:
            print(f"Error checking district '{district_name}': {e}")
            continue
    
    print(f"Point ({lat}, {lng}) is outside all districts")
    return "Outside Districts"

@app.route('/api/location', methods=['POST'])
def receive_location():
    try:
        data = request.get_json()
        username = data.get('username', 'unknown')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        if latitude is None or longitude is None:
            return jsonify({'error': 'Missing latitude or longitude'}), 400
        
        # Determine district using polygon containment
        district = get_district(latitude, longitude)
        
        with data_lock:
            location_data[username] = {
                'latitude': latitude,
                'longitude': longitude,
                'timestamp': timestamp,
                'district': district
            }
        
        print(f"Received location from {username}: {latitude}, {longitude} in {district}")
        return jsonify({'status': 'success', 'district': district})
    
    except Exception as e:
        print(f"Error processing location: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user_districts', methods=['GET'])
def get_user_districts():
    with data_lock:
        return jsonify(dict(location_data))

@app.route('/api/districts', methods=['GET'])
def get_districts():
    """Return districts data for mobile app"""
    return jsonify(DISTRICTS)

@app.route('/api/districts', methods=['POST'])
def update_districts():
    """Update district polygon definitions and save to file"""
    try:
        global DISTRICTS
        new_districts = request.get_json()
        
        # Validate the data structure
        for name, polygon in new_districts.items():
            if not isinstance(polygon, list) or len(polygon) < 3:
                return jsonify({'error': f'Invalid polygon for district {name}'}), 400
            for point in polygon:
                if not isinstance(point, list) or len(point) != 2:
                    return jsonify({'error': f'Invalid point in district {name}'}), 400
        
        DISTRICTS = new_districts
        
        # Save to file
        if not save_districts(DISTRICTS):
            return jsonify({'error': 'Failed to save districts to file'}), 500
        
        # Recalculate districts for all existing users
        with data_lock:
            for username, data in location_data.items():
                lat, lng = data['latitude'], data['longitude']
                data['district'] = get_district(lat, lng)
        
        return jsonify({'status': 'success', 'message': f'Saved {len(DISTRICTS)} districts to file'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/districts/reset', methods=['POST'])
def reset_districts():
    """Reset districts to defaults"""
    try:
        global DISTRICTS
        DISTRICTS = DEFAULT_DISTRICTS.copy()
        
        # Save to file
        if not save_districts(DISTRICTS):
            return jsonify({'error': 'Failed to save districts to file'}), 500
        
        # Recalculate districts for all existing users
        with data_lock:
            for username, data in location_data.items():
                lat, lng = data['latitude'], data['longitude']
                data['district'] = get_district(lat, lng)
        
        return jsonify({'status': 'success', 'message': 'Reset to default districts'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/point', methods=['POST'])
def debug_point():
    """Debug endpoint to test point-in-polygon detection"""
    try:
        data = request.get_json()
        lat = data.get('lat')
        lng = data.get('lng')
        
        if lat is None or lng is None:
            return jsonify({'error': 'Missing lat or lng parameters'}), 400
        
        results = {}
        for district_name, polygon in DISTRICTS.items():
            try:
                is_inside = point_in_polygon(lat, lng, polygon)
                results[district_name] = {
                    'inside': is_inside,
                    'polygon_points': len(polygon),
                    'first_point': polygon[0] if polygon else None,
                    'last_point': polygon[-1] if polygon else None
                }
            except Exception as e:
                results[district_name] = {
                    'error': str(e)
                }
        
        detected_district = get_district(lat, lng)
        
        return jsonify({
            'point': {'lat': lat, 'lng': lng},
            'detected_district': detected_district,
            'all_results': results
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def dashboard():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Location Tracker Dashboard</title>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { display: flex; gap: 20px; }
        .sidebar { width: 300px; }
        .map-container { flex: 1; height: 600px; }
        #map { height: 100%; width: 100%; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .controls { margin-bottom: 20px; }
        button { padding: 10px 15px; margin: 5px; cursor: pointer; }
        .drawing-mode { background-color: #4CAF50; color: white; }
        .editing-mode { background-color: #2196F3; color: white; }
        .district-list { margin-top: 20px; }
        .district-item { margin: 5px 0; padding: 5px; border: 1px solid #ccc; display: flex; justify-content: space-between; align-items: center; }
        .district-item.selected { background-color: #e3f2fd; border-color: #2196F3; }
        .delete-btn { background-color: #f44336; color: white; border: none; padding: 2px 8px; margin-left: 5px; }
        .edit-btn { background-color: #2196F3; color: white; border: none; padding: 2px 8px; margin-left: 5px; }
        .reset-btn { background-color: #ff9800; color: white; }
        .file-info { font-size: 12px; color: #666; margin-top: 10px; }
        .editor-info { font-size: 12px; color: #2196F3; margin-top: 10px; padding: 10px; background-color: #e3f2fd; border-radius: 4px; display: none; }
        select { padding: 5px; margin: 5px; width: 200px; }
    </style>
</head>
<body>
    <h1>Location Tracker Dashboard with Polygon Districts</h1>
    
    <div class="container">
        <div class="sidebar">
            <div class="controls">
                <button id="drawBtn" onclick="toggleDrawing()">Start Drawing District</button>
                <button onclick="clearDrawing()">Clear Current Drawing</button>
                <button onclick="saveDistricts()">Save All Districts</button>
                <button class="reset-btn" onclick="resetDistricts()">Reset to Defaults</button>
                <input type="text" id="districtName" placeholder="District name..." />
                <div class="file-info">
                    Districts are automatically saved to districts.json
                </div>
            </div>
            
            <div class="controls">
                <h4>District Editor:</h4>
                <select id="districtSelector" onchange="selectDistrictForEditing()">
                    <option value="">Select district to edit...</option>
                </select>
                <button id="editBtn" onclick="toggleEditing()" disabled>Edit Selected District</button>
                <button onclick="finishEditing()" id="finishEditBtn" style="display: none;">Finish Editing</button>
                <div class="editor-info" id="editorInfo">
                    Click and drag the red circles to move boundary points. 
                    Right-click a point to delete it. 
                    Click on the polygon edge to add a new point.
                </div>
            </div>
            
            <div class="district-list">
                <h3>Districts:</h3>
                <div id="districtsList"></div>
            </div>
            
            <h3>User Locations:</h3>
            <table id="locationTable">
                <thead>
                    <tr>
                        <th>User</th>
                        <th>District</th>
                        <th>Coordinates</th>
                        <th>Time</th>
                    </tr>
                </thead>
                <tbody id="locationData">
                </tbody>
            </table>
            
            <div style="margin-bottom: 20px;">
                <h3>Add Test User</h3>
                <input type="text" id="testUsername" placeholder="Username (optional)" style="margin-right: 10px; padding: 5px;">
                <button onclick="addTestUser()" style="padding: 5px 10px; background-color: #4CAF50; color: white; border: none; border-radius: 3px; cursor: pointer;">Add Random User</button>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h3>Districts</h3>
            </div>
        </div>
        
        <div class="map-container">
            <div id="map"></div>
        </div>
    </div>

    <script>
        // Initialize map centered on Point Loma
        const map = L.map('map').setView([32.72, -117.22], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        
        let districts = {};
        let userMarkers = {};
        let districtLayers = {};
        let isDrawing = false;
        let isEditing = false;
        let currentPolygon = null;
        let currentPoints = [];
        let selectedDistrict = null;
        let editingMarkers = [];
        let editingPolygon = null;
        
        // Load initial districts
        loadDistricts();
        
        function loadDistricts() {
            fetch('/api/districts')
                .then(response => response.json())
                .then(data => {
                    districts = data;
                    updateDistrictsDisplay();
                    updateDistrictsList();
                    updateDistrictSelector();
                });
        }
        
        function updateDistrictsDisplay() {
            // Clear existing district layers
            Object.values(districtLayers).forEach(layer => map.removeLayer(layer));
            districtLayers = {};
            
            // Add district polygons to map
            Object.entries(districts).forEach(([name, coordinates]) => {
                if (name === selectedDistrict && isEditing) {
                    // Don't show the regular polygon for the district being edited
                    return;
                }
                
                const polygon = L.polygon(coordinates.map(coord => [coord[0], coord[1]]), {
                    color: getRandomColor(),
                    fillOpacity: 0.3
                }).addTo(map);
                
                polygon.bindPopup(name);
                districtLayers[name] = polygon;
            });
        }
        
        function updateDistrictsList() {
            const list = document.getElementById('districtsList');
            list.innerHTML = '';
            
            Object.keys(districts).forEach(name => {
                const div = document.createElement('div');
                div.className = 'district-item' + (name === selectedDistrict ? ' selected' : '');
                div.innerHTML = `
                    <span>${name}</span>
                    <div>
                        <button class="edit-btn" onclick="selectDistrictForEditingByName('${name}')">Edit</button>
                        <button class="delete-btn" onclick="deleteDistrict('${name}')">Delete</button>
                    </div>
                `;
                list.appendChild(div);
            });
        }
        
        function updateDistrictSelector() {
            const selector = document.getElementById('districtSelector');
            selector.innerHTML = '<option value="">Select district to edit...</option>';
            
            Object.keys(districts).forEach(name => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                if (name === selectedDistrict) {
                    option.selected = true;
                }
                selector.appendChild(option);
            });
        }
        
        function selectDistrictForEditing() {
            const selector = document.getElementById('districtSelector');
            selectedDistrict = selector.value;
            
            const editBtn = document.getElementById('editBtn');
            editBtn.disabled = !selectedDistrict;
            
            updateDistrictsList();
            
            if (isEditing && selectedDistrict) {
                startEditingDistrict();
            }
        }
        
        function selectDistrictForEditingByName(name) {
            selectedDistrict = name;
            const selector = document.getElementById('districtSelector');
            selector.value = name;
            
            const editBtn = document.getElementById('editBtn');
            editBtn.disabled = false;
            
            updateDistrictsList();
        }
        
        function toggleEditing() {
            if (!selectedDistrict) return;
            
            isEditing = !isEditing;
            
            if (isEditing) {
                startEditingDistrict();
            } else {
                finishEditing();
            }
        }
        
        function startEditingDistrict() {
            if (!selectedDistrict || !districts[selectedDistrict]) return;
            
            isEditing = true;
            
            // Update UI
            document.getElementById('editBtn').style.display = 'none';
            document.getElementById('finishEditBtn').style.display = 'inline-block';
            document.getElementById('editorInfo').style.display = 'block';
            
            // Clear any existing editing elements
            clearEditingElements();
            
            // Hide the regular polygon for this district
            if (districtLayers[selectedDistrict]) {
                map.removeLayer(districtLayers[selectedDistrict]);
                delete districtLayers[selectedDistrict];
            }
            
            // Create editable polygon
            const coordinates = districts[selectedDistrict];
            editingPolygon = L.polygon(coordinates.map(coord => [coord[0], coord[1]]), {
                color: '#FF0000',
                fillOpacity: 0.2,
                weight: 2
            }).addTo(map);
            
            // Add draggable markers for each point
            coordinates.forEach((coord, index) => {
                const marker = L.circleMarker([coord[0], coord[1]], {
                    radius: 8,
                    color: '#FF0000',
                    fillColor: '#FF0000',
                    fillOpacity: 0.8,
                    draggable: true
                }).addTo(map);
                
                // Handle marker drag
                marker.on('drag', function(e) {
                    updatePolygonPoint(index, e.target.getLatLng());
                });
                
                marker.on('dragend', function(e) {
                    savePointChange(index, e.target.getLatLng());
                });
                
                // Handle right-click to delete point
                marker.on('contextmenu', function(e) {
                    e.originalEvent.preventDefault();
                    deletePolygonPoint(index);
                });
                
                editingMarkers.push(marker);
            });
            
            // Handle clicks on polygon edges to add new points
            editingPolygon.on('click', function(e) {
                addPolygonPoint(e.latlng);
            });
        }
        
        function updatePolygonPoint(index, newLatLng) {
            districts[selectedDistrict][index] = [newLatLng.lat, newLatLng.lng];
            
            // Update the polygon
            const coordinates = districts[selectedDistrict];
            editingPolygon.setLatLngs(coordinates.map(coord => [coord[0], coord[1]]));
        }
        
        function savePointChange(index, newLatLng) {
            districts[selectedDistrict][index] = [newLatLng.lat, newLatLng.lng];
            // Auto-save could be added here if desired
        }
        
        function deletePolygonPoint(index) {
            if (districts[selectedDistrict].length <= 3) {
                alert('Cannot delete point - polygon must have at least 3 points');
                return;
            }
            
            // Remove the point
            districts[selectedDistrict].splice(index, 1);
            
            // Restart editing to refresh markers
            finishEditing();
            setTimeout(() => startEditingDistrict(), 100);
        }
        
        function addPolygonPoint(latlng) {
            const coordinates = districts[selectedDistrict];
            
            // Find the best position to insert the new point
            let insertIndex = coordinates.length;
            let minDistance = Infinity;
            
            for (let i = 0; i < coordinates.length; i++) {
                const nextIndex = (i + 1) % coordinates.length;
                const point1 = L.latLng(coordinates[i][0], coordinates[i][1]);
                const point2 = L.latLng(coordinates[nextIndex][0], coordinates[nextIndex][1]);
                
                // Calculate distance from clicked point to line segment
                const distance = distanceToLineSegment(latlng, point1, point2);
                
                if (distance < minDistance) {
                    minDistance = distance;
                    insertIndex = nextIndex;
                }
            }
            
            // Insert the new point
            districts[selectedDistrict].splice(insertIndex, 0, [latlng.lat, latlng.lng]);
            
            // Restart editing to refresh markers
            finishEditing();
            setTimeout(() => startEditingDistrict(), 100);
        }
        
        function distanceToLineSegment(point, lineStart, lineEnd) {
            // Simplified distance calculation
            const A = point.distanceTo(lineStart);
            const B = point.distanceTo(lineEnd);
            const C = lineStart.distanceTo(lineEnd);
            
            if (C === 0) return A;
            
            const t = Math.max(0, Math.min(1, ((point.lat - lineStart.lat) * (lineEnd.lat - lineStart.lat) + 
                                                (point.lng - lineStart.lng) * (lineEnd.lng - lineStart.lng)) / (C * C)));
            
            const projection = L.latLng(
                lineStart.lat + t * (lineEnd.lat - lineStart.lat),
                lineStart.lng + t * (lineEnd.lng - lineStart.lng)
            );
            
            return point.distanceTo(projection);
        }
        
        function finishEditing() {
            isEditing = false;
            
            // Update UI
            document.getElementById('editBtn').style.display = 'inline-block';
            document.getElementById('finishEditBtn').style.display = 'none';
            document.getElementById('editorInfo').style.display = 'none';
            
            // Clear editing elements
            clearEditingElements();
            
            // Restore normal district display
            updateDistrictsDisplay();
            updateDistrictsList();
        }
        
        function clearEditingElements() {
            // Remove editing markers
            editingMarkers.forEach(marker => map.removeLayer(marker));
            editingMarkers = [];
            
            // Remove editing polygon
            if (editingPolygon) {
                map.removeLayer(editingPolygon);
                editingPolygon = null;
            }
        }
        
        function getRandomColor() {
            const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8'];
            return colors[Math.floor(Math.random() * colors.length)];
        }
        
        function toggleDrawing() {
            if (isEditing) {
                alert('Please finish editing the current district first');
                return;
            }
            
            isDrawing = !isDrawing;
            const btn = document.getElementById('drawBtn');
            
            if (isDrawing) {
                btn.textContent = 'Stop Drawing';
                btn.className = 'drawing-mode';
                map.on('click', onMapClick);
            } else {
                btn.textContent = 'Start Drawing District';
                btn.className = '';
                map.off('click', onMapClick);
                finishDrawing();
            }
        }
        
        function onMapClick(e) {
            if (!isDrawing) return;
            
            const lat = e.latlng.lat;
            const lng = e.latlng.lng;
            currentPoints.push([lat, lng]);
            
            if (currentPolygon) {
                map.removeLayer(currentPolygon);
            }
            
            if (currentPoints.length >= 3) {
                currentPolygon = L.polygon(currentPoints, {
                    color: '#FF0000',
                    fillOpacity: 0.3
                }).addTo(map);
            } else {
                // Show points being drawn
                L.circleMarker([lat, lng], {radius: 3, color: 'red'}).addTo(map);
            }
        }
        
        function finishDrawing() {
            if (currentPoints.length >= 3) {
                const name = document.getElementById('districtName').value.trim();
                if (name) {
                    districts[name] = currentPoints.slice(); // Copy array
                    updateDistrictsDisplay();
                    updateDistrictsList();
                    updateDistrictSelector();
                    document.getElementById('districtName').value = '';
                } else {
                    alert('Please enter a district name');
                }
            }
            clearDrawing();
        }
        
        function clearDrawing() {
            if (currentPolygon) {
                map.removeLayer(currentPolygon);
                currentPolygon = null;
            }
            currentPoints = [];
        }
        
        function deleteDistrict(name) {
            if (confirm(`Delete district "${name}"?`)) {
                if (name === selectedDistrict) {
                    finishEditing();
                    selectedDistrict = null;
                }
                delete districts[name];
                updateDistrictsDisplay();
                updateDistrictsList();
                updateDistrictSelector();
            }
        }
        
        function saveDistricts() {
            fetch('/api/districts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(districts)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('Districts saved successfully to districts.json!');
                    updateUserLocations(); // Refresh to show updated districts
                } else {
                    alert('Error saving districts: ' + data.error);
                }
            });
        }
        
        function resetDistricts() {
            if (confirm('Reset all districts to defaults? This will delete your custom districts.')) {
                finishEditing();
                selectedDistrict = null;
                
                fetch('/api/districts/reset', {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        alert('Districts reset to defaults!');
                        loadDistricts(); // Reload districts
                        updateUserLocations(); // Refresh user locations
                    } else {
                        alert('Error resetting districts: ' + data.error);
                    }
                });
            }
        }
        
        function updateUserLocations() {
            fetch('/api/user_districts')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('locationData');
                    tbody.innerHTML = '';
                    
                    // Clear existing user markers
                    Object.values(userMarkers).forEach(marker => map.removeLayer(marker));
                    userMarkers = {};
                    
                    Object.entries(data).forEach(([username, info]) => {
                        // Add to table
                        const row = tbody.insertRow();
                        row.insertCell(0).textContent = username;
                        row.insertCell(1).textContent = info.district;
                        row.insertCell(2).textContent = `${info.latitude.toFixed(6)}, ${info.longitude.toFixed(6)}`;
                        row.insertCell(3).textContent = new Date(info.timestamp).toLocaleTimeString();
                        
                        // Add marker to map
                        const marker = L.marker([info.latitude, info.longitude])
                            .bindPopup(`${username}<br/>District: ${info.district}`)
                            .addTo(map);
                        userMarkers[username] = marker;
                    });
                });
        }
        
        // Update user locations every 10 seconds
        setInterval(updateUserLocations, 10000);
        updateUserLocations(); // Initial load

        // Add test user function
        async function addTestUser() {
            const username = document.getElementById('testUsername').value || '';
            
            try {
                const response = await fetch('/api/add_test_user', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username: username })
                });
                
                const result = await response.json();
                if (result.status === 'success') {
                    console.log('Added test user:', result.username);
                    document.getElementById('testUsername').value = '';
                    // Refresh the data
                    updateUserLocations();
                }
            } catch (error) {
                console.error('Error adding test user:', error);
            }
        }
        
        // Auto-refresh every 5 seconds
    </script>
</body>
</html>
    ''')

@app.route('/api/add_test_user', methods=['POST'])
def add_test_user():
    data = request.json
    username = data.get('username', f'testuser_{len(location_data) + 1}')
    
    # Predefined test locations in different districts
    test_locations = [
        {"lat": 32.7157, "lng": -117.1611, "district": "wooded-area"},  # Wooded area
        {"lat": 32.7280, "lng": -117.1950, "district": "catalina"},     # Catalina
        {"lat": 32.7045, "lng": -117.1500, "district": "plnu-top"},    # PLNU top
        {"lat": 32.7200, "lng": -117.1700, "district": "upper-wooded"}, # Upper wooded
        {"lat": 32.7150, "lng": -117.2400, "district": "sunset-cliffs-south"}, # Sunset cliffs
        {"lat": 32.7350, "lng": -117.1800, "district": "midway-north"}, # Midway north
        {"lat": 32.7100, "lng": -117.1900, "district": "liberty-station-east"}, # Liberty station
    ]
    
    # Pick a random test location
    location = random.choice(test_locations)
    
    with data_lock:
        location_data[username] = {
            'lat': location['lat'],
            'lng': location['lng'],
            'timestamp': datetime.now().isoformat(),
            'district': get_district(location['lat'], location['lng'])
        }
    
    return jsonify({
        'status': 'success',
        'username': username,
        'location': location_data[username]
    })

if __name__ == '__main__':
    print("Starting Location Tracker Server with Polygon Districts...")
    print("Dashboard available at: http://localhost:5001")
    print("Location API endpoint: http://localhost:5001/api/location")
    print(f"Districts will be saved to: {DISTRICTS_FILE}")
    app.run(host='0.0.0.0', port=5001, debug=True) 