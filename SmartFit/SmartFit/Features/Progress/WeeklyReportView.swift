import SwiftUI

struct WeeklyReportView: View {
    let report: WeeklyReportResponse?

    var body: some View {
        AppCard(cornerRadius: 24, padding: 20) {
            VStack(alignment: .leading, spacing: 16) {
                SectionHeader(title: "Weekly Report", subtitle: "Calm coaching notes")

                if let report {
                    Text(report.summary)
                        .font(AppTypography.body.weight(.semibold))

                    if !report.highlights.isEmpty {
                        section("Highlights", items: report.highlights)
                    }

                    if !report.suggestions.isEmpty {
                        section("Suggestions", items: report.suggestions)
                    }
                } else {
                    Text("Weekly report is not available yet.")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.textSecondary)
                }
            }
        }
    }

    private func section(_ title: String, items: [String]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.textSecondary)
            ForEach(items, id: \.self) { item in
                HStack(alignment: .top, spacing: 8) {
                    Circle()
                        .fill(AppColors.primary)
                        .frame(width: 6, height: 6)
                        .padding(.top, 6)
                    Text(item)
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.textPrimary)
                }
            }
        }
    }
}

#if DEBUG
struct WeeklyReportView_Previews: PreviewProvider {
    static var previews: some View {
        WeeklyReportView(report: .mock)
            .padding()
            .background(AppColors.background)
            .preferredColorScheme(.dark)
    }
}
#endif
