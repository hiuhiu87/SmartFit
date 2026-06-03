import SwiftUI

struct ReplacementReasonPicker: View {
    @Binding var selection: String

    static let options: [ReplacementReasonOption] = [
        ReplacementReasonOption(value: "equipment_unavailable", label: "Equipment unavailable"),
        ReplacementReasonOption(value: "too_hard", label: "Too hard"),
        ReplacementReasonOption(value: "too_easy", label: "Too easy"),
        ReplacementReasonOption(value: "pain_or_discomfort", label: "Pain or discomfort"),
        ReplacementReasonOption(value: "dislike", label: "I do not like this exercise"),
        ReplacementReasonOption(value: "other", label: "Other"),
    ]

    private let columns = [
        GridItem(.flexible(), spacing: 10),
        GridItem(.flexible(), spacing: 10),
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Reason")
                .font(AppTypography.title)

            LazyVGrid(columns: columns, spacing: 10) {
                ForEach(Self.options, id: \.value) { option in
                    Button {
                        selection = option.value
                    } label: {
                        Text(option.label)
                            .font(AppTypography.caption.weight(.semibold))
                            .foregroundStyle(selection == option.value ? AppColors.textInverse : AppColors.textPrimary)
                            .frame(maxWidth: .infinity, minHeight: 44)
                            .padding(.horizontal, 10)
                            .background(selection == option.value ? AppColors.primary : AppColors.surfaceElevated)
                            .overlay(
                                RoundedRectangle(cornerRadius: 12, style: .continuous)
                                    .stroke(selection == option.value ? AppColors.primary : AppColors.border, lineWidth: 1)
                            )
                            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                    }
                    .buttonStyle(.plain)
                }
            }

            if selection == "pain_or_discomfort" {
                Text("If you feel pain, consider stopping this movement and choosing a lighter option.")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.warning)
                    .padding(12)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(AppColors.warning.opacity(0.12))
                    .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            }
        }
    }
}

struct ReplacementReasonOption: Hashable {
    let value: String
    let label: String
}

#if DEBUG
struct ReplacementReasonPicker_Previews: PreviewProvider {
    struct PreviewContainer: View {
        @State private var reason = "pain_or_discomfort"

        var body: some View {
            ReplacementReasonPicker(selection: $reason)
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
