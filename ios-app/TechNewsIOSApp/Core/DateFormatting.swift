import Foundation

enum ServerDateCoder {
    private static let locale = Locale(identifier: "en_US_POSIX")
    private static let formatterPatterns = [
        "yyyy-MM-dd'T'HH:mm:ss.SSSSSS",
        "yyyy-MM-dd'T'HH:mm:ss.SSS",
        "yyyy-MM-dd'T'HH:mm:ss"
    ]

    private static let formatters: [DateFormatter] = formatterPatterns.map { pattern in
        let formatter = DateFormatter()
        formatter.locale = locale
        formatter.dateFormat = pattern
        formatter.timeZone = .current
        return formatter
    }

    static let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let value = try container.decode(String.self)

            for formatter in formatters {
                if let date = formatter.date(from: value) {
                    return date
                }
            }

            if let isoDate = ISO8601DateFormatter().date(from: value) {
                return isoDate
            }

            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "Unsupported date format: \(value)"
            )
        }
        return decoder
    }()

    static let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        return encoder
    }()
}

enum DateFormatting {
    private static let itemFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter
    }()

    private static let detailFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .long
        formatter.timeStyle = .short
        return formatter
    }()

    static func itemTimestamp(_ date: Date?) -> String {
        guard let date else { return "Unknown" }
        return itemFormatter.string(from: date)
    }

    static func detailTimestamp(_ date: Date?) -> String {
        guard let date else { return "Unknown" }
        return detailFormatter.string(from: date)
    }
}
