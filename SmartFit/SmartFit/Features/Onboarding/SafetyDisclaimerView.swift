import SwiftUI

struct SafetyDisclaimerView: View {
    @ObservedObject var viewModel: OnboardingViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("SmartFit is coaching software, not a medical device. Stop training and seek professional care if you feel sharp pain, dizziness, numbness, or unusual symptoms.")
                .font(AppTypography.body)
                .foregroundStyle(AppColors.textPrimary)
                .padding(20)
                .background(AppColors.surface)
                .overlay(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .stroke(AppColors.border, lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))

            Toggle(isOn: $viewModel.acceptedSafetyDisclaimer) {
                Text("I understand that recommendations are for fitness guidance only.")
                    .font(AppTypography.body)
            }
            .tint(AppColors.primary)
        }
    }
}
