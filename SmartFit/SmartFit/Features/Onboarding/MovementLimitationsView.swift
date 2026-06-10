import SwiftUI

struct MovementLimitationsView: View {
    @ObservedObject var viewModel: OnboardingViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Select anything that regularly feels uncomfortable. SmartFit will use this to choose more suitable exercise options, not to diagnose a condition.")
                .font(AppTypography.body)
                .foregroundStyle(AppColors.textSecondary)

            ForEach(viewModel.limitationOptions) { option in
                SelectableCard(
                    title: option.title,
                    subtitle: option.subtitle,
                    isSelected: viewModel.selectedLimitations.contains(option.id)
                ) {
                    viewModel.toggleLimitation(option.id)
                }
            }

            Text("Stop exercising and seek appropriate medical advice for sharp, worsening, or unexplained pain.")
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.textSecondary)
        }
    }
}
