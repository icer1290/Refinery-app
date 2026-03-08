import Foundation

struct UserPreferences: Codable, Equatable {
    let id: Int64?
    var preferredCategories: [String]
    var notificationEnabled: Bool
}

struct UserPreferencesRequest: Encodable {
    let preferredCategories: [String]
    let notificationEnabled: Bool
}
