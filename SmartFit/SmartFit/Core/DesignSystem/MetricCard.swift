import SwiftUI

struct MetricCard: View {
    let title: String
    let value: String
    var subtitle: String?
    var tint: Color = AppColors.primary

    var body: some View {
        AppCard(cornerRadius: 16, padding: 16, background: AppColors.surfaceElevated) {
            VStack(alignment: .leading, spacing: 8) {
                Text(title)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.textSecondary)
                Text(value)
                    .font(.system(size: 28, weight: .bold, design: .rounded))
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
