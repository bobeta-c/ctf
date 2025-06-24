import Foundation
import CoreLocation

struct UserLocationData: Decodable {
    let latitude: Double
    let longitude: Double
    let timestamp: String
    let district: String
}

class NetworkManager {
    static let shared = NetworkManager()
    private let baseURL = "http://ctf-zefb.onrender.com" // Change to your server

    func sendLocation(_ location: CLLocation, username: String, completion: @escaping (Bool) -> Void) {
        guard let url = URL(string: "\(baseURL)/location") else { completion(false); return }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = [
            "latitude": location.coordinate.latitude,
            "longitude": location.coordinate.longitude,
            "accuracy": location.horizontalAccuracy,
            "timestamp": ISO8601DateFormatter().string(from: location.timestamp),
            "username": username
        ]
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)
        URLSession.shared.dataTask(with: req) { data, resp, err in
            if let data = data, let responseString = String(data: data, encoding: .utf8) {
                print("Server response: \(responseString)")
            }
            completion(err == nil)
        }.resume()
    }
    
    func fetchUserDistricts(completion: @escaping ([String: UserLocationData]?) -> Void) {
        guard let url = URL(string: "\(baseURL)/user_districts") else { 
            print("Invalid URL for user_districts")
            completion(nil)
            return 
        }
        
        URLSession.shared.dataTask(with: url) { data, resp, err in
            guard let data = data, err == nil else { 
                print("Network error: \(err?.localizedDescription ?? "Unknown error")")
                completion(nil)
                return 
            }
            
            do {
                if let responseString = String(data: data, encoding: .utf8) {
                    print("Raw server response: \(responseString)")
                }
                
                guard let json = try JSONSerialization.jsonObject(with: data) as? [String: [String: Any]] else {
                    print("Failed to parse JSON as expected format")
                    completion(nil)
                    return
                }
                
                var userDistricts: [String: UserLocationData] = [:]
                
                for (username, userData) in json {
                    guard let latitude = userData["latitude"] as? Double,
                          let longitude = userData["longitude"] as? Double,
                          let timestamp = userData["timestamp"] as? String,
                          let district = userData["district"] as? String else {
                        print("Invalid data format for user: \(username)")
                        continue
                    }
                    
                    userDistricts[username] = UserLocationData(
                        latitude: latitude,
                        longitude: longitude,
                        timestamp: timestamp,
                        district: district
                    )
                }
                
                print("Parsed \(userDistricts.count) users successfully")
                completion(userDistricts)
                
            } catch {
                print("JSON parsing error: \(error)")
                completion(nil)
            }
        }.resume()
    }
} 
