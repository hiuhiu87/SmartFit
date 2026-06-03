import SwiftUI

struct EquipmentSelectorView: View {
    @Binding var selection: Set<String>

    let options: [String]

    private let columns = [
        GridItem(.flexible(), spacing: 12),
        GridItem(.flexible(), spacing: 12),
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Equipment")
                .font(AppTypography.title)

            LazyVGrid(columns: columns, spacing: 12) {
                ForEach(options, id: \.self) { equipment in
                    Button {
                        toggle(equipment)
                    } label: {
                        Text(label(for: equipment))
                            .font(AppTypography.body.weight(.semibold))
                            .foregroundStyle(selection.contains(equipment) ? AppColors.textInverse : AppColors.textPrimary)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 14)
                            .background(selection.contains(equipment) ? AppColors.primary : AppColors.surfaceElevated)
                            .overlay(
                                RoundedRectangle(cornerRadius: 16, style: .continuous)
                                    .stroke(selection.contains(equipment) ? AppColors.primary : AppColors.border, lineWidth: 1)
                            )
                            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    private func toggle(_ item: String) {
        if selection.contains(item) {
            selection.remove(item)
        } else {
            selection.insert(item)
        }
    }

    private func label(for value: String) -> String {
        value.replacingOccurrences(of: "_", with: " ").capitalized
    }
}
