import Foundation

struct LoginRequest: Encodable {
    let email: String
    let password: String
}

struct RegisterRequest: Encodable {
    let email: String
    let password: String
    let nickname: String
}

struct AuthSession: Codable, Equatable {
    let token: String
    let email: String
    let nickname: String?
    let userID: Int64

    enum CodingKeys: String, CodingKey {
        case token
        case email
        case nickname
        case userID = "userId"
    }
}
