import SwiftUI

struct RegisterView: View {
    @EnvironmentObject var authViewModel: AuthViewModel
    @Environment(\.dismiss) var dismiss
    @State private var email = ""
    @State private var password = ""
    @State private var confirmPassword = ""
    @State private var nickname = ""

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: DesignTokens.spacingL) {
                    // Header
                    headerSection

                    // Form
                    formSection

                    // Error Message
                    if let error = authViewModel.errorMessage {
                        Text(error)
                            .font(AppTypography.monoCaption())
                            .foregroundColor(AppColors.error)
                            .padding(.horizontal)
                    }
                }
                .padding(DesignTokens.spacingM)
            }
            .background(AppColors.background)
            .navigationTitle("Create Account")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                    .foregroundColor(AppColors.secondary)
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Register") {
                        Task {
                            await authViewModel.register(
                                email: email,
                                password: password,
                                nickname: nickname.isEmpty ? nil : nickname
                            )
                        }
                    }
                    .font(AppTypography.button())
                    .foregroundColor(isValidForm ? AppColors.accent : AppColors.secondary)
                    .disabled(!isValidForm || authViewModel.isLoading)
                }
            }
            .overlay {
                if authViewModel.isLoading {
                    ZStack {
                        Color.black.opacity(0.3)
                            .ignoresSafeArea()

                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: AppColors.accent))
                            .scaleEffect(1.5)
                            .padding(DesignTokens.spacingL)
                            .background(AppColors.surface)
                            .cornerRadius(DesignTokens.radiusM)
                    }
                }
            }
        }
    }

    // MARK: - Header Section

    private var headerSection: some View {
        VStack(spacing: DesignTokens.spacingS) {
            ZStack {
                RoundedRectangle(cornerRadius: DesignTokens.radiusS)
                    .stroke(AppColors.accent, lineWidth: 1)
                    .frame(width: 48, height: 48)

                Image(systemName: "person.badge.plus")
                    .font(.system(size: 20, weight: .light))
                    .foregroundColor(AppColors.accent)
            }

            Text("Create your account to get started")
                .font(AppTypography.caption())
                .foregroundColor(AppColors.secondary)
        }
    }

    // MARK: - Form Section

    private var formSection: some View {
        VStack(spacing: DesignTokens.spacingM) {
            // Email Field
            FormField(label: "EMAIL", text: $email, keyboardType: .emailAddress)

            // Password Field
            FormField(label: "PASSWORD", text: $password, isSecure: true)

            // Confirm Password Field
            FormField(label: "CONFIRM PASSWORD", text: $confirmPassword, isSecure: true)

            // Nickname Field
            FormField(label: "NICKNAME (OPTIONAL)", text: $nickname)
        }
        .padding(DesignTokens.cardPadding)
        .background(AppColors.surface)
        .cornerRadius(DesignTokens.radiusM)
        .overlay(
            RoundedRectangle(cornerRadius: DesignTokens.radiusM)
                .stroke(AppColors.border, lineWidth: DesignTokens.borderWidth)
        )
    }

    // MARK: - Validation

    private var isValidForm: Bool {
        !email.isEmpty &&
        !password.isEmpty &&
        password == confirmPassword &&
        password.count >= 6
    }
}

// MARK: - Form Field

struct FormField: View {
    let label: String
    @Binding var text: String
    var isSecure: Bool = false
    var keyboardType: UIKeyboardType = .default

    var body: some View {
        VStack(alignment: .leading, spacing: DesignTokens.spacingXS) {
            Text(label)
                .font(AppTypography.monoCaption())
                .foregroundColor(AppColors.secondary)

            if isSecure {
                SecureField("", text: $text)
                    .textFieldStyle(UnderlinedTextFieldStyle())
            } else {
                TextField("", text: $text)
                    .textFieldStyle(UnderlinedTextFieldStyle())
                    .textInputAutocapitalization(.never)
                    .keyboardType(keyboardType)
                    .autocorrectionDisabled()
            }
        }
    }
}

#Preview {
    RegisterView()
        .environmentObject(AuthViewModel())
}