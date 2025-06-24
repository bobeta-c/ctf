//
//  ViewController.swift
//  LocationTracker
//
//  Created by oren tuchin on 6/23/25.
//

import UIKit
import CoreLocation

class ViewController: UIViewController, LocationManagerDelegate {
    let statusLabel = UILabel()
    let locationLabel = UILabel()
    let currentDistrictLabel = UILabel()
    let usernameTextField = UITextField()
    let userDistrictsLabel = UILabel()
    let scrollView = UIScrollView()
    let viewMapButton = UIButton(type: .system)
    let logoutButton = UIButton(type: .system)
    var username: String = "demo"
    var districtTimer: Timer?
    var currentDistrict: String = "Unknown"

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        setupUI()
        LocationManager.shared.delegate = self
        LocationManager.shared.requestPermission()
        LocationManager.shared.start()
        startDistrictUpdates()
    }

    func setupUI() {
        statusLabel.text = "Tracking location..."
        statusLabel.textAlignment = .center
        statusLabel.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(statusLabel)

        // Username input field
        usernameTextField.text = username
        usernameTextField.placeholder = "Enter username"
        usernameTextField.borderStyle = .roundedRect
        usernameTextField.textAlignment = .center
        usernameTextField.addTarget(self, action: #selector(usernameChanged), for: .editingChanged)
        usernameTextField.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(usernameTextField)

        locationLabel.text = "Location: --"
        locationLabel.textAlignment = .center
        locationLabel.numberOfLines = 0
        locationLabel.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(locationLabel)

        currentDistrictLabel.text = "Current District: Unknown"
        currentDistrictLabel.textAlignment = .center
        currentDistrictLabel.numberOfLines = 0
        currentDistrictLabel.font = UIFont.boldSystemFont(ofSize: 16)
        currentDistrictLabel.textColor = .systemBlue
        currentDistrictLabel.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(currentDistrictLabel)

        scrollView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(scrollView)

        userDistrictsLabel.text = "All Users & Districts:\nLoading..."
        userDistrictsLabel.numberOfLines = 0
        userDistrictsLabel.font = UIFont.systemFont(ofSize: 14)
        userDistrictsLabel.textAlignment = .left
        userDistrictsLabel.translatesAutoresizingMaskIntoConstraints = false
        scrollView.addSubview(userDistrictsLabel)

        viewMapButton.setTitle("🗺️ View Map", for: .normal)
        viewMapButton.titleLabel?.font = UIFont.systemFont(ofSize: 16, weight: .medium)
        viewMapButton.backgroundColor = UIColor.systemBlue
        viewMapButton.setTitleColor(.white, for: .normal)
        viewMapButton.layer.cornerRadius = 8
        viewMapButton.addTarget(self, action: #selector(viewMapTapped), for: .touchUpInside)
        viewMapButton.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(viewMapButton)

        logoutButton.setTitle("Logout", for: .normal)
        logoutButton.addTarget(self, action: #selector(logoutTapped), for: .touchUpInside)
        logoutButton.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(logoutButton)

        NSLayoutConstraint.activate([
            statusLabel.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 20),
            statusLabel.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            
            usernameTextField.topAnchor.constraint(equalTo: statusLabel.bottomAnchor, constant: 20),
            usernameTextField.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            usernameTextField.widthAnchor.constraint(equalToConstant: 200),
            
            locationLabel.topAnchor.constraint(equalTo: usernameTextField.bottomAnchor, constant: 20),
            locationLabel.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            
            currentDistrictLabel.topAnchor.constraint(equalTo: locationLabel.bottomAnchor, constant: 20),
            currentDistrictLabel.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            
            scrollView.topAnchor.constraint(equalTo: currentDistrictLabel.bottomAnchor, constant: 20),
            scrollView.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 20),
            scrollView.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -20),
            scrollView.bottomAnchor.constraint(equalTo: viewMapButton.topAnchor, constant: -20),
            
            userDistrictsLabel.topAnchor.constraint(equalTo: scrollView.topAnchor),
            userDistrictsLabel.leadingAnchor.constraint(equalTo: scrollView.leadingAnchor),
            userDistrictsLabel.trailingAnchor.constraint(equalTo: scrollView.trailingAnchor),
            userDistrictsLabel.bottomAnchor.constraint(equalTo: scrollView.bottomAnchor),
            userDistrictsLabel.widthAnchor.constraint(equalTo: scrollView.widthAnchor),
            
            viewMapButton.bottomAnchor.constraint(equalTo: logoutButton.topAnchor, constant: -10),
            viewMapButton.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            viewMapButton.widthAnchor.constraint(equalToConstant: 150),
            viewMapButton.heightAnchor.constraint(equalToConstant: 44),
            
            logoutButton.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor, constant: -20),
            logoutButton.centerXAnchor.constraint(equalTo: view.centerXAnchor)
        ])
    }
    
    func startDistrictUpdates() {
        fetchUserDistricts()
        districtTimer = Timer.scheduledTimer(withTimeInterval: 10.0, repeats: true) { [weak self] _ in
            self?.fetchUserDistricts()
        }
    }
    
    func fetchUserDistricts() {
        NetworkManager.shared.fetchUserDistricts { [weak self] districts in
            DispatchQueue.main.async {
                guard let self = self else { return }
                
                if let districts = districts, !districts.isEmpty {
                    // Update current user's district
                    if let myData = districts[self.username] {
                        self.currentDistrict = myData.district
                        self.currentDistrictLabel.text = "Current District: \(myData.district)"
                    }
                    
                    // Create formatted display of all users
                    let sortedUsers = districts.sorted { $0.key < $1.key }
                    var displayText = "All Users & Districts:\n\n"
                    
                    for (username, userData) in sortedUsers {
                        let timeFormatter = DateFormatter()
                        timeFormatter.timeStyle = .short
                        
                        // Try to parse the timestamp
                        let timeString: String
                        if let date = ISO8601DateFormatter().date(from: userData.timestamp) {
                            timeString = timeFormatter.string(from: date)
                        } else {
                            timeString = "Unknown"
                        }
                        
                        let isCurrentUser = username == self.username
                        let marker = isCurrentUser ? "👤 " : "📍 "
                        
                        displayText += "\(marker)\(username)\n"
                        displayText += "  District: \(userData.district)\n"
                        //displayText += "  Location: \(String(format: "%.4f", userData.latitude)), \(String(format: "%.4f", userData.longitude))\n"
                        displayText += "  Since: \(timeString)\n\n"
                    }
                    
                    self.userDistrictsLabel.text = displayText
                } else {
                    self.userDistrictsLabel.text = "All Users & Districts:\nNo users found"
                    self.currentDistrictLabel.text = "Current District: Unknown"
                }
            }
        }
    }

    func locationManager(_ manager: LocationManager, didUpdateLocation location: CLLocation) {
        locationLabel.text = String(format: "Location:\nLat: %.5f\nLon: %.5f\nAccuracy: %.1fm", location.coordinate.latitude, location.coordinate.longitude, location.horizontalAccuracy)
        statusLabel.text = "Sending location..."
        NetworkManager.shared.sendLocation(location, username: username) { [weak self] success in
            DispatchQueue.main.async {
                self?.statusLabel.text = success ? "Location sent!" : "Failed to send location"
            }
        }
    }
    
    func locationManager(_ manager: LocationManager, didFailWithError error: Error) {
        statusLabel.text = "Location error: \(error.localizedDescription)"
    }

    @objc func logoutTapped() {
        LocationManager.shared.stop()
        districtTimer?.invalidate()
        dismiss(animated: true)
    }

    @objc func usernameChanged() {
        if let newUsername = usernameTextField.text, !newUsername.isEmpty {
            username = newUsername
            print("Username changed to: \(username)")
        }
    }

    @objc func viewMapTapped() {
        let mapViewController = MapViewController()
        mapViewController.modalPresentationStyle = .fullScreen
        present(mapViewController, animated: true)
    }
}

