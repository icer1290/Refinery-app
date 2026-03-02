import Foundation

struct UserPreference: Codable {
    let id: Int?
    let preferredCategories: [String]?
    let notificationEnabled: Bool?

    enum CodingKeys: String, CodingKey {
        case id
        case preferredCategories = "preferredCategories"
        case notificationEnabled = "notificationEnabled"
    }
}

struct UserPreferenceResponse: Codable {
    let success: Bool?
    let message: String?
    let data: UserPreference?
}

struct UserPreferenceRequest: Encodable {
    let preferredCategories: [String]?
    let notificationEnabled: Bool?
}
