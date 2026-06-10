import SwiftUI

struct ProgramWorkoutRowView: View {
    let workout: ProgramCalendarDay
    let onSelect: () -> Void

    var body: some View {
        Button(action: onSelect) {
            HStack(spacing: 16) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(formatDate(workout.date))
                        .font(AppTypography.caption.weight(.semibold))
                        .foregroundStyle(isToday ? AppColors.primary : AppColors.textSecondary)
                    
                    Text(workout.title)
                        .font(AppTypography.body.weight(.semibold))
                        .foregroundStyle(AppColors.textPrimary)
                    
                    if let focus = workout.focusType {
                        Text(focus.programDisplayName)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.textSecondary)
                    }
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 6) {
                    if let phase = workout.phase {
                        ProgramPhaseBadge(phase: phase)
                    }
                    
                    StatusBadge(
                        title: workout.status.programDisplayName,
                        color: statusColor
                    )
                }
                
                Image(systemName: "chevron.right")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(AppColors.textSecondary)
            }
            .padding(.vertical, 14)
            .padding(.horizontal, 16)
            .background(isToday ? AppColors.surfaceElevated : AppColors.surface)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .stroke(isToday ? AppColors.primary.opacity(0.4) : Color.clear, lineWidth: 1.5)
            )
        }
        .buttonStyle(.plain)
    }

    private var isToday: Bool {
        workout.status.lowercased() == "today" || workout.status.lowercased() == "scheduled_today"
    }

    private var statusColor: Color {
        switch workout.status.lowercased() {
        case "completed": return AppColors.success
        case "skipped": return AppColors.warning
        case "started", "today": return AppColors.secondary
        default: return AppColors.textSecondary
        }
    }

    private func formatDate(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter.smartFitDate
        guard let date = formatter.date(from: dateString) else { return dateString }
        
        let outputFormatter = DateFormatter()
        outputFormatter.dateFormat = "EEE, MMM d"
        return outputFormatter.string(from: date)
    }
}
