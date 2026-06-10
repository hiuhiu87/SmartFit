import SwiftUI

struct StatusBadge: View {
    let title: String
    var color: Color = AppColors.primary

    var body: some View {
        Text(title)
            .font(AppTypography.caption.weight(.semibold))
            .foregroundStyle(color)
            .padding(.horizontal, AppSpacing.md)
            .padding(.vertical, AppSpacing.sm)
            .background(color.opacity(0.14))
            .overlay(
                RoundedRectangle(cornerRadius: AppRadius.chip, style: .continuous)
                    .stroke(color.opacity(0.35), lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: AppRadius.chip, style: .continuous))
    }
}

struct StatusBadge_Previews: PreviewProvider {
    static var previews: some View {
        ZStack {
            AppColors.background.ignoresSafeArea()
            HStack(spacing: AppSpacing.sm) {
                StatusBadge(title: "Ready", color: AppColors.success)
                StatusBadge(title: "Caution", color: AppColors.warning)
                StatusBadge(title: "Recovery", color: AppColors.info)
            }
            .padding(AppSpacing.xxl)
        }
        .preferredColorScheme(.dark)
        .previewDisplayName("StatusBadge")
    }
}
