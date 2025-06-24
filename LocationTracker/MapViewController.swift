import UIKit
import MapKit

class MapViewController: UIViewController {
    private let mapView = MKMapView()
    private let backButton = UIButton(type: .system)
    private var districts: [String: [[Double]]] = [:]
    private var userLocations: [String: UserLocationData] = [:]
    private var refreshTimer: Timer?
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupMapView()
        loadDistrictsAndUsers()
        startAutoRefresh()
    }
    
    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        refreshTimer?.invalidate()
    }
    
    private func setupUI() {
        view.backgroundColor = .systemBackground
        
        // Setup map view
        mapView.translatesAutoresizingMaskIntoConstraints = false
        mapView.delegate = self
        view.addSubview(mapView)
        
        // Setup back button
        backButton.setTitle("← Back", for: .normal)
        backButton.titleLabel?.font = UIFont.systemFont(ofSize: 16, weight: .medium)
        backButton.addTarget(self, action: #selector(backTapped), for: .touchUpInside)
        backButton.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(backButton)
        
        NSLayoutConstraint.activate([
            backButton.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 10),
            backButton.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 20),
            
            mapView.topAnchor.constraint(equalTo: backButton.bottomAnchor, constant: 10),
            mapView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            mapView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            mapView.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])
    }
    
    private func setupMapView() {
        // Center on Point Loma area
        let pointLomaCenter = CLLocationCoordinate2D(latitude: 32.7157, longitude: -117.1900)
        let region = MKCoordinateRegion(center: pointLomaCenter, latitudinalMeters: 5000, longitudinalMeters: 5000)
        mapView.setRegion(region, animated: false)
        mapView.mapType = .standard
        mapView.showsUserLocation = true
    }
    
    @objc private func backTapped() {
        dismiss(animated: true)
    }
    
    private func loadDistrictsAndUsers() {
        loadDistricts()
        loadUserLocations()
    }
    
    private func loadDistricts() {
        guard let url = URL(string: "http://localhost:5001/api/districts") else { return }
        
        URLSession.shared.dataTask(with: url) { [weak self] data, response, error in
            guard let data = data, error == nil else {
                print("Error loading districts: \(error?.localizedDescription ?? "Unknown error")")
                return
            }
            
            do {
                let districts = try JSONSerialization.jsonObject(with: data) as? [String: [[Double]]] ?? [:]
                DispatchQueue.main.async {
                    self?.districts = districts
                    self?.displayDistricts()
                }
            } catch {
                print("Error parsing districts: \(error)")
            }
        }.resume()
    }
    
    private func loadUserLocations() {
        guard let url = URL(string: "http://localhost:5001/api/user_districts") else { return }
        
        URLSession.shared.dataTask(with: url) { [weak self] data, response, error in
            guard let data = data, error == nil else {
                print("Error loading user locations: \(error?.localizedDescription ?? "Unknown error")")
                return
            }
            
            do {
                let users = try JSONDecoder().decode([String: UserLocationData].self, from: data)
                DispatchQueue.main.async {
                    self?.userLocations = users
                    self?.displayUserLocations()
                }
            } catch {
                print("Error parsing user locations: \(error)")
            }
        }.resume()
    }
    
    private func displayDistricts() {
        // Remove existing overlays
        mapView.removeOverlays(mapView.overlays)
        
        for (districtName, coordinates) in districts {
            let polygonCoordinates = coordinates.map { coord in
                CLLocationCoordinate2D(latitude: coord[0], longitude: coord[1])
            }
            
            let polygon = MKPolygon(coordinates: polygonCoordinates, count: polygonCoordinates.count)
            polygon.title = districtName
            mapView.addOverlay(polygon)
        }
    }
    
    private func displayUserLocations() {
        // Remove existing annotations (except user location)
        let annotationsToRemove = mapView.annotations.filter { !($0 is MKUserLocation) }
        mapView.removeAnnotations(annotationsToRemove)
        
        // Group users by district
        var usersByDistrict: [String: [String]] = [:]
        
        for (username, userData) in userLocations {
            if usersByDistrict[userData.district] == nil {
                usersByDistrict[userData.district] = []
            }
            usersByDistrict[userData.district]?.append(username)
        }
        
        // Create annotations for each district at the center of the polygon
        for (districtName, users) in usersByDistrict {
            guard let districtCoordinates = districts[districtName] else { continue }
            
            // Calculate center of polygon
            let center = calculatePolygonCenter(coordinates: districtCoordinates)
            
            let annotation = DistrictUserAnnotation()
            annotation.coordinate = center
            annotation.title = districtName
            annotation.users = users
            
            mapView.addAnnotation(annotation)
        }
    }
    
    private func calculatePolygonCenter(coordinates: [[Double]]) -> CLLocationCoordinate2D {
        guard !coordinates.isEmpty else {
            return CLLocationCoordinate2D(latitude: 32.7157, longitude: -117.1900) // Default Point Loma center
        }
        
        var totalLat = 0.0
        var totalLng = 0.0
        
        for coordinate in coordinates {
            totalLat += coordinate[0] // latitude
            totalLng += coordinate[1] // longitude
        }
        
        let centerLat = totalLat / Double(coordinates.count)
        let centerLng = totalLng / Double(coordinates.count)
        
        return CLLocationCoordinate2D(latitude: centerLat, longitude: centerLng)
    }
    
    private func startAutoRefresh() {
        refreshTimer = Timer.scheduledTimer(withTimeInterval: 10.0, repeats: true) { [weak self] _ in
            self?.loadUserLocations()
        }
    }
}

// MARK: - MKMapViewDelegate
extension MapViewController: MKMapViewDelegate {
    func mapView(_ mapView: MKMapView, rendererFor overlay: MKOverlay) -> MKOverlayRenderer {
        if let polygon = overlay as? MKPolygon {
            let renderer = MKPolygonRenderer(polygon: polygon)
            renderer.fillColor = UIColor.systemBlue.withAlphaComponent(0.2)
            renderer.strokeColor = UIColor.systemBlue
            renderer.lineWidth = 2
            return renderer
        }
        return MKOverlayRenderer(overlay: overlay)
    }
    
    func mapView(_ mapView: MKMapView, viewFor annotation: MKAnnotation) -> MKAnnotationView? {
        if annotation is MKUserLocation {
            return nil // Use default user location view
        }
        
        guard let districtAnnotation = annotation as? DistrictUserAnnotation else {
            return nil
        }
        
        let identifier = "DistrictUser"
        var annotationView = mapView.dequeueReusableAnnotationView(withIdentifier: identifier)
        
        if annotationView == nil {
            annotationView = MKAnnotationView(annotation: annotation, reuseIdentifier: identifier)
            annotationView?.canShowCallout = true
        } else {
            annotationView?.annotation = annotation
        }
        
        // Create custom view for the annotation
        let containerView = UIView(frame: CGRect(x: 0, y: 0, width: 160, height: 70))
        containerView.backgroundColor = UIColor.systemBlue.withAlphaComponent(0.9)
        containerView.layer.cornerRadius = 10
        containerView.layer.borderWidth = 2
        containerView.layer.borderColor = UIColor.white.cgColor
        
        let districtLabel = UILabel(frame: CGRect(x: 5, y: 5, width: 150, height: 20))
        districtLabel.text = districtAnnotation.title?.replacingOccurrences(of: "-", with: " ").capitalized
        districtLabel.font = UIFont.boldSystemFont(ofSize: 14)
        districtLabel.textAlignment = .center
        districtLabel.textColor = .white
        districtLabel.adjustsFontSizeToFitWidth = true
        districtLabel.minimumScaleFactor = 0.8
        containerView.addSubview(districtLabel)
        
        let usersLabel = UILabel(frame: CGRect(x: 5, y: 25, width: 150, height: 40))
        usersLabel.text = districtAnnotation.users.joined(separator: ", ")
        usersLabel.font = UIFont.systemFont(ofSize: 11, weight: .medium)
        usersLabel.textAlignment = .center
        usersLabel.numberOfLines = 3
        usersLabel.textColor = .white
        usersLabel.adjustsFontSizeToFitWidth = true
        usersLabel.minimumScaleFactor = 0.7
        containerView.addSubview(usersLabel)
        
        // Convert view to image for annotation
        UIGraphicsBeginImageContextWithOptions(containerView.bounds.size, false, 0)
        containerView.layer.render(in: UIGraphicsGetCurrentContext()!)
        let image = UIGraphicsGetImageFromCurrentImageContext()
        UIGraphicsEndImageContext()
        
        annotationView?.image = image
        annotationView?.centerOffset = CGPoint(x: 0, y: -35)
        
        return annotationView
    }
}

// MARK: - Custom Annotation
class DistrictUserAnnotation: NSObject, MKAnnotation {
    var coordinate: CLLocationCoordinate2D = CLLocationCoordinate2D()
    var title: String?
    var users: [String] = []
} 