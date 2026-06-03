import SwiftUI

struct GoalSelectionView: View {
    @ObservedObject var viewModel: OnboardingViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Choose the training outcome you want the app to optimize first.")
                .font(AppTypography.body)
                .foregroundStyle(AppColors.textSecondary)

            ForEach(viewModel.goalOptions) { option in
                SelectableCard(
                    title: option.title,
                    subtitle: option.subtitle,
                    isSelected: viewModel.selectedGoal == option.id
                ) {
                    viewModel.selectedGoal = option.id
                }
            }
        }
    }
}
