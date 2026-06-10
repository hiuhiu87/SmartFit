import SwiftUI

struct OnboardingView: View {
    @Environment(\.dismiss) private var dismiss
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
        case .lifestyle:
            LifestyleAssessmentView(viewModel: viewModel)
        case .trainingHistory:
            TrainingHistoryView(viewModel: viewModel)
        case .limitations:
            MovementLimitationsView(viewModel: viewModel)
        case .trainingStyle:
            TrainingStyleView(viewModel: viewModel)
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
                    Task {
                        if await viewModel.submitOnboarding() {
                            dismiss()
                        }
                    }
                }
            } else {
                PrimaryButton(title: "Continue") {
                    viewModel.goToNextStep()
                }
            }

            if viewModel.currentStep.isOptionalAssessment {
                Button("Skip for now") {
                    viewModel.goToNextStep()
                }
                .font(AppTypography.body.weight(.semibold))
                .foregroundStyle(AppColors.textSecondary)
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

private extension OnboardingViewModel.Step {
    var isOptionalAssessment: Bool {
        self == .lifestyle || self == .trainingHistory || self == .limitations
    }
}
