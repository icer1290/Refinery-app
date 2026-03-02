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

    // MARK: - Score Colors (based on llm_score, 0-10 scale)
    /// 热点 (>= 7) - 红色 #FF3B30
    static let scoreHigh = Color("ScoreHigh")
    /// 热门 (5 - 7) - 橙色 #FF9500
    static let scoreMedium = Color("ScoreMedium")
    /// 快讯 (< 5) - 灰色 #8E8E93
    static let scoreLow = Color("ScoreLow")
}

// MARK: - Color Extensions

extension Color {
    /// Primary accent color (Cyan #00D9FF)
    static let appAccent = AppColors.accent

    /// Get score color based on llm_score value (0-10 scale)
    /// - 热点 (>= 7): Red
    /// - 热门 (5 - 7): Orange
    /// - 快讯 (< 5): Gray
    static func scoreColor(for llmScore: Double) -> Color {
        if llmScore >= 7 {
            return AppColors.scoreHigh
        } else if llmScore >= 5 {
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