import SwiftUI

struct WeeklyStructureView: View {
    let templates: [ProgramWorkoutTemplate]
    var currentDayIndex: Int?

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            SectionHeader(
                title: "Weekly Structure",
                subtitle: "\(templates.count) planned training days"
            )

            ForEach(templates.sorted(by: { $0.sequenceOrder < $1.sequenceOrder })) { template in
                HStack(spacing: 14) {
                    Text("\(template.dayIndex + 1)")
                        .font(AppTypography.body.weight(.bold))
                        .foregroundStyle(
                            currentDayIndex == template.dayIndex
                                ? AppColors.textInverse
                                : AppColors.primary
                        )
                        .frame(width: 36, height: 36)
                        .background(
                            currentDayIndex == template.dayIndex
                                ? AppColors.primary
                                : AppColors.primary.opacity(0.14)
                        )
                        .clipShape(Circle())

                    VStack(alignment: .leading, spacing: 4) {
                        Text(template.title)
                            .font(AppTypography.body.weight(.semibold))
                        Text(
                            "\(template.focusType.programDisplayName) · "
                                + "\(template.estimatedDurationMinutes) min"
                        )
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                    }
                    Spacer()
                    if currentDayIndex == template.dayIndex {
                        StatusBadge(title: "Today")
                    }
                }
                .padding(16)
                .background(AppColors.surface)
                .overlay(
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .stroke(
                            currentDayIndex == template.dayIndex
                                ? AppColors.primary.opacity(0.55)
                                : AppColors.border,
                            lineWidth: 1
                        )
                )
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            }
        }
    }
}
