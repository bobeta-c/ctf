# Location Tracker iOS App

iOS app that allows user to play large scale capture the flag with friends
## Features

- **Secure Authentication**: Login system with username/password
- **Location Tracking**: Uses Core Location to track user's location
- **Server Communication**: Sends location data to remote server
- **Privacy Focused**: Requests proper location permissions
- **Real-time Updates**: Automatically sends location updates every 30 seconds

## Architecture

### Key Components

1. **LoginViewController**: Handles user authentication
2. **ViewController**: Main app interface showing location tracking status
3. **LocationManager**: Manages Core Location services and permissions
4. **NetworkManager**: Handles all server communication

### File Structure

```
LocationTracker/
├── AppDelegate.swift              # App lifecycle management
├── SceneDelegate.swift           # Scene lifecycle management
├── LoginViewController.swift     # User authentication UI
├── ViewController.swift          # Main location tracking UI
├── LocationManager.swift         # Location services manager
├── NetworkManager.swift          # Network communication manager
├── Main.storyboard              # UI layout
├── LaunchScreen.storyboard      # Launch screen
├── Info.plist                   # App configuration and permissions
└── Assets.xcassets/             # App assets
```

## Setup Instructions

### 1. Open in Xcode
- Open `LocationTracker.xcodeproj` in Xcode
- Ensure you have Xcode 14.0 or later installed
- Select a valid iOS development team in project settings

### 2. Configure Server URL
Update the `baseURL` in `NetworkManager.swift`:
```swift
private let baseURL = "https://your-actual-server.com/api"
```

### 3. Server API Endpoints

Your server should implement these endpoints:

#### Authentication Endpoint
```
POST /api/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}

Response:
{
  "token": "jwt_token_here",
  "success": true
}
```

#### Location Update Endpoint
```
POST /api/location
Authorization: Bearer jwt_token_here
Content-Type: application/json

{
  "latitude": 37.7749,
  "longitude": -122.4194,
  "accuracy": 5.0,
  "timestamp": "2024-01-15T10:30:00Z",
  "username": "user@example.com"
}

Response:
{
  "success": true
}
```

#### Server Updates Endpoint
```
GET /api/updates
Authorization: Bearer jwt_token_here

Response:
{
  "updates": [...],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Privacy & Permissions

The app requests the following permissions:
- **Location Services**: Required for location tracking
- **Network Access**: Required for server communication

All permissions are clearly explained to users with appropriate usage descriptions in `Info.plist`.

## Building and Running

1. **Development**: 
   - Open project in Xcode
   - Select your development team
   - Choose target device/simulator
   - Click Run

2. **Production**:
   - Update bundle identifier in project settings
   - Configure signing certificates
   - Archive and distribute via App Store Connect

## Security Features

- Secure password input with hidden text
- Token-based authentication
- HTTPS communication (when proper server URL is configured)
- Automatic logout functionality
- Local storage of minimal user data

## Location Tracking Details

- **Accuracy**: Best accuracy available (GPS when possible)
- **Update Frequency**: Every 30 seconds
- **Distance Filter**: Only updates when moved 10+ meters
- **Battery Optimization**: Uses efficient location tracking methods

## Troubleshooting

### Common Issues:

1. **Location Permission Denied**
   - Check iOS Settings > Privacy & Security > Location Services
   - Ensure app has location permission enabled

2. **Network Errors**
   - Verify server URL is correct
   - Check internet connection
   - Ensure server endpoints are implemented

3. **Build Errors**
   - Verify Xcode version compatibility
   - Check iOS deployment target (15.0+)
   - Ensure valid development team selected

## Development Notes

- Minimum iOS version: 15.0
- Development language: Swift 5.0
- Uses modern iOS frameworks: UIKit, CoreLocation, Foundation
- Follows MVC architecture pattern
- Implements proper memory management with weak references

## Next Steps

1. Configure your backend server with the required API endpoints
2. Update the `baseURL` in `NetworkManager.swift`
3. Test the app with your server implementation
4. Add additional features as needed (push notifications, offline storage, etc.)

## License

This project is provided as-is for educational and development purposes. 
