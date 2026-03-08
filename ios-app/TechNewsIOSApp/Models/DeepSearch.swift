import Foundation

struct DeepSearchRequest: Encodable {
    let articleID: String
    let maxIterations: Int

    enum CodingKeys: String, CodingKey {
        case articleID = "article_id"
        case maxIterations = "max_iterations"
    }
}

struct DeepSearchResult: Decodable, Equatable {
    let articleID: String
    let articleTitle: String
    let finalReport: String
    let toolsUsed: [ToolCallInfo]
    let collectedInfo: [CollectedInfo]
    let iterations: Int
    let isComplete: Bool
    let errors: [DeepSearchError]

    enum CodingKeys: String, CodingKey {
        case articleID = "article_id"
        case articleTitle = "article_title"
        case finalReport = "final_report"
        case toolsUsed = "tools_used"
        case collectedInfo = "collected_info"
        case iterations
        case isComplete = "is_complete"
        case errors
    }
}

struct ToolCallInfo: Decodable, Equatable, Hashable {
    let toolName: String
    let toolInput: [String: StringCodable]
    let toolOutput: String
    let iteration: Int

    enum CodingKeys: String, CodingKey {
        case toolName = "tool_name"
        case toolInput = "tool_input"
        case toolOutput = "tool_output"
        case iteration
    }
}

struct CollectedInfo: Decodable, Equatable, Hashable {
    let source: String
    let content: String
    let relevance: String
}

struct DeepSearchError: Decodable, Equatable, Hashable {
    let phase: String
    let message: String
}

enum StringCodable: Codable, Equatable, Hashable {
    case string(String)
    case int(Int)
    case double(Double)
    case bool(Bool)

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let value = try? container.decode(String.self) {
            self = .string(value)
        } else if let value = try? container.decode(Int.self) {
            self = .int(value)
        } else if let value = try? container.decode(Double.self) {
            self = .double(value)
        } else if let value = try? container.decode(Bool.self) {
            self = .bool(value)
        } else {
            self = .string("")
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let value):
            try container.encode(value)
        case .int(let value):
            try container.encode(value)
        case .double(let value):
            try container.encode(value)
        case .bool(let value):
            try container.encode(value)
        }
    }
}
