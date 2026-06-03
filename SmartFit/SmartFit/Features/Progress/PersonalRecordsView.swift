import SwiftUI

struct PersonalRecordsView: View {
    let items: [PersonalRecordItem]

    var body: some View {
        AppCard(cornerRadius: 24, padding: 20) {
            VStack(alignment: .leading, spacing: 16) {
                SectionHeader(title: "Personal Records", subtitle: "Best logged lifts")

                if items.isEmpty {
                    Text("No personal records yet.")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.textSecondary)
                } else {
                    ForEach(items) { item in
                        HStack(alignment: .top, spacing: 12) {
                            Image(systemName: "trophy.fill")
                                .foregroundStyle(AppColors.secondary)
                                .frame(width: 30, height: 30)
                                .background(AppColors.secondary.opacity(0.14))
                                .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
                            VStack(alignment: .leading, spacing: 6) {
                                Text(item.exerciseName)
                                    .font(AppTypography.body.weight(.semibold))
                                Text("\(weightText(item)) • \(oneRepMaxText(item))")
                                    .font(AppTypography.caption)
                                    .foregroundStyle(AppColors.textSecondary)
                                if let achievedAt = item.achievedAt {
                                    Text(Self.displayDateTime(from: achievedAt))
                                        .font(AppTypography.caption)
                                        .foregroundStyle(AppColors.textSecondary)
                                }
                            }
                            Spacer()
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.bottom, 8)
                    }
                }
            }
        }
    }

    private func weightText(_ item: PersonalRecordItem) -> String {
        let weight = item.bestWeight.map { String(format: "%.0f kg", $0) } ?? "-"
        let reps = item.bestReps.map(String.init) ?? "-"
        return "\(weight) x \(reps)"
    }

    private func oneRepMaxText(_ item: PersonalRecordItem) -> String {
        guard let estimatedOneRepMax = item.estimatedOneRepMax else { return "1RM -"}
        return "1RM \(String(format: "%.1f", estimatedOneRepMax)) kg"
    }

    private static func displayDateTime(from raw: String) -> String {
        let formatters = WorkoutDateFormatting.apiFormatters
        for formatter in formatters {
            if let date = formatter.date(from: raw) {
                return date.formatted(date: .abbreviated, time: .shortened)
            }
        }
        return raw
    }
}

#if DEBUG
struct PersonalRecordsView_Previews: PreviewProvider {
    static var previews: some View {
        PersonalRecordsView(items: [.mock])
            .padding()
            .background(AppColors.background)
            .preferredColorScheme(.dark)
    }
}
#endif
