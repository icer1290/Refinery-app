import SwiftUI

// MARK: - Typography System

/// Typography styles for the minimalist geek style
/// Uses SF Pro for body text and SF Mono for code/scores
enum AppTypography {
    // MARK: - Display Styles

    /// Large display title - 34pt Bold
    static func display() -> Font {
        .system(size: 34, weight: .bold, design: .default)
    }

    // MARK: - Title Styles

    /// Page title - 24pt Semibold
    static func title() -> Font {
        .system(size: 24, weight: .semibold, design: .default)
    }

    /// Section title - 20pt Semibold
    static func title2() -> Font {
        .system(size: 20, weight: .semibold, design: .default)
    }

    /// Small title - 17pt Semibold
    static func title3() -> Font {
        .system(size: 17, weight: .semibold, design: .default)
    }

    // MARK: - Headline Styles

    /// News headline - 17pt Semibold
    static func headline() -> Font {
        .system(size: 17, weight: .semibold, design: .default)
    }

    // MARK: - Body Styles

    /// Regular body text - 15pt Regular
    static func body() -> Font {
        .system(size: 15, weight: .regular, design: .default)
    }

    /// Body text with more prominence - 15pt Medium
    static func bodyMedium() -> Font {
        .system(size: 15, weight: .medium, design: .default)
    }

    /// Callout text - 14pt Regular
    static func callout() -> Font {
        .system(size: 14, weight: .regular, design: .default)
    }

    // MARK: - Caption Styles

    /// Caption text - 13pt Regular
    static func caption() -> Font {
        .system(size: 13, weight: .regular, design: .default)
    }

    /// Caption with emphasis - 13pt Medium
    static func captionMedium() -> Font {
        .system(size: 13, weight: .medium, design: .default)
    }

    // MARK: - Monospace Styles (Terminal/Code feel)

    /// Monospace text for scores, codes, sources - 13pt Medium
    static func mono() -> Font {
        .system(size: 13, weight: .medium, design: .monospaced)
    }

    /// Monospace caption for tags - 11pt Medium
    static func monoCaption() -> Font {
        .system(size: 11, weight: .medium, design: .monospaced)
    }

    /// Monospace body - 14pt Regular
    static func monoBody() -> Font {
        .system(size: 14, weight: .regular, design: .monospaced)
    }

    // MARK: - Button Styles

    /// Button text - 15pt Semibold
    static func button() -> Font {
        .system(size: 15, weight: .semibold, design: .default)
    }

    /// Small button text - 13pt Semibold
    static func buttonSmall() -> Font {
        .system(size: 13, weight: .semibold, design: .default)
    }
}

// MARK: - View Extension for Typography

extension View {
    /// Apply display typography style
    func displayStyle() -> some View {
        self.font(AppTypography.display())
    }

    /// Apply title typography style
    func titleStyle() -> some View {
        self.font(AppTypography.title())
    }

    /// Apply headline typography style
    func headlineStyle() -> some View {
        self.font(AppTypography.headline())
    }

    /// Apply body typography style
    func bodyStyle() -> some View {
        self.font(AppTypography.body())
    }

    /// Apply caption typography style
    func captionStyle() -> some View {
        self.font(AppTypography.caption())
    }

    /// Apply monospace typography style
    func monoStyle() -> some View {
        self.font(AppTypography.mono())
    }

    /// Apply monospace caption typography style
    func monoCaptionStyle() -> some View {
        self.font(AppTypography.monoCaption())
    }
}