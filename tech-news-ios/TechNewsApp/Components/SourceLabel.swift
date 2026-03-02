import SwiftUI

// MARK: - Source Label

/// A styled label for displaying news sources
/// Uses monospace font for a terminal/terminal aesthetic
struct SourceLabel: View {
    let source: String
    var style: SourceStyle = .default

    enum SourceStyle {
        case `default`
        case compact
        case prominent
    }

    var body: some View {
        HStack(spacing: 4) {
            // Source icon indicator
            sourceIndicator

            // Source name
            Text(source)
                .font(AppTypography.mono())
                .foregroundColor(textColor)
        }
    }

    // MARK: - Source Indicator

    private var sourceIndicator: some View {
        RoundedRectangle(cornerRadius: 1)
            .fill(indicatorColor)
            .frame(width: 2, height: 10)
    }

    // MARK: - Style Properties

    private var textColor: Color {
        switch style {
        case .prominent:
            return AppColors.accent
        default:
            return AppColors.secondary
        }
    }

    private var indicatorColor: Color {
        switch style {
        case .prominent:
            return AppColors.accent
        default:
            return AppColors.secondary.opacity(0.5)
        }
    }
}

// MARK: - Preview

#Preview("Source Labels") {
    VStack(alignment: .leading, spacing: 16) {
        SourceLabel(source: "TechCrunch", style: .default)
        SourceLabel(source: "Hacker News", style: .compact)
        SourceLabel(source: "The Verge", style: .prominent)

        HStack {
            SourceLabel(source: "TechCrunch")
            Spacer()
            Text("•")
                .foregroundColor(AppColors.secondary)
            Spacer()
            ScoreBadge(llmScore: 8.5)
        }
    }
    .padding()
    .background(AppColors.background)
}