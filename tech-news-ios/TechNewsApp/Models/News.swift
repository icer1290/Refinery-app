import Foundation
import SwiftUI

struct News: Codable, Identifiable, Hashable {
    let id: Int
    let title: String
    let translatedTitle: String?
    let url: String
    let source: String?
    let category: String?
    let score: Int?
    let llmScore: Double?
    let finalScore: Double?
    let summary: String?
    let publishedDate: String?
    let isFavorite: Bool?

    enum CodingKeys: String, CodingKey {
        case id, title, url, source, category, score, summary
        case translatedTitle = "translatedTitle"
        case llmScore = "llmScore"
        case finalScore = "finalScore"
        case publishedDate = "publishedDate"
        case isFavorite = "isFavorite"
    }

    var displayTitle: String {
        translatedTitle ?? title
    }

    var formattedDate: String {
        guard let date = publishedDate else { return "" }
        return date.formatDateFromISO8601()
    }

    var scoreBadge: String {
        guard let fs = finalScore else {
            return score.map { "\($0)" } ?? ""
        }
        return String(format: "%.2f", fs)
    }
}

struct NewsListResponse: Codable {
    let success: Bool?
    let message: String?
    let data: [News]?
}

struct DateListResponse: Codable {
    let success: Bool?
    let data: [String]?
}
