import SwiftUI

// MARK: - Empty State View

/// A styled empty state view for when there's no content to display
struct EmptyStateView: View {
    let icon: String
    let title: String
    let subtitle: String?
    let action: EmptyStateAction?

    struct EmptyStateAction {
        let title: String
        let handler: () -> Void
    }

    init(
        icon: String,
        title: String,
        subtitle: String? = nil,
        action: EmptyStateAction? = nil
    ) {
        self.icon = icon
        self.title = title
        self.subtitle = subtitle
        self.action = action
    }

    var body: some View {
        VStack(spacing: DesignTokens.spacingM) {
            // Icon
            Image(systemName: icon)
                .font(.system(size: 48, weight: .light))
                .foregroundColor(AppColors.accent.opacity(0.6))

            // Title
            Text(title)
                .font(AppTypography.title3())
                .foregroundColor(AppColors.primary)
                .multilineTextAlignment(.center)

            // Subtitle
            if let subtitle = subtitle {
                Text(subtitle)
                    .font(AppTypography.body())
                    .foregroundColor(AppColors.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, DesignTokens.spacingL)
            }

            // Action button
            if let action = action {
                Button(action: action.handler) {
                    Text(action.title)
                        .font(AppTypography.button())
                        .foregroundColor(AppColors.accent)
                        .padding(.horizontal, DesignTokens.spacingL)
                        .padding(.vertical, DesignTokens.spacingS)
                        .background(AppColors.accent.opacity(0.1))
                        .cornerRadius(DesignTokens.radiusS)
                }
                .padding(.top, DesignTokens.spacingS)
            }
        }
        .padding(DesignTokens.spacingXL)
    }
}

// MARK: - Loading State View

/// A styled loading indicator
struct LoadingStateView: View {
    let message: String

    init(_ message: String = "Loading...") {
        self.message = message
    }

    var body: some View {
        VStack(spacing: DesignTokens.spacingM) {
            ProgressView()
                .progressViewStyle(CircularProgressViewStyle(tint: AppColors.accent))
                .scaleEffect(1.2)

            Text(message)
                .font(AppTypography.caption())
                .foregroundColor(AppColors.secondary)
        }
        .padding(DesignTokens.spacingXL)
    }
}

// MARK: - Error State View

/// A styled error state view
struct ErrorStateView: View {
    let title: String
    let message: String?
    let retryAction: (() -> Void)?

    init(
        title: String = "Something went wrong",
        message: String? = nil,
        retryAction: (() -> Void)? = nil
    ) {
        self.title = title
        self.message = message
        self.retryAction = retryAction
    }

    var body: some View {
        VStack(spacing: DesignTokens.spacingM) {
            // Icon
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 48, weight: .light))
                .foregroundColor(AppColors.warning)

            // Title
            Text(title)
                .font(AppTypography.title3())
                .foregroundColor(AppColors.primary)
                .multilineTextAlignment(.center)

            // Message
            if let message = message {
                Text(message)
                    .font(AppTypography.body())
                    .foregroundColor(AppColors.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, DesignTokens.spacingL)
            }

            // Retry button
            if let retryAction = retryAction {
                Button(action: retryAction) {
                    HStack(spacing: 6) {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 12, weight: .medium))
                        Text("Try Again")
                            .font(AppTypography.button())
                    }
                    .foregroundColor(AppColors.accent)
                    .padding(.horizontal, DesignTokens.spacingL)
                    .padding(.vertical, DesignTokens.spacingS)
                    .background(AppColors.accent.opacity(0.1))
                    .cornerRadius(DesignTokens.radiusS)
                }
                .padding(.top, DesignTokens.spacingS)
            }
        }
        .padding(DesignTokens.spacingXL)
    }
}

// MARK: - Preview

#Preview("Empty States") {
    VStack(spacing: 40) {
        EmptyStateView(
            icon: "newspaper",
            title: "No News Yet",
            subtitle: "Check back later for the latest tech news",
            action: EmptyStateView.EmptyStateAction(title: "Refresh") {}
        )

        LoadingStateView("Loading news...")

        ErrorStateView(
            title: "Connection Error",
            message: "Unable to load news. Please check your connection.",
            retryAction: {}
        )
    }
    .padding()
    .background(AppColors.background)
}