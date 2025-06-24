import UIKit

class LoginViewController: UIViewController {
    let usernameField = UITextField()
    let passwordField = UITextField()
    let loginButton = UIButton(type: .system)
    let statusLabel = UILabel()

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        setupUI()
    }

    func setupUI() {
        usernameField.placeholder = "Username"
        usernameField.borderStyle = .roundedRect
        usernameField.autocapitalizationType = .none
        usernameField.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(usernameField)

        passwordField.placeholder = "Password"
        passwordField.borderStyle = .roundedRect
        passwordField.isSecureTextEntry = true
        passwordField.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(passwordField)

        loginButton.setTitle("Login", for: .normal)
        loginButton.addTarget(self, action: #selector(loginTapped), for: .touchUpInside)
        loginButton.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(loginButton)

        statusLabel.textAlignment = .center
        statusLabel.textColor = .systemRed
        statusLabel.numberOfLines = 0
        statusLabel.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(statusLabel)

        NSLayoutConstraint.activate([
            usernameField.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            usernameField.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 120),
            usernameField.widthAnchor.constraint(equalToConstant: 250),
            passwordField.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            passwordField.topAnchor.constraint(equalTo: usernameField.bottomAnchor, constant: 20),
            passwordField.widthAnchor.constraint(equalToConstant: 250),
            loginButton.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            loginButton.topAnchor.constraint(equalTo: passwordField.bottomAnchor, constant: 30),
            loginButton.widthAnchor.constraint(equalToConstant: 200),
            statusLabel.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            statusLabel.topAnchor.constraint(equalTo: loginButton.bottomAnchor, constant: 20),
            statusLabel.widthAnchor.constraint(equalToConstant: 250)
        ])
    }

    @objc func loginTapped() {
        let username = usernameField.text ?? ""
        let password = passwordField.text ?? ""
        if username == "demo" && password == "password123" {
            statusLabel.textColor = .systemGreen
            statusLabel.text = "Login successful!"
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                let vc = ViewController()
                vc.modalPresentationStyle = .fullScreen
                self.present(vc, animated: true)
            }
        }
        else if username == "admin" && password == "password123" {
            statusLabel.textColor = .systemGreen
            statusLabel.text = "Login successful! (admin)"
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                let vc = ViewController()
                vc.modalPresentationStyle = .fullScreen
                self.present(vc, animated: true)
            }
        } else {
            statusLabel.textColor = .systemRed
            statusLabel.text = "Invalid credentials. Try demo/password123."
        }
    }
} 
