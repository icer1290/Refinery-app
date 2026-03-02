import SwiftUI

// MARK: - Score Label

/// Score label types with corresponding display text
/// Based on llm_score (0-10 scale)
enum ScoreLabel: String {
    case hot = "热点"     // >= 6.5
    case popular = "热门" // 5 - 6.5
    case flash = "快讯"   // < 5

    /// Get label from llm_score value (0-10 scale)
    static func from(llmScore: Double) -> ScoreLabel {
        if llmScore >= 6.5 {
            return .hot
        } else if llmScore >= 5 {
            return .popular
        } else {
            return .flash
        }
    }
}

// MARK: - Score Badge

/// A badge displaying a score label with color coding
/// Uses llm_score (0-10 scale):
/// 热点 (>= 7): Red, 热门 (5 - 7): Orange, 快讯 (< 5): Gray
struct ScoreBadge: View {
    let llmScore: Double

    private var label: ScoreLabel {
        ScoreLabel.from(llmScore: llmScore)
    }

    var body: some View {
        HStack(spacing: 4) {
            // Score indicator bar
            scoreIndicator

            // Score label text
            Text(label.rawValue)
                .font(AppTypography.captionBold())
                .foregroundColor(scoreColor)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 4)
        .background(scoreColor.opacity(0.1))
        .cornerRadius(DesignTokens.radiusS)
        .overlay(
            RoundedRectangle(cornerRadius: DesignTokens.radiusS)
                .stroke(scoreColor.opacity(0.3), lineWidth: DesignTokens.borderWidth)
        )
    }

    // MARK: - Score Color

    private var scoreColor: Color {
        switch label {
        case .hot:
            return AppColors.scoreHigh
        case .popular:
            return AppColors.scoreMedium
        case .flash:
            return AppColors.scoreLow
        }
    }

    // MARK: - Score Indicator

    private var scoreIndicator: some View {
        RoundedRectangle(cornerRadius: 1)
            .fill(scoreColor)
            .frame(width: 3, height: 12)
    }
}

// MARK: - Compact Score Badge

/// A more compact version of the score badge for smaller spaces
struct CompactScoreBadge: View {
    let llmScore: Double

    private var label: ScoreLabel {
        ScoreLabel.from(llmScore: llmScore)
    }

    var body: some View {
        Text(label.rawValue)
            .font(AppTypography.captionBold())
            .foregroundColor(scoreColor)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(scoreColor.opacity(0.1))
            .cornerRadius(4)
    }

    private var scoreColor: Color {
        switch label {
        case .hot:
            return AppColors.scoreHigh
        case .popular:
            return AppColors.scoreMedium
        case .flash:
            return AppColors.scoreLow
        }
    }
}

// MARK: - Preview

#Preview("Score Badges") {
    VStack(spacing: 16) {
        HStack(spacing: 12) {
            ScoreBadge(llmScore: 9.2)
            ScoreBadge(llmScore: 6.5)
            ScoreBadge(llmScore: 3.5)
        }

        HStack(spacing: 12) {
            CompactScoreBadge(llmScore: 9.2)
            CompactScoreBadge(llmScore: 6.5)
            CompactScoreBadge(llmScore: 3.5)
        }
    }
    .padding()
    .background(AppColors.background)
}
