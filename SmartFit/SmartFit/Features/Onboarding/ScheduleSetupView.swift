import SwiftUI

struct ScheduleSetupView: View {
    @ObservedObject var viewModel: OnboardingViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("How many days per week do you realistically want to train?")
                .font(AppTypography.body)
                .foregroundStyle(AppColors.textSecondary)

            VStack(alignment: .leading, spacing: 12) {
                Text("\(viewModel.trainingDaysPerWeek) days / week")
                    .font(AppTypography.title)
                Stepper(value: $viewModel.trainingDaysPerWeek, in: 1...7) {
                    Text("Adjust training frequency")
                        .font(AppTypography.body)
                }
            }
            .padding(20)
            .background(AppColors.surface)
            .overlay(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(AppColors.border, lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))

            Text("For MVP this is stored inside onboarding notes until a dedicated schedule field exists in the backend.")
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.textSecondary)
        }
    }
}
