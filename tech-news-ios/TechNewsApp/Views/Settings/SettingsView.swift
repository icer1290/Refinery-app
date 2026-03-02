import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var authViewModel: AuthViewModel
    @StateObject private var settingsViewModel = SettingsViewModel()
    @State private var showLogoutConfirm = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: DesignTokens.spacingM) {
                    // Account Section
                    accountSection

                    // Preferences Section
                    preferencesSection

                    // Favorites Section
                    favoritesSection

                    // Logout Section
                    logoutSection
                }
                .padding(DesignTokens.spacingM)
            }
            .background(AppColors.background)
            .navigationTitle("Settings")
            .task {
                await settingsViewModel.loadPreferences()
            }
            .alert("Logout", isPresented: $showLogoutConfirm) {
                Button("Cancel", role: .cancel) {}
                Button("Logout", role: .destructive) {
                    authViewModel.logout()
                }
            } message: {
                Text("Are you sure you want to logout?")
            }
        }
    }

    // MARK: - Account Section

    private var accountSection: some View {
        VStack(alignment: .leading, spacing: DesignTokens.spacingS) {
            // Section Header
            SectionHeader(title: "ACCOUNT")

            // User Card
            HStack(spacing: DesignTokens.spacingM) {
                // Avatar
                ZStack {
                    Circle()
                        .stroke(AppColors.accent, lineWidth: 1)
                        .frame(width: 56, height: 56)

                    Image(systemName: "person.fill")
                        .font(.system(size: 24, weight: .light))
                        .foregroundColor(AppColors.accent)
                }

                // User Info
                VStack(alignment: .leading, spacing: 4) {
                    Text(authViewModel.userEmail ?? "Unknown")
                        .font(AppTypography.headline())
                        .foregroundColor(AppColors.primary)

                    Text("ID: \(authViewModel.userId ?? 0)")
                        .font(AppTypography.monoCaption())
                        .foregroundColor(AppColors.secondary)
                }

                Spacer()
            }
            .padding(DesignTokens.cardPadding)
            .background(AppColors.surface)
            .cornerRadius(DesignTokens.radiusM)
            .overlay(
                RoundedRectangle(cornerRadius: DesignTokens.radiusM)
                    .stroke(AppColors.border, lineWidth: DesignTokens.borderWidth)
            )
        }
    }

    // MARK: - Preferences Section

    private var preferencesSection: some View {
        VStack(alignment: .leading, spacing: DesignTokens.spacingS) {
            SectionHeader(title: "PREFERENCES")

            VStack(spacing: 0) {
                // Categories
                NavigationLink {
                    CategorySelectionView(
                        selectedCategories: $settingsViewModel.selectedCategories
                    ) {
                        Task {
                            await settingsViewModel.savePreferences()
                        }
                    }
                } label: {
                    SettingsRow(
                        icon: "square.grid.2x2",
                        title: "Preferred Categories",
                        value: "\(settingsViewModel.selectedCategories.count) selected"
                    )
                }

                Divider()
                    .padding(.leading, 44)

                // Notifications
                HStack(spacing: DesignTokens.spacingM) {
                    SettingsIcon(icon: "bell")

                    Text("Notifications")
                        .font(AppTypography.body())
                        .foregroundColor(AppColors.primary)

                    Spacer()

                    Toggle("", isOn: $settingsViewModel.notificationsEnabled)
                        .labelsHidden()
                        .tint(AppColors.accent)
                        .onChange(of: settingsViewModel.notificationsEnabled) { _ in
                            Task {
                                await settingsViewModel.savePreferences()
                            }
                        }
                }
                .padding(.vertical, DesignTokens.spacingS)
                .padding(.horizontal, DesignTokens.cardPadding)
            }
            .background(AppColors.surface)
            .cornerRadius(DesignTokens.radiusM)
            .overlay(
                RoundedRectangle(cornerRadius: DesignTokens.radiusM)
                    .stroke(AppColors.border, lineWidth: DesignTokens.borderWidth)
            )
        }
    }

    // MARK: - Favorites Section

    private var favoritesSection: some View {
        VStack(alignment: .leading, spacing: DesignTokens.spacingS) {
            SectionHeader(title: "CONTENT")

            NavigationLink {
                FavoritesView()
            } label: {
                SettingsRow(
                    icon: "heart",
                    title: "My Favorites",
                    showChevron: true
                )
            }
            .padding(DesignTokens.cardPadding)
            .background(AppColors.surface)
            .cornerRadius(DesignTokens.radiusM)
            .overlay(
                RoundedRectangle(cornerRadius: DesignTokens.radiusM)
                    .stroke(AppColors.border, lineWidth: DesignTokens.borderWidth)
            )
        }
    }

    // MARK: - Logout Section

    private var logoutSection: some View {
        Button(role: .destructive) {
            showLogoutConfirm = true
        } label: {
            HStack {
                Spacer()
                Text("Logout")
                    .font(AppTypography.button())
                Spacer()
            }
            .padding(.vertical, DesignTokens.spacingM)
            .background(AppColors.error.opacity(0.1))
            .cornerRadius(DesignTokens.radiusM)
            .overlay(
                RoundedRectangle(cornerRadius: DesignTokens.radiusM)
                    .stroke(AppColors.error.opacity(0.3), lineWidth: DesignTokens.borderWidth)
            )
        }
        .foregroundColor(AppColors.error)
        .padding(.top, DesignTokens.spacingM)
    }
}

// MARK: - Section Header

struct SectionHeader: View {
    let title: String

    var body: some View {
        Text(title)
            .font(AppTypography.monoCaption())
            .foregroundColor(AppColors.secondary)
            .padding(.leading, DesignTokens.spacingS)
    }
}

// MARK: - Settings Row

struct SettingsRow: View {
    let icon: String
    let title: String
    var value: String? = nil
    var showChevron: Bool = false

    var body: some View {
        HStack(spacing: DesignTokens.spacingM) {
            SettingsIcon(icon: icon)

            Text(title)
                .font(AppTypography.body())
                .foregroundColor(AppColors.primary)

            Spacer()

            if let value = value {
                Text(value)
                    .font(AppTypography.monoCaption())
                    .foregroundColor(AppColors.secondary)
            }

            if showChevron {
                Image(systemName: "chevron.right")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(AppColors.secondary)
            }
        }
        .padding(.vertical, DesignTokens.spacingS)
        .padding(.horizontal, DesignTokens.cardPadding)
    }
}

// MARK: - Settings Icon

struct SettingsIcon: View {
    let icon: String

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: DesignTokens.radiusS)
                .fill(AppColors.accent.opacity(0.1))
                .frame(width: 32, height: 32)

            Image(systemName: icon)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(AppColors.accent)
        }
    }
}

// MARK: - Category Selection View

struct CategorySelectionView: View {
    @Binding var selectedCategories: Set<String>
    @Environment(\.dismiss) var dismiss
    let onSave: () -> Void

    var body: some View {
        ScrollView {
            VStack(spacing: DesignTokens.spacingS) {
                ForEach(Constants.categories, id: \.self) { category in
                    Button {
                        if selectedCategories.contains(category) {
                            selectedCategories.remove(category)
                        } else {
                            selectedCategories.insert(category)
                        }
                    } label: {
                        HStack {
                            Text(category)
                                .font(AppTypography.body())
                                .foregroundColor(AppColors.primary)

                            Spacer()

                            if selectedCategories.contains(category) {
                                Image(systemName: "checkmark")
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(AppColors.accent)
                            }
                        }
                        .padding(DesignTokens.cardPadding)
                        .background(AppColors.surface)
                        .cornerRadius(DesignTokens.radiusM)
                        .overlay(
                            RoundedRectangle(cornerRadius: DesignTokens.radiusM)
                                .stroke(selectedCategories.contains(category) ? AppColors.accent : AppColors.border, lineWidth: DesignTokens.borderWidth)
                        )
                    }
                }
            }
            .padding(DesignTokens.spacingM)
        }
        .background(AppColors.background)
        .navigationTitle("Categories")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("Save") {
                    onSave()
                    dismiss()
                }
                .font(AppTypography.button())
                .foregroundColor(AppColors.accent)
            }
        }
    }
}

// MARK: - Favorites View

struct FavoritesView: View {
    @StateObject private var newsViewModel = NewsViewModel()

    var body: some View {
        Group {
            if newsViewModel.isLoading {
                LoadingStateView("Loading favorites...")
            } else if newsViewModel.favoriteNews.isEmpty {
                EmptyStateView(
                    icon: "heart.slash",
                    title: "No Favorites Yet",
                    subtitle: "Add articles to favorites from the news detail page"
                )
            } else {
                ScrollView {
                    LazyVStack(spacing: DesignTokens.spacingM) {
                        ForEach(newsViewModel.favoriteNews) { news in
                            NavigationLink(value: news) {
                                NewsCardView(news: news)
                            }
                            .buttonStyle(PlainButtonStyle())
                        }
                    }
                    .padding(DesignTokens.spacingM)
                }
                .navigationDestination(for: News.self) { news in
                    NewsDetailView(news: news)
                        .environmentObject(newsViewModel)
                }
            }
        }
        .background(AppColors.background)
        .navigationTitle("Favorites")
        .task {
            await newsViewModel.loadFavorites()
        }
    }
}

#Preview {
    SettingsView()
        .environmentObject(AuthViewModel())
}