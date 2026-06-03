import SwiftUI

struct ReplacementOptionCard: View {
    let option: ReplacementOptionResponse
    var isApplying = false
    let onUse: () -> Void

    var body: some View {
        AppCard(cornerRadius: 18, padding: 16) {
            VStack(alignment: .leading, spacing: 12) {
                VStack(alignment: .leading, spacing: 6) {
                    Text(option.name)
                        .font(AppTypography.title)
                    Text("\(label(option.primaryMuscle)) • \(label(option.equipment))")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                }

                HStack(spacing: 10) {
                    metric("Sets", "\(option.targetSets)")
                    metric("Reps", option.targetReps)
                    metric("Rest", "\(option.restSeconds)s")
                    metric("RPE", option.targetRpe.map(String.init) ?? "-")
                }

                Text(option.reason)
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.textPrimary)

                if let safetyNote = option.safetyNote, !safetyNote.isEmpty {
                    Text(safetyNote)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.warning)
                }

                PrimaryButton(title: "Use This Exercise", isLoading: isApplying, action: onUse)
            }
        }
    }

    private func metric(_ title: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.textSecondary)
            Text(value)
                .font(AppTypography.body.weight(.semibold))
                .foregroundStyle(AppColors.textPrimary)
                .lineLimit(1)
                .minimumScaleFactor(0.8)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(10)
        .background(AppColors.surfaceElevated)
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
    }

    private func label(_ value: String) -> String {
        value.replacingOccurrences(of: "_", with: " ").capitalized
    }
}

#if DEBUG
struct ReplacementOptionCard_Previews: PreviewProvider {
    static var previews: some View {
        ReplacementOptionCard(option: .mockPushUp, onUse: {})
            .padding()
            .background(AppColors.background)
            .preferredColorScheme(.dark)
    }
}
#endif
