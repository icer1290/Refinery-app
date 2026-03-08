import Foundation

enum AppConfiguration {
    static let apiBaseURLDefaultsKey = "api-base-url"
    private static let simulatorDefaultAPIBaseURLString = "http://localhost:8080"
    private static let fallbackAPIBaseURLString = "http://localhost:8080"
    static let deepSearchMaxIterations = 10

    static var apiBaseURLString: String {
        if let override = persistedAPIBaseURLString {
            return override
        }

        if
            let bundled = Bundle.main.object(forInfoDictionaryKey: "API_BASE_URL") as? String,
            let normalized = normalizeBaseURLString(bundled)
        {
            return normalized
        }

        #if targetEnvironment(simulator)
        return simulatorDefaultAPIBaseURLString
        #else
        return fallbackAPIBaseURLString
        #endif
    }

    static var persistedAPIBaseURLString: String? {
        guard let value = UserDefaults.standard.string(forKey: apiBaseURLDefaultsKey) else {
            return nil
        }
        return normalizeBaseURLString(value)
    }

    static func saveAPIBaseURLString(_ value: String) {
        guard let normalized = normalizeBaseURLString(value) else {
            UserDefaults.standard.removeObject(forKey: apiBaseURLDefaultsKey)
            return
        }
        UserDefaults.standard.set(normalized, forKey: apiBaseURLDefaultsKey)
    }

    static func clearAPIBaseURLOverride() {
        UserDefaults.standard.removeObject(forKey: apiBaseURLDefaultsKey)
    }

    static func normalizeBaseURLString(_ value: String) -> String? {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            return nil
        }

        return trimmed.hasSuffix("/") ? String(trimmed.dropLast()) : trimmed
    }
}
