import Foundation

enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case unauthorized
    case server(String)
    case emptyResponse

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API URL."
        case .invalidResponse:
            return "Invalid server response."
        case .unauthorized:
            return "Please log in to continue."
        case .server(let message):
            return message
        case .emptyResponse:
            return "The server returned no data."
        }
    }
}

struct AnyEncodable: Encodable {
    private let encodeValue: (Encoder) throws -> Void

    init<T: Encodable>(_ value: T) {
        encodeValue = value.encode
    }

    func encode(to encoder: Encoder) throws {
        try encodeValue(encoder)
    }
}

struct APIClient {
    func request<T: Decodable>(
        path: String,
        method: String = "GET",
        queryItems: [URLQueryItem] = [],
        body: AnyEncodable? = nil,
        token: String? = nil
    ) async throws -> T {
        let request = try makeRequest(
            path: path,
            method: method,
            queryItems: queryItems,
            body: body,
            token: token
        )
        return try await execute(request)
    }

    func requestEmpty(
        path: String,
        method: String,
        queryItems: [URLQueryItem] = [],
        body: AnyEncodable? = nil,
        token: String? = nil
    ) async throws {
        let request = try makeRequest(
            path: path,
            method: method,
            queryItems: queryItems,
            body: body,
            token: token
        )
        _ = try await execute(request) as EmptyPayload
    }

    private func makeRequest(
        path: String,
        method: String,
        queryItems: [URLQueryItem],
        body: AnyEncodable?,
        token: String?
    ) throws -> URLRequest {
        guard let baseURL = URL(string: AppConfiguration.apiBaseURLString) else {
            throw APIError.invalidURL
        }

        guard var components = URLComponents(url: baseURL.appendingPathComponent(path), resolvingAgainstBaseURL: false) else {
            throw APIError.invalidURL
        }
        components.queryItems = queryItems.isEmpty ? nil : queryItems

        guard let url = components.url else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        if let token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        if let body {
            request.httpBody = try ServerDateCoder.encoder.encode(body)
        }

        return request
    }

    private func execute<T: Decodable>(_ request: URLRequest) async throws -> T {
        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        if httpResponse.statusCode == 401 {
            throw APIError.unauthorized
        }

        guard (200..<300).contains(httpResponse.statusCode) else {
            let envelope = try? ServerDateCoder.decoder.decode(APIResponse<EmptyPayload>.self, from: data)
            throw APIError.server(envelope?.message ?? "Request failed with status \(httpResponse.statusCode).")
        }

        let envelope = try ServerDateCoder.decoder.decode(APIResponse<T>.self, from: data)
        guard envelope.success else {
            throw APIError.server(envelope.message ?? "Request failed.")
        }

        guard let payload = envelope.data else {
            if T.self == EmptyPayload.self, let empty = EmptyPayload() as? T {
                return empty
            }
            throw APIError.emptyResponse
        }

        return payload
    }
}
