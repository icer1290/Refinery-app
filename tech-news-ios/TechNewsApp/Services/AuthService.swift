import Foundation

class AuthService {
    private let client = APIClient.shared

    func login(email: String, password: String) async throws -> AuthResponse.AuthData? {
        let request = LoginRequest(email: email, password: password)
        let response: AuthResponse = try await client.post(Constants.Endpoints.login(), body: request)

        if let authData = response.data {
            client.authToken = authData.token
            client.userEmail = authData.email
            client.userId = authData.userId
            return authData
        }
        return nil
    }

    func register(email: String, password: String, nickname: String?) async throws -> AuthResponse.AuthData? {
        let request = RegisterRequest(email: email, password: password, nickname: nickname)
        let response: AuthResponse = try await client.post(Constants.Endpoints.register(), body: request)

        if let authData = response.data {
            client.authToken = authData.token
            client.userEmail = authData.email
            client.userId = authData.userId
            return authData
        }
        return nil
    }

    func logout() {
        client.clearAuth()
    }

    func isLoggedIn() -> Bool {
        return client.authToken != nil
    }
}

// MARK: - Request Models

struct LoginRequest: Encodable {
    let email: String
    let password: String
}

struct RegisterRequest: Encodable {
    let email: String
    let password: String
    let nickname: String?
}
