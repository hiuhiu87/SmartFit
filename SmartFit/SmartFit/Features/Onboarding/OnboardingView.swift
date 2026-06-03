import SwiftUI

struct OnboardingView: View {
    @EnvironmentObject private var appState: AppState
    @StateObject private var viewModel = OnboardingViewModel()

    var body: some View {
        VStack(spacing: 0) {
            header
            Divider()
            ScrollView {
                VStack(spacing: 24) {
                    content
                    if let errorMessage = viewModel.errorMessage {
                        Text(errorMessage)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.error)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
                .padding(24)
            }
            footer
        }
        .background(AppColors.background.ignoresSafeArea())
        .onAppear {
            viewModel.configure(appState: appState)
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Set up your coach")
                .font(AppTypography.title)
            Text(viewModel.currentStep.title)
                .font(AppTypography.body)
                .foregroundStyle(AppColors.textSecondary)
            ProgressView(value: Double(viewModel.currentStep.rawValue + 1), total: Double(OnboardingViewModel.Step.allCases.count))
                .tint(AppColors.primary)
        }
        .padding(24)
    }

    @ViewBuilder
    private var content: some View {
        switch viewModel.currentStep {
        case .goal:
            GoalSelectionView(viewModel: viewModel)
        case .trainingLevel:
            TrainingLevelView(viewModel: viewModel)
        case .schedule:
            ScheduleSetupView(viewModel: viewModel)
        case .equipment:
            EquipmentSetupView(viewModel: viewModel)
        case .safety:
            SafetyDisclaimerView(viewModel: viewModel)
        }
    }

    private var footer: some View {
        VStack(spacing: 12) {
            if viewModel.currentStep == .safety {
                PrimaryButton(title: "Finish Setup", isLoading: viewModel.isSubmitting) {
                    Task { await viewModel.submitOnboarding() }
                }
            } else {
                PrimaryButton(title: "Continue") {
                    viewModel.goToNextStep()
                }
            }

            if viewModel.currentStep.rawValue > 0 {
                Button("Back") {
                    viewModel.goToPreviousStep()
                }
                .font(AppTypography.body.weight(.semibold))
                .foregroundStyle(AppColors.textSecondary)
            }
        }
        .padding(24)
    }
}
