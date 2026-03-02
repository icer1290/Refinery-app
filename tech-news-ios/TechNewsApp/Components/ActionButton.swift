import SwiftUI

// MARK: - Action Button

/// A styled action button with multiple variants
/// Supports filled, bordered, and text styles
struct ActionButton: View {
    let title: String
    let icon: String?
    let style: ButtonStyleType
    let action: () -> Void

    enum ButtonStyleType {
        case filled
        case bordered
        case text
        case destructive
    }

    init(
        _ title: String,
        icon: String? = nil,
        style: ButtonStyleType = .filled,
        action: @escaping () -> Void
    ) {
        self.title = title
        self.icon = icon
        self.style = style
        self.action = action
    }

    var body: some View {
        Button(action: action) {
            HStack(spacing: DesignTokens.spacingS) {
                if let icon = icon {
                    Image(systemName: icon)
                        .font(.system(size: 14, weight: .medium))
                }
                Text(title)
                    .font(AppTypography.button())
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, DesignTokens.spacingM)
            .background(backgroundColor)
            .foregroundColor(foregroundColor)
            .cornerRadius(DesignTokens.radiusM)
            .overlay(
                RoundedRectangle(cornerRadius: DesignTokens.radiusM)
                    .stroke(borderColor, lineWidth: borderWidth)
            )
        }
        .disabled(style == .filled)
    }

    // MARK: - Style Properties

    private var backgroundColor: Color {
        switch style {
        case .filled:
            return AppColors.accent
        case .bordered:
            return Color.clear
        case .text:
            return Color.clear
        case .destructive:
            return Color.clear
        }
    }

    private var foregroundColor: Color {
        switch style {
        case .filled:
            return AppColors.background
        case .bordered:
            return AppColors.accent
        case .text:
            return AppColors.accent
        case .destructive:
            return AppColors.error
        }
    }

    private var borderColor: Color {
        switch style {
        case .filled:
            return Color.clear
        case .bordered:
            return AppColors.accent
        case .text:
            return Color.clear
        case .destructive:
            return AppColors.error
        }
    }

    private var borderWidth: CGFloat {
        switch style {
        case .filled, .text:
            return 0
        case .bordered, .destructive:
            return DesignTokens.borderWidth
        }
    }
}

// MARK: - Secondary Action Button

/// A smaller, secondary action button
struct SecondaryActionButton: View {
    let title: String
    let icon: String?
    let action: () -> Void

    init(_ title: String, icon: String? = nil, action: @escaping () -> Void) {
        self.title = title
        self.icon = icon
        self.action = action
    }

    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                if let icon = icon {
                    Image(systemName: icon)
                        .font(.system(size: 12, weight: .medium))
                }
                Text(title)
                    .font(AppTypography.buttonSmall())
            }
            .foregroundColor(AppColors.accent)
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(AppColors.accent.opacity(0.1))
            .cornerRadius(DesignTokens.radiusS)
        }
    }
}

// MARK: - Icon Button

/// A circular icon button
struct IconButton: View {
    let icon: String
    let style: ActionButton.ButtonStyleType
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: icon)
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(foregroundColor)
                .frame(width: 44, height: 44)
                .background(backgroundColor)
                .cornerRadius(DesignTokens.radiusM)
                .overlay(
                    RoundedRectangle(cornerRadius: DesignTokens.radiusM)
                        .stroke(borderColor, lineWidth: borderWidth)
                )
        }
    }

    private var backgroundColor: Color {
        switch style {
        case .filled:
            return AppColors.accent
        default:
            return AppColors.surface
        }
    }

    private var foregroundColor: Color {
        switch style {
        case .filled:
            return AppColors.background
        default:
            return AppColors.accent
        }
    }

    private var borderColor: Color {
        switch style {
        case .filled:
            return Color.clear
        default:
            return AppColors.border
        }
    }

    private var borderWidth: CGFloat {
        switch style {
        case .filled:
            return 0
        default:
            return DesignTokens.borderWidth
        }
    }
}

// MARK: - Preview

#Preview("Action Buttons") {
    VStack(spacing: 16) {
        ActionButton("Read Article", icon: "safari", style: .filled) {}

        HStack(spacing: 12) {
            ActionButton("Favorite", icon: "heart", style: .bordered) {}
            ActionButton("Share", icon: "square.and.arrow.up", style: .bordered) {}
        }

        ActionButton("Delete", icon: "trash", style: .destructive) {}
        ActionButton("Learn More", style: .text) {}

        HStack(spacing: 12) {
            IconButton(icon: "heart", style: .bordered) {}
            IconButton(icon: "arrow.clockwise", style: .filled) {}
        }

        SecondaryActionButton("View All", icon: "chevron.right") {}
    }
    .padding()
    .background(AppColors.background)
}