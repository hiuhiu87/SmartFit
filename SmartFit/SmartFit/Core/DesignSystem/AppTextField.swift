import SwiftUI

struct AppTextField: View {
    let title: String
    @Binding var text: String
    var prompt: String?
    var systemImage: String?
    var axis: Axis = .horizontal

    var body: some View {
        AppInputField {
            HStack(alignment: axis == .vertical ? .top : .center, spacing: AppSpacing.md) {
                if let systemImage {
                    Image(systemName: systemImage)
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundStyle(AppColors.textSecondary)
                        .frame(width: AppSpacing.xl)
                }
                VStack(alignment: .leading, spacing: AppSpacing.xs) {
                    Text(title)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                    TextField(prompt ?? title, text: $text, axis: axis)
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.textPrimary)
                        .tint(AppColors.primary)
                }
            }
        }
    }
}

struct AppTextField_Previews: PreviewProvider {
    static var previews: some View {
        AppTextFieldPreview()
            .previewDisplayName("AppTextField")
    }
}

private struct AppTextFieldPreview: View {
    @State private var text = "Mobility note"

    var body: some View {
        ZStack {
            AppColors.background.ignoresSafeArea()
            AppTextField(
                title: "Notes",
                text: $text,
                prompt: "Add context",
                systemImage: "note.text",
                axis: .vertical
            )
            .padding(AppSpacing.xxl)
        }
        .preferredColorScheme(.dark)
    }
}
