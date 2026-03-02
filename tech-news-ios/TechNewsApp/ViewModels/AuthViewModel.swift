import Foundation
import SwiftUI

@MainActor
class AuthViewModel: ObservableObject {
    @Published var isAuthenticated = false
    @Published var userEmail: String?
    @Published var userId: Int?
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let authService = AuthService()

    init() {
        checkAuthStatus()
    }

    func checkAuthStatus() {
        isAuthenticated = authService.isLoggedIn()
        if isAuthenticated {
            userEmail = APIClient.shared.userEmail
            userId = APIClient.shared.userId
        }
    }

    func login(email: String, password: String) async {
        isLoading = true
        errorMessage = nil

        do {
            let authData = try await authService.login(email: email, password: password)
            if authData != nil {
                isAuthenticated = true
                userEmail = authData?.email
                userId = authData?.userId
            } else {
                errorMessage = "Login failed"
            }
        } catch {
            errorMessage = error.localizedDescription
        }

        isLoading = false
    }

    func register(email: String, password: String, nickname: String?) async {
        isLoading = true
        errorMessage = nil

        do {
            let authData = try await authService.register(email: email, password: password, nickname: nickname)
            if authData != nil {
                isAuthenticated = true
                userEmail = authData?.email
                userId = authData?.userId
            } else {
                errorMessage = "Registration failed"
            }
        } catch {
            errorMessage = error.localizedDescription
        }

        isLoading = false
    }

    func logout() {
        authService.logout()
        isAuthenticated = false
        userEmail = nil
        userId = nil
    }
}
