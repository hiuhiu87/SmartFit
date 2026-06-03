import SwiftUI

struct AuthFormContainer<Content: View>: View {
    let title: String
    let subtitle: String
    @ViewBuilder let content: Content

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                Text(title)
                    .font(AppTypography.title)
                Text(subtitle)
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.textSecondary)
                VStack(spacing: 16) {
                    content
                }
            }
            .padding(24)
        }
        .background(AppColors.background.ignoresSafeArea())
    }
}

private struct AuthFieldModifier: ViewModifier {
    func body(content: Content) -> some View {
        AppInputField {
            content
        }
    }
}

extension View {
    func authFieldStyle() -> some View {
        modifier(AuthFieldModifier())
    }
}
