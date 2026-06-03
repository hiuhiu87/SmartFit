import SwiftUI

struct GenerationModePicker: View {
    @Binding var selection: String

    private let options: [(value: String, title: String, subtitle: String)] = [
        ("auto", "Auto", "AI first, safe fallback"),
        ("gemini", "Gemini", "AI only"),
        ("rule_based", "Rule-based", "No AI"),
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Generation mode")
                .font(AppTypography.title)

            ForEach(options, id: \.value) { option in
                SelectableCard(
                    title: option.title,
                    subtitle: option.subtitle,
                    isSelected: selection == option.value,
                    action: { selection = option.value }
                )
            }
        }
    }
}
