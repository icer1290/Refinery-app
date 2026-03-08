import Foundation

struct Article: Codable, Identifiable, Hashable {
    let id: UUID
    let sourceName: String?
    let sourceURL: String?
    let originalTitle: String?
    let originalDescription: String?
    let chineseTitle: String?
    let chineseSummary: String?
    let fullContent: String?
    let totalScore: Double?
    let industryImpactScore: Double?
    let milestoneScore: Double?
    let attentionScore: Double?
    let publishedAt: Date?
    let processedAt: Date?
    var isFavorite: Bool
    var deepsearchReport: String?
    let deepsearchPerformedAt: Date?

    enum CodingKeys: String, CodingKey {
        case id
        case sourceName
        case sourceURL = "sourceUrl"
        case originalTitle
        case originalDescription
        case chineseTitle
        case chineseSummary
        case fullContent
        case totalScore
        case industryImpactScore
        case milestoneScore
        case attentionScore
        case publishedAt
        case processedAt
        case isFavorite
        case deepsearchReport
        case deepsearchPerformedAt
    }

    var displayTitle: String {
        let title = chineseTitle?.trimmingCharacters(in: .whitespacesAndNewlines)
        if let title, !title.isEmpty {
            return title
        }
        return originalTitle?.trimmingCharacters(in: .whitespacesAndNewlines).nonEmpty ?? "Untitled"
    }

    var displayPreview: String {
        let summary = chineseSummary?.trimmingCharacters(in: .whitespacesAndNewlines)
        if let summary, !summary.isEmpty {
            return summary
        }
        return originalDescription?.trimmingCharacters(in: .whitespacesAndNewlines).nonEmpty ?? "No summary available."
    }
}

private extension String {
    var nonEmpty: String? {
        isEmpty ? nil : self
    }
}
