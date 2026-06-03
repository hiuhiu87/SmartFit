import SwiftUI

struct EquipmentSetupView: View {
    @ObservedObject var viewModel: OnboardingViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Pick everything you can usually access. This is used for workout generation and replacement suggestions.")
                .font(AppTypography.body)
                .foregroundStyle(AppColors.textSecondary)

            ForEach(viewModel.equipmentOptions) { option in
                SelectableCard(
                    title: option.title,
                    subtitle: option.subtitle,
                    isSelected: viewModel.selectedEquipment.contains(option.id)
                ) {
                    viewModel.toggleEquipment(option.id)
                }
            }
        }
    }
}
