import SwiftUI

// MARK: - Score Badge

/// A badge displaying a score value with color coding
/// High (>=0.8): Cyan, Medium (0.5-0.8): Yellow, Low (<0.5): Red
struct ScoreBadge: View {
    let score: Double

    var body: some View {
        HStack(spacing: 4) {
            // Score indicator bar
            scoreIndicator

            // Score value
            Text(String(format: "%.2f", score))
                .font(AppTypography.mono())
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
        if score >= 0.8 {
            return AppColors.scoreHigh
        } else if score >= 0.5 {
            return AppColors.scoreMedium
        } else {
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
    let score: Double

    var body: some View {
        Text(String(format: "%.2f", score))
            .font(AppTypography.monoCaption())
            .foregroundColor(scoreColor)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(scoreColor.opacity(0.1))
            .cornerRadius(4)
    }

    private var scoreColor: Color {
        if score >= 0.8 {
            return AppColors.scoreHigh
        } else if score >= 0.5 {
            return AppColors.scoreMedium
        } else {
            return AppColors.scoreLow
        }
    }
}

// MARK: - Preview

#Preview("Score Badges") {
    VStack(spacing: 16) {
        HStack(spacing: 12) {
            ScoreBadge(score: 0.92)
            ScoreBadge(score: 0.75)
            ScoreBadge(score: 0.35)
        }

        HStack(spacing: 12) {
            CompactScoreBadge(score: 0.92)
            CompactScoreBadge(score: 0.75)
            CompactScoreBadge(score: 0.35)
        }
    }
    .padding()
    .background(AppColors.background)
}