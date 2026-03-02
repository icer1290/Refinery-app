import Foundation

class APIClient {
    static let shared = APIClient()

    private let baseURL: String
    private let session: URLSession
    private let defaults = UserDefaults.standard

    private init() {
        self.baseURL = Constants.apiBaseURL
        self.session = URLSession.shared
    }

    var authToken: String? {
        get { defaults.string(forKey: Constants.StorageKeys.authToken) }
        set { defaults.set(newValue, forKey: Constants.StorageKeys.authToken) }
    }

    var userEmail: String? {
        get { defaults.string(forKey: Constants.StorageKeys.userEmail) }
        set { defaults.set(newValue, forKey: Constants.StorageKeys.userEmail) }
    }

    var userId: Int? {
        get { defaults.integer(forKey: Constants.StorageKeys.userId) }
        set { defaults.set(newValue, forKey: Constants.StorageKeys.userId) }
    }

    func clearAuth() {
        defaults.removeObject(forKey: Constants.StorageKeys.authToken)
        defaults.removeObject(forKey: Constants.StorageKeys.userEmail)
        defaults.removeObject(forKey: Constants.StorageKeys.userId)
    }

    // MARK: - Generic Request Methods

    func get<T: Codable>(_ endpoint: String) async throws -> T {
        guard let url = URL(string: baseURL + endpoint) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        addAuthHeaderIfNeeded(&request)

        return try await performRequest(request)
    }

    func post<T: Codable, U: Encodable>(_ endpoint: String, body: U) async throws -> T {
        guard let url = URL(string: baseURL + endpoint) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        addAuthHeaderIfNeeded(&request)

        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        request.httpBody = try encoder.encode(body)

        return try await performRequest(request)
    }

    func post<T: Codable>(_ endpoint: String) async throws -> T {
        guard let url = URL(string: baseURL + endpoint) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        addAuthHeaderIfNeeded(&request)

        return try await performRequest(request)
    }

    func put<T: Codable, U: Encodable>(_ endpoint: String, body: U) async throws -> T {
        guard let url = URL(string: baseURL + endpoint) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        addAuthHeaderIfNeeded(&request)

        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        request.httpBody = try encoder.encode(body)

        return try await performRequest(request)
    }

    func delete(_ endpoint: String) async throws {
        guard let url = URL(string: baseURL + endpoint) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        addAuthHeaderIfNeeded(&request)

        let (_, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        if !(200...299).contains(httpResponse.statusCode) {
            throw APIError.serverError(httpResponse.statusCode)
        }
    }

    // MARK: - Private Helpers

    private func addAuthHeaderIfNeeded(_ request: inout URLRequest) {
        if let token = authToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
    }

    private func performRequest<T: Codable>(_ request: URLRequest) async throws -> T {
        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        if !(200...299).contains(httpResponse.statusCode) {
            if let errorMessage = String(data: data, encoding: .utf8) {
                print("Error response: \(errorMessage)")
            }
            throw APIError.serverError(httpResponse.statusCode)
        }

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            print("Decode error: \(error)")
            print("Response data: \(String(data: data, encoding: .utf8) ?? "nil")")
            throw APIError.decodingError
        }
    }
}

// MARK: - Error Types

enum APIError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case serverError(Int)
    case decodingError
    case unauthorized

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid server response"
        case .serverError(let code):
            return "Server error: \(code)"
        case .decodingError:
            return "Failed to parse response"
        case .unauthorized:
            return "Authentication required"
        }
    }
}
