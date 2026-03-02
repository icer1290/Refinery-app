import SwiftUI

// MARK: - Category Tag

/// A styled tag for displaying news categories
/// Uses monospace font for a terminal/code aesthetic
struct CategoryTag: View {
    let category: String
    var style: TagStyle = .default

    enum TagStyle {
        case `default`
        case compact
        case prominent
    }

    var body: some View {
        Text(category.uppercased())
            .font(AppTypography.monoCaption())
            .foregroundColor(textColor)
            .padding(.horizontal, horizontalPadding)
            .padding(.vertical, verticalPadding)
            .background(backgroundColor)
            .cornerRadius(DesignTokens.radiusS)
            .overlay(
                RoundedRectangle(cornerRadius: DesignTokens.radiusS)
                    .stroke(borderColor, lineWidth: DesignTokens.borderWidth)
            )
    }

    // MARK: - Style Properties

    private var horizontalPadding: CGFloat {
        switch style {
        case .compact:
            return 6
        case .prominent:
            return 10
        default:
            return 8
        }
    }

    private var verticalPadding: CGFloat {
        switch style {
        case .compact:
            return 3
        case .prominent:
            return 5
        default:
            return 4
        }
    }

    private var textColor: Color {
        switch style {
        case .prominent:
            return AppColors.accent
        default:
            return AppColors.secondary
        }
    }

    private var backgroundColor: Color {
        switch style {
        case .prominent:
            return AppColors.accent.opacity(0.1)
        default:
            return AppColors.surface.opacity(0.5)
        }
    }

    private var borderColor: Color {
        switch style {
        case .prominent:
            return AppColors.accent.opacity(0.3)
        default:
            return AppColors.borderSubtle
        }
    }
}

// MARK: - Tag List View

/// A horizontal scrollable list of category tags
struct CategoryTagList: View {
    let categories: [String]
    var style: CategoryTag.TagStyle = .default

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: DesignTokens.spacingS) {
                ForEach(categories, id: \.self) { category in
                    CategoryTag(category: category, style: style)
                }
            }
        }
    }
}

// MARK: - Preview

#Preview("Category Tags") {
    VStack(alignment: .leading, spacing: 16) {
        HStack(spacing: 8) {
            CategoryTag(category: "AI", style: .compact)
            CategoryTag(category: "Machine Learning", style: .default)
            CategoryTag(category: "iOS", style: .prominent)
        }

        CategoryTagList(categories: ["AI", "Swift", "iOS", "Machine Learning", "Tech"])
    }
    .padding()
    .background(AppColors.background)
}