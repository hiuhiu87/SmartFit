import SwiftUI

struct TrainingStyleView: View {
    @ObservedObject var viewModel: OnboardingViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 24) {
            Text("What kind of training do you prefer?")
                .font(AppTypography.title)

            VStack(spacing: 12) {
                ForEach(viewModel.trainingStyleOptions) { option in
                    SelectableCard(
                        title: option.title,
                        subtitle: option.subtitle,
                        isSelected: viewModel.selectedTrainingStyle == option.id
                    ) {
                        viewModel.selectedTrainingStyle = option.id
                    }
                }
            }
        }
    }
}
