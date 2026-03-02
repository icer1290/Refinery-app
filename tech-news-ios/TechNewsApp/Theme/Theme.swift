import SwiftUI

// MARK: - Theme Manager

/// Theme environment key for accessing theme values
struct ThemeKey: EnvironmentKey {
    static let defaultValue = Theme.current
}

extension EnvironmentValues {
    var theme: Theme {
        get { self[ThemeKey.self] }
        set { self[ThemeKey.self] = newValue }
    }
}

// MARK: - Theme Configuration

/// Theme configuration containing all design system values
struct Theme {
    /// Current theme instance
    static let current = Theme()

    // MARK: - Colors
    let colors = AppColors.self
    let gradients = AppGradients.self

    // MARK: - Typography
    let typography = AppTypography.self

    // MARK: - Tokens
    let tokens = DesignTokens.self
}

// MARK: - Color Assets (Asset Catalog References)

// These color references work with the Asset Catalog colors
extension Color {
    // MARK: - Primary Colors
    static let primaryColor = Color("Primary")
    static let secondaryColor = Color("Secondary")

    // MARK: - Accent Colors
    static let accentColor = Color("Accent")
    static let accentSecondaryColor = Color("AccentSecondary")

    // MARK: - Background Colors
    static let backgroundColor = Color("Background")
    static let surfaceColor = Color("Surface")
    static let surfaceElevatedColor = Color("SurfaceElevated")

    // MARK: - Border Colors
    static let borderColor = Color("Border")
    static let borderSubtleColor = Color("BorderSubtle")

    // MARK: - Semantic Colors
    static let successColor = Color("Success")
    static let errorColor = Color("Error")
    static let warningColor = Color("Warning")

    // MARK: - Score Colors
    static let scoreMediumColor = Color("ScoreMedium")
    static let scoreLowColor = Color("ScoreLow")
}