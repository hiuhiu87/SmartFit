import SwiftUI

struct TrainingHistoryView: View {
    @ObservedObject var viewModel: OnboardingViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Choose the description that feels closest today. Your plan can change as your routine develops.")
                .font(AppTypography.body)
                .foregroundStyle(AppColors.textSecondary)

            ForEach(viewModel.trainingHistoryOptions) { option in
                SelectableCard(
                    title: option.title,
                    subtitle: option.subtitle,
                    isSelected: viewModel.selectedTrainingHistory == option.id
                ) {
                    viewModel.selectTrainingHistory(option.id)
                }
            }

            if viewModel.selectedTrainingHistory == "returning_after_break" {
                VStack(alignment: .leading, spacing: 12) {
                    Text("About \(viewModel.monthsInactive) months away from regular training")
                        .font(AppTypography.body.weight(.semibold))
                    Stepper(
                        "Adjust time away",
                        value: $viewModel.monthsInactive,
                        in: 0...60
                    )
                    .font(AppTypography.body)
                    Text("This helps us start with moderate volume and comfortable exercise choices.")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                }
                .padding(18)
                .background(AppColors.surface)
                .overlay(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .stroke(AppColors.border, lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
            }
        }
    }
}
