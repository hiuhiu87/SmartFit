import SwiftUI

struct WorkoutHistoryRowView: View {
    let item: WorkoutHistoryItem

    var body: some View {
        AppCard(cornerRadius: 20, padding: 18) {
            VStack(alignment: .leading, spacing: 12) {
                HStack(alignment: .top, spacing: 12) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(item.title)
                            .font(AppTypography.title)
                            .lineLimit(2)
                        if let date = item.date {
                            Text(Self.displayDate(from: date))
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.textSecondary)
                        }
                    }

                    Spacer(minLength: 8)

                    VStack(alignment: .trailing, spacing: 8) {
                        StatusBadge(title: item.statusLabel, color: statusColor)
                        if let source = item.source {
                            StatusBadge(title: item.sourceBadgeTitle, color: source == "ai" ? AppColors.primary : AppColors.textSecondary)
                        }
                    }
                }

                HStack(spacing: 12) {
                    detailPill(item.focusMuscle?.replacingOccurrences(of: "_", with: " ").capitalized ?? "Unknown")
                    if let durationMinutes = item.durationMinutes {
                        detailPill("\(durationMinutes) min")
                    }
                    if let totalVolume = item.totalVolume {
                        detailPill("\(Int(totalVolume)) kg")
                    }
                }
            }
        }
    }

    private var statusColor: Color {
        switch item.status {
        case "completed":
            return AppColors.success
        case "started":
            return AppColors.warning
        default:
            return AppColors.surfaceMuted
        }
    }

    private func detailPill(_ title: String) -> some View {
        Text(title)
            .font(AppTypography.caption)
            .foregroundStyle(AppColors.textPrimary)
            .padding(.horizontal, 10)
            .padding(.vertical, 8)
            .background(AppColors.surfaceElevated)
            .clipShape(Capsule())
    }

    private static func displayDate(from raw: String) -> String {
        let input = DateFormatter()
        input.dateFormat = "yyyy-MM-dd"
        input.locale = Locale(identifier: "en_US_POSIX")
        if let date = input.date(from: raw) {
            return date.formatted(date: .abbreviated, time: .omitted)
        }
        return raw
    }
}

#if DEBUG
struct WorkoutHistoryRowView_Previews: PreviewProvider {
    static var previews: some View {
        WorkoutHistoryRowView(item: .mockCompleted)
            .padding()
            .background(AppColors.background)
            .preferredColorScheme(.dark)
    }
}
#endif
