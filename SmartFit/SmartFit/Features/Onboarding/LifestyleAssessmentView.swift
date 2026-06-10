import SwiftUI

struct LifestyleAssessmentView: View {
    @ObservedObject var viewModel: OnboardingViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("There is no right answer. This simply helps SmartFit balance training with the movement already in your day.")
                .font(AppTypography.body)
                .foregroundStyle(AppColors.textSecondary)

            ForEach(viewModel.lifestyleOptions) { option in
                SelectableCard(
                    title: option.title,
                    subtitle: option.subtitle,
                    isSelected: viewModel.selectedLifestyleType == option.id
                ) {
                    viewModel.selectedLifestyleType = option.id
                }
            }

            if viewModel.selectedLifestyleType != nil {
                VStack(alignment: .leading, spacing: 12) {
                    Text("About \(viewModel.sittingHoursPerDay.formatted(.number.precision(.fractionLength(0...1)))) sitting hours per day")
                        .font(AppTypography.body.weight(.semibold))
                    Slider(value: $viewModel.sittingHoursPerDay, in: 0...16, step: 0.5)
                        .tint(AppColors.primary)
                    Text("An estimate is enough. This helps us include appropriate posture, core, and mobility work.")
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
