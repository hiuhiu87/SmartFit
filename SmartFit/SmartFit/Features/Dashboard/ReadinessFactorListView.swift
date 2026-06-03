import SwiftUI

struct ReadinessFactorListView: View {
    let readiness: ReadinessResponse

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            SectionHeader(title: "Top Factors", subtitle: "What shaped today’s score")

            AppCard(cornerRadius: 18, padding: 16, background: AppColors.surfaceElevated) {
                VStack(spacing: 14) {
                    ForEach(factors.prefix(5), id: \.title) { factor in
                        HStack(alignment: .top, spacing: 12) {
                            Circle()
                                .fill(AppColors.primary.opacity(0.18))
                                .frame(width: 10, height: 10)
                                .padding(.top, 7)
                            VStack(alignment: .leading, spacing: 4) {
                                Text(factor.title)
                                    .font(AppTypography.body.weight(.semibold))
                                Text(factor.message)
                                    .font(AppTypography.caption)
                                    .foregroundStyle(AppColors.textSecondary)
                                    .lineLimit(2)
                            }
                            Spacer()
                        }
                        if factor.title != factors.prefix(5).last?.title {
                            Divider().overlay(AppColors.border)
                        }
                    }
                }
            }
        }
    }

    private var factors: [(title: String, message: String)] {
        if let factorBreakdown = readiness.factorBreakdown, !factorBreakdown.isEmpty {
            return factorBreakdown
                .sorted { $0.key < $1.key }
                .map {
                    (
                        title: $0.key.replacingOccurrences(of: "_", with: " ").capitalized,
                        message: $0.value.message ?? $0.value.impact ?? "No additional detail."
                    )
                }
        }

        return [
            ("Sleep", "Sleep quality and duration shape today’s readiness score."),
            ("HRV", "HRV contributes when Apple Health has enough recovery data."),
            ("Resting Heart Rate", "Elevated resting heart rate can lower confidence or readiness."),
            ("Recent Load", "Recent load is estimated conservatively until workout data accumulates."),
            ("Self Report", "Manual check-in can refine the score when health signals are limited."),
        ]
    }
}
