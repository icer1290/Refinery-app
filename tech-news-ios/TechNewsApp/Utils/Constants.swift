import Foundation

struct Constants {
    // API Configuration
    static let apiBaseURL = ProcessInfo.processInfo.environment["API_BASE_URL"] ?? "http://localhost:8080"

    // Endpoints
    struct Endpoints {
        static let auth = "/api/auth"
        static let news = "/api/news"
        static let user = "/api/user"

        static func login() -> String { return auth + "/login" }
        static func register() -> String { return auth + "/register" }
        static func todayNews() -> String { return news + "/today" }
        static func archiveNews() -> String { return news + "/archive" }
        static func newsDetail(id: Int) -> String { return news + "/\(id)" }
        static func favorite(id: Int) -> String { return news + "/\(id)/favorite" }
        static func preferences() -> String { return user + "/preferences" }
        static func userFavorites() -> String { return user + "/favorites" }
        static func availableDates() -> String { return news + "/dates" }
    }

    // Storage Keys
    struct StorageKeys {
        static let authToken = "auth_token"
        static let userEmail = "user_email"
        static let userId = "user_id"
    }

    // Categories
    static let categories = [
        "AI & Machine Learning",
        "Software Development",
        "Startup & Business",
        "Hardware & Devices",
        "Security & Privacy",
        "Cloud & DevOps",
        "Mobile & Apps",
        "Web & Frontend"
    ]
}
