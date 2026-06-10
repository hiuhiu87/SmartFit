import SwiftUI

struct Chip: View {
    let title: String
    var systemImage: String?
    var tint: Color = AppColors.primary

    var body: some View {
        HStack(spacing: AppSpacing.xs) {
            if let systemImage {
                Image(systemName: systemImage)
                    .font(.system(size: 12, weight: .semibold))
            }
            Text(title)
                .font(AppTypography.caption.weight(.semibold))
                .lineLimit(1)
        }
        .foregroundStyle(tint)
        .padding(.horizontal, AppSpacing.md)
        .padding(.vertical, AppSpacing.sm)
        .background(tint.opacity(0.12))
        .overlay(
            RoundedRectangle(cornerRadius: AppRadius.chip, style: .continuous)
                .stroke(tint.opacity(0.30), lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: AppRadius.chip, style: .continuous))
    }
}

struct SelectableChip: View {
    let title: String
    var systemImage: String?
    var isSelected: Bool
    var action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: AppSpacing.xs) {
                if let systemImage {
                    Image(systemName: systemImage)
                        .font(.system(size: 12, weight: .semibold))
                }
                Text(title)
                    .font(AppTypography.caption.weight(.semibold))
                    .lineLimit(1)
            }
            .foregroundStyle(isSelected ? AppColors.textInverse : AppColors.textPrimary)
            .padding(.horizontal, AppSpacing.md)
            .padding(.vertical, AppSpacing.sm)
            .background(isSelected ? AppColors.primary : AppColors.surfaceElevated)
            .overlay(
                RoundedRectangle(cornerRadius: AppRadius.chip, style: .continuous)
                    .stroke(isSelected ? AppColors.primary.opacity(0.4) : AppColors.border, lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: AppRadius.chip, style: .continuous))
        }
        .buttonStyle(.plain)
        .animation(AppAnimation.quick, value: isSelected)
    }
}

struct Chip_Previews: PreviewProvider {
    static var previews: some View {
        ZStack {
            AppColors.background.ignoresSafeArea()
            HStack(spacing: AppSpacing.sm) {
                Chip(title: "Upper", systemImage: "figure.strengthtraining.traditional")
                SelectableChip(title: "Selected", isSelected: true) {}
                SelectableChip(title: "Rest", isSelected: false) {}
            }
            .padding(AppSpacing.xxl)
        }
        .preferredColorScheme(.dark)
        .previewDisplayName("Chips")
    }
}
