import SwiftUI

struct ReplacementEquipmentSelector: View {
    @Binding var selection: Set<String>

    let options: [String]

    private let columns = [
        GridItem(.flexible(), spacing: 10),
        GridItem(.flexible(), spacing: 10),
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Available Equipment")
                .font(AppTypography.title)

            LazyVGrid(columns: columns, spacing: 10) {
                ForEach(options, id: \.self) { equipment in
                    Button {
                        toggle(equipment)
                    } label: {
                        HStack(spacing: 8) {
                            Image(systemName: selection.contains(equipment) ? "checkmark.circle.fill" : "circle")
                                .font(.system(size: 15, weight: .semibold))
                            Text(label(for: equipment))
                                .lineLimit(2)
                                .multilineTextAlignment(.leading)
                        }
                        .font(AppTypography.caption.weight(.semibold))
                        .foregroundStyle(selection.contains(equipment) ? AppColors.textInverse : AppColors.textPrimary)
                        .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
                        .padding(.horizontal, 10)
                        .background(selection.contains(equipment) ? AppColors.primary : AppColors.surfaceElevated)
                        .overlay(
                            RoundedRectangle(cornerRadius: 12, style: .continuous)
                                .stroke(selection.contains(equipment) ? AppColors.primary : AppColors.border, lineWidth: 1)
                        )
                        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
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
        switch value {
        case "cable_machine":
            return "Cable Machine"
        case "smith_machine":
            return "Smith Machine"
        case "pull_up_bar":
            return "Pull-up Bar"
        case "resistance_band":
            return "Resistance Band"
        default:
            return value.replacingOccurrences(of: "_", with: " ").capitalized
        }
    }
}

#if DEBUG
struct ReplacementEquipmentSelector_Previews: PreviewProvider {
    struct PreviewContainer: View {
        @State private var equipment: Set<String> = ["bodyweight", "dumbbell"]

        var body: some View {
            ReplacementEquipmentSelector(
                selection: $equipment,
                options: [
                    "dumbbell",
                    "barbell",
                    "bench",
                    "cable_machine",
                    "machine",
                    "smith_machine",
                    "pull_up_bar",
                    "resistance_band",
                    "treadmill",
                    "bodyweight",
                ]
            )
            .padding()
            .background(AppColors.background)
        }
    }

    static var previews: some View {
        PreviewContainer()
            .preferredColorScheme(.dark)
    }
}
#endif
