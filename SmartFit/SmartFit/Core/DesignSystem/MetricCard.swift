import SwiftUI

struct MetricCard: View {
    let title: String
    let value: String
    var subtitle: String?
    var tint: Color = AppColors.primary

    var body: some View {
        AppCard(cornerRadius: AppRadius.card, padding: AppSpacing.lg, background: AppColors.surfaceElevated) {
            VStack(alignment: .leading, spacing: AppSpacing.sm) {
                Text(title)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.textSecondary)
                Text(value)
                    .font(AppTypography.metric)
                    .foregroundStyle(tint)
                    .lineLimit(1)
                    .minimumScaleFactor(0.75)
                if let subtitle {
                    Text(subtitle)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                        .lineLimit(2)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}

struct MetricCard_Previews: PreviewProvider {
    static var previews: some View {
        ZStack {
            AppColors.background.ignoresSafeArea()
            HStack(spacing: AppSpacing.md) {
                MetricCard(title: "Readiness", value: "86%", subtitle: "Ready", tint: AppColors.success)
                MetricCard(title: "Volume", value: "12.4k", subtitle: "This week", tint: AppColors.primary)
            }
            .padding(AppSpacing.xxl)
        }
        .preferredColorScheme(.dark)
        .previewDisplayName("MetricCard")
    }
}
