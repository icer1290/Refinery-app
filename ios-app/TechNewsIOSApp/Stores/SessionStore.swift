import Foundation
import SwiftUI

@MainActor
final class SessionStore: ObservableObject {
    @Published private(set) var session: AuthSession?
    @Published var authSheetPresented = false
    @Published var authErrorMessage: String?
    @Published var isSubmitting = false

    private let client: APIClient
    private let storageKey = "saved-auth-session"

    init(client: APIClient) {
        self.client = client
        restoreSession()
    }

    var token: String? { session?.token }
    var isAuthenticated: Bool { session != nil }

    func presentAuthSheet() {
        authSheetPresented = true
    }

    func dismissAuthSheet() {
        authSheetPresented = false
        authErrorMessage = nil
    }

    func login(email: String, password: String) async -> Bool {
        await authenticate(path: "api/auth/login", body: LoginRequest(email: email, password: password))
    }

    func register(email: String, password: String, nickname: String) async -> Bool {
        await authenticate(
            path: "api/auth/register",
            body: RegisterRequest(email: email, password: password, nickname: nickname)
        )
    }

    func logout() {
        session = nil
        authErrorMessage = nil
        KeychainStore.deleteToken()
        UserDefaults.standard.removeObject(forKey: storageKey)
    }

    private func authenticate<T: Encodable>(path: String, body: T) async -> Bool {
        isSubmitting = true
        authErrorMessage = nil
        defer { isSubmitting = false }

        do {
            let response: AuthSession = try await client.request(
                path: path,
                method: "POST",
                body: AnyEncodable(body)
            )
            session = response
            persistSession(response)
            authSheetPresented = false
            return true
        } catch {
            authErrorMessage = error.localizedDescription
            return false
        }
    }

    private func persistSession(_ session: AuthSession) {
        KeychainStore.saveToken(session.token)
        if let encoded = try? JSONEncoder().encode(session) {
            UserDefaults.standard.set(encoded, forKey: storageKey)
        }
    }

    private func restoreSession() {
        guard
            let data = UserDefaults.standard.data(forKey: storageKey),
            var storedSession = try? JSONDecoder().decode(AuthSession.self, from: data)
        else {
            return
        }

        if let token = KeychainStore.loadToken() {
            storedSession = AuthSession(
                token: token,
                email: storedSession.email,
                nickname: storedSession.nickname,
                userID: storedSession.userID
            )
        }

        session = storedSession
    }
}
