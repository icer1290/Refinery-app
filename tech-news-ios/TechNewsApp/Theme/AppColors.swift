import SwiftUI

// MARK: - App Colors

/// Color palette for the minimalist geek style theme
/// Primary accent: Cyan #00D9FF (terminal/code editor aesthetic)
enum AppColors {
    // MARK: - Primary Colors
    /// Primary text color - near black in light, off white in dark
    static let primary = Color("Primary")
    /// Secondary text color - gray tones
    static let secondary = Color("Secondary")

    // MARK: - Accent Colors
    /// Main accent color - Cyan #00D9FF
    static let accent = Color("Accent")
    /// Secondary accent - Purple
    static let accentSecondary = Color("AccentSecondary")

    // MARK: - Background Colors
    /// Main background
    static let background = Color("Background")
    /// Surface/card background
    static let surface = Color("Surface")
    /// Elevated surface
    static let surfaceElevated = Color("SurfaceElevated")

    // MARK: - Border Colors
    /// Default border
    static let border = Color("Border")
    /// Subtle border
    static let borderSubtle = Color("BorderSubtle")

    // MARK: - Semantic Colors
    /// Success color
    static let success = Color("Success")
    /// Error/danger color
    static let error = Color("Error")
    /// Warning color
    static let warning = Color("Warning")

    // MARK: - Score Colors
    /// High score (>= 0.8)
    static let scoreHigh = Color("Accent")
    /// Medium score (0.5 - 0.8)
    static let scoreMedium = Color("ScoreMedium")
    /// Low score (< 0.5)
    static let scoreLow = Color("ScoreLow")
}

// MARK: - Color Extensions

extension Color {
    /// Primary accent color (Cyan #00D9FF)
    static let appAccent = AppColors.accent

    /// Get score color based on value
    static func scoreColor(for score: Double) -> Color {
        if score >= 0.8 {
            return AppColors.scoreHigh
        } else if score >= 0.5 {
            return AppColors.scoreMedium
        } else {
            return AppColors.scoreLow
        }
    }
}

// MARK: - Shape Style for Gradients

/// Gradient styles used throughout the app
enum AppGradients {
    /// Subtle gradient for cards and surfaces
    static var cardGradient: LinearGradient {
        LinearGradient(
            colors: [AppColors.surface, AppColors.surfaceElevated],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }

    /// Accent gradient for buttons
    static var accentGradient: LinearGradient {
        LinearGradient(
            colors: [AppColors.accent, AppColors.accent.opacity(0.8)],
            startPoint: .leading,
            endPoint: .trailing
        )
    }
}