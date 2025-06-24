# Location Tracker Server Example

This is a simple Flask server that provides the backend API for the Location Tracker iOS app.

## Features

- User authentication with simple username/password
- Receive and store location updates from iOS app
- Provide server updates back to the app
- Simple token-based authentication

## Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   python app.py
   ```

3. **The server will start on:** `http://localhost:5000`

## API Endpoints

### 1. Login
```
POST /api/login
Content-Type: application/json

{
  "username": "demo",
  "password": "password123"
}
```

### 2. Send Location
```
POST /api/location
Authorization: Bearer <token>
Content-Type: application/json

{
  "latitude": 37.7749,
  "longitude": -122.4194,
  "accuracy": 5.0,
  "timestamp": "2024-01-15T10:30:00Z",
  "username": "demo"
}
```

### 3. Get Updates
```
GET /api/updates
Authorization: Bearer <token>
```

### 4. Server Status
```
GET /api/status
```

## Default Users

- Username: `demo`, Password: `password123`
- Username: `user@example.com`, Password: `securepass`

## Production Deployment

For production use, consider:

1. **Database**: Replace in-memory storage with a proper database (PostgreSQL, MySQL, etc.)
2. **Authentication**: Use JWT tokens or OAuth
3. **Security**: Add HTTPS, rate limiting, input validation
4. **Monitoring**: Add logging, metrics, and health checks
5. **Scalability**: Use proper WSGI server like Gunicorn

## Deploy to Heroku (Example)

1. Create a Heroku app
2. Add a `Procfile`:
   ```
   web: gunicorn app:app
   ```
3. Deploy the code
4. Update the iOS app's `baseURL` to your Heroku URL

## Testing

You can test the API using curl:

```bash
# Login
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "password123"}'

# Send location (replace TOKEN with actual token from login)
curl -X POST http://localhost:5000/api/location \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"latitude": 37.7749, "longitude": -122.4194, "accuracy": 5.0, "timestamp": "2024-01-15T10:30:00Z", "username": "demo"}'
``` 