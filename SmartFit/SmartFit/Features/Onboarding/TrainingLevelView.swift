import SwiftUI

struct TrainingLevelView: View {
    @ObservedObject var viewModel: OnboardingViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("This helps tune exercise complexity and readiness-based decisions.")
                .font(AppTypography.body)
                .foregroundStyle(AppColors.textSecondary)

            ForEach(viewModel.trainingLevelOptions) { option in
                SelectableCard(
                    title: option.title,
                    subtitle: option.subtitle,
                    isSelected: viewModel.selectedTrainingLevel == option.id
                ) {
                    viewModel.selectedTrainingLevel = option.id
                }
            }
        }
    }
}
