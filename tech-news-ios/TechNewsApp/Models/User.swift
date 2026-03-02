import Foundation

struct User: Codable {
    let id: Int
    let email: String
    let nickname: String?
    let createdAt: String?

    enum CodingKeys: String, CodingKey {
        case id, email, nickname
        case createdAt = "createdAt"
    }
}

struct AuthResponse: Codable {
    let success: Bool?
    let message: String?
    let data: AuthData?

    struct AuthData: Codable {
        let token: String
        let email: String
        let nickname: String?
        let userId: Int
    }
}

struct ApiResponse<T: Codable>: Codable {
    let success: Bool?
    let message: String?
    let data: T?
}
