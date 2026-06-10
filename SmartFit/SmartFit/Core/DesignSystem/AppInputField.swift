import SwiftUI

struct AppInputField<Content: View>: View {
    var cornerRadius: CGFloat = AppRadius.input
    @ViewBuilder let content: Content

    var body: some View {
        content
            .padding(AppSpacing.lg)
            .background(AppColors.surfaceElevated)
            .overlay(
                RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                    .stroke(AppColors.border, lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
    }
}
