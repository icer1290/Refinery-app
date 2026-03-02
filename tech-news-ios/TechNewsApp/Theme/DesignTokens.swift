import SwiftUI

// MARK: - Design Tokens

/// Spacing, sizing, and other design tokens
/// Following a consistent spacing scale
enum DesignTokens {
    // MARK: - Spacing

    /// Extra small spacing - 4pt
    static let spacingXS: CGFloat = 4

    /// Small spacing - 8pt
    static let spacingS: CGFloat = 8

    /// Medium spacing - 16pt
    static let spacingM: CGFloat = 16

    /// Large spacing - 24pt
    static let spacingL: CGFloat = 24

    /// Extra large spacing - 32pt
    static let spacingXL: CGFloat = 32

    /// Extra extra large spacing - 48pt
    static let spacingXXL: CGFloat = 48

    // MARK: - Corner Radius

    /// Small radius - 6pt (tags, small badges)
    static let radiusS: CGFloat = 6

    /// Medium radius - 10pt (cards, buttons)
    static let radiusM: CGFloat = 10

    /// Large radius - 16pt (modals, sheets)
    static let radiusL: CGFloat = 16

    // MARK: - Border Width

    /// Standard border width - 1pt
    static let borderWidth: CGFloat = 1

    /// Thick border width - 2pt
    static let borderThick: CGFloat = 2

    // MARK: - Card Styling

    /// Card padding
    static let cardPadding: CGFloat = 16

    /// Card spacing between elements
    static let cardSpacing: CGFloat = 12

    // MARK: - Animation

    /// Standard animation duration
    static let animationDuration: Double = 0.25

    /// Quick animation duration
    static let animationDurationQuick: Double = 0.15

    /// Spring animation
    static let springAnimation = Animation.spring(response: 0.3, dampingFraction: 0.7)

    /// Ease out animation
    static let easeOutAnimation = Animation.easeOut(duration: animationDuration)
}

// MARK: - Card Style Modifier

/// Card style modifier for consistent card appearance
struct CardStyle: ViewModifier {
    var padding: CGFloat = DesignTokens.cardPadding
    var cornerRadius: CGFloat = DesignTokens.radiusM

    func body(content: Content) -> some View {
        content
            .padding(padding)
            .background(AppColors.surface)
            .cornerRadius(cornerRadius)
            .overlay(
                RoundedRectangle(cornerRadius: cornerRadius)
                    .stroke(AppColors.border, lineWidth: DesignTokens.borderWidth)
            )
    }
}

// MARK: - Pressed Button Style

/// Custom button style with press effect
struct PressedButtonStyle: ButtonStyle {
    var color: Color = AppColors.accent

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(AppTypography.button())
            .foregroundColor(configuration.isPressed ? color.opacity(0.8) : color)
            .scaleEffect(configuration.isPressed ? 0.98 : 1)
            .animation(DesignTokens.easeOutAnimation, value: configuration.isPressed)
    }
}

// MARK: - View Extensions

extension View {
    /// Apply card style
    func cardStyle(padding: CGFloat = DesignTokens.cardPadding, cornerRadius: CGFloat = DesignTokens.radiusM) -> some View {
        modifier(CardStyle(padding: padding, cornerRadius: cornerRadius))
    }
}