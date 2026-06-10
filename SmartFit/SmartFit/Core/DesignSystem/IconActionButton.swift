import SwiftUI

struct IconActionButton: View {
    let systemName: String
    let title: String
    var tint: Color = AppColors.textPrimary
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: systemName)
                .font(.system(size: 17, weight: .semibold))
                .foregroundStyle(tint)
                .frame(width: AppSpacing.huge + AppSpacing.sm, height: AppSpacing.huge + AppSpacing.sm)
                .background(AppColors.surfaceElevated)
                .overlay(
                    RoundedRectangle(cornerRadius: AppRadius.button, style: .continuous)
                        .stroke(AppColors.border, lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: AppRadius.button, style: .continuous))
        }
        .buttonStyle(.plain)
        .accessibilityLabel(title)
    }
}
