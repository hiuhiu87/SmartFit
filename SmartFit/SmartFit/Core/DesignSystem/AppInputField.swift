import SwiftUI

struct AppInputField<Content: View>: View {
    var cornerRadius: CGFloat = 14
    @ViewBuilder let content: Content

    var body: some View {
        content
            .padding()
            .background(AppColors.surfaceElevated)
            .overlay(
                RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                    .stroke(AppColors.border, lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
    }
}
