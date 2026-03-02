import SwiftUI

struct LoginView: View {
    @EnvironmentObject var authViewModel: AuthViewModel
    @State private var email = ""
    @State private var password = ""
    @State private var showRegister = false

    var body: some View {
        NavigationStack {
            VStack(spacing: DesignTokens.spacingXL) {
                Spacer()

                // Logo Section
                logoSection

                // Form Section
                formSection

                Spacer()

                // Register Link
                registerLink
            }
            .padding(DesignTokens.spacingL)
            .background(AppColors.background)
            .sheet(isPresented: $showRegister) {
                RegisterView()
                    .environmentObject(authViewModel)
            }
        }
    }

    // MARK: - Logo Section

    private var logoSection: some View {
        VStack(spacing: DesignTokens.spacingM) {
            // Terminal-style icon
            ZStack {
                RoundedRectangle(cornerRadius: DesignTokens.radiusM)
                    .stroke(AppColors.accent, lineWidth: 2)
                    .frame(width: 80, height: 80)

                Image(systemName: "terminal")
                    .font(.system(size: 36, weight: .light))
                    .foregroundColor(AppColors.accent)
            }

            // App Title
            VStack(spacing: 4) {
                Text("TECH NEWS")
                    .font(AppTypography.mono())
                    .foregroundColor(AppColors.accent)

                Text("Your daily tech digest")
                    .font(AppTypography.caption())
                    .foregroundColor(AppColors.secondary)
            }
        }
    }

    // MARK: - Form Section

    private var formSection: some View {
        VStack(spacing: DesignTokens.spacingM) {
            // Email Field
            VStack(alignment: .leading, spacing: DesignTokens.spacingXS) {
                Text("EMAIL")
                    .font(AppTypography.monoCaption())
                    .foregroundColor(AppColors.secondary)

                TextField("", text: $email)
                    .textFieldStyle(UnderlinedTextFieldStyle())
                    .textInputAutocapitalization(.never)
                    .keyboardType(.emailAddress)
                    .autocorrectionDisabled()
            }

            // Password Field
            VStack(alignment: .leading, spacing: DesignTokens.spacingXS) {
                Text("PASSWORD")
                    .font(AppTypography.monoCaption())
                    .foregroundColor(AppColors.secondary)

                SecureField("", text: $password)
                    .textFieldStyle(UnderlinedTextFieldStyle())
            }

            // Error Message
            if let error = authViewModel.errorMessage {
                Text(error)
                    .font(AppTypography.monoCaption())
                    .foregroundColor(AppColors.error)
                    .padding(.top, DesignTokens.spacingS)
            }

            // Login Button
            Button {
                Task {
                    await authViewModel.login(email: email, password: password)
                }
            } label: {
                HStack {
                    if authViewModel.isLoading {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: AppColors.background))
                    } else {
                        Text("LOGIN")
                            .font(AppTypography.button())
                    }
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, DesignTokens.spacingM)
                .background(AppColors.accent)
                .foregroundColor(AppColors.background)
                .cornerRadius(DesignTokens.radiusM)
            }
            .disabled(email.isEmpty || password.isEmpty || authViewModel.isLoading)
            .opacity(email.isEmpty || password.isEmpty ? 0.5 : 1)
        }
        .padding(.horizontal, DesignTokens.spacingS)
    }

    // MARK: - Register Link

    private var registerLink: some View {
        VStack(spacing: DesignTokens.spacingS) {
            Text("Don't have an account?")
                .font(AppTypography.caption())
                .foregroundColor(AppColors.secondary)

            Button {
                showRegister = true
            } label: {
                Text("CREATE ACCOUNT")
                    .font(AppTypography.mono())
                    .foregroundColor(AppColors.accent)
            }
        }
    }
}

// MARK: - Underlined Text Field Style

struct UnderlinedTextFieldStyle: TextFieldStyle {
    func _body(configuration: TextField<Self._Label>) -> some View {
        VStack(spacing: 0) {
            configuration
                .font(AppTypography.body())
                .foregroundColor(AppColors.primary)
                .padding(.vertical, DesignTokens.spacingS)

            Rectangle()
                .frame(height: 1)
                .foregroundColor(AppColors.border)
        }
    }
}

#Preview {
    LoginView()
        .environmentObject(AuthViewModel())
}