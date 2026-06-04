import SwiftUI

struct CompleteWorkoutView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var difficultyFeedback = "just_right"
    @State private var energyAfter = 7
    @State private var notes = ""

    let isLoading: Bool
    let statusMessage: String?
    let metricsNote: String?
    let onSubmit: (_ difficultyFeedback: String, _ energyAfter: Int?, _ notes: String?) -> Void

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    Text("Finish Workout")
                        .font(AppTypography.hero)
                        .foregroundStyle(AppColors.textPrimary)
                    Text("Nice work. Your workout will be saved.")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.textSecondary)

                    if let statusMessage {
                        AppCard(cornerRadius: 18, padding: 14) {
                            HStack(spacing: 12) {
                                ProgressView()
                                    .tint(AppColors.primary)
                                Text(statusMessage)
                                    .font(AppTypography.body)
                                    .foregroundStyle(AppColors.textSecondary)
                            }
                        }
                    } else if let metricsNote {
                        AppCard(cornerRadius: 18, padding: 14) {
                            Text(metricsNote)
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.textSecondary)
                        }
                    }

                    AppCard(cornerRadius: 22, padding: 18) {
                        VStack(alignment: .leading, spacing: 14) {
                            Text("How did it feel?")
                                .font(AppTypography.title)

                            HStack(spacing: 10) {
                                chip("Too Easy", value: "too_easy", selection: $difficultyFeedback)
                                chip("Just Right", value: "just_right", selection: $difficultyFeedback)
                                chip("Too Hard", value: "too_hard", selection: $difficultyFeedback)
                            }
                        }
                    }

                    AppCard(cornerRadius: 22, padding: 18) {
                        VStack(alignment: .leading, spacing: 14) {
                            Text("Energy After")
                                .font(AppTypography.title)
                            Text("\(energyAfter)")
                                .font(AppTypography.metricNumber)
                                .foregroundStyle(AppColors.primary)
                            Slider(value: Binding(
                                get: { Double(energyAfter) },
                                set: { energyAfter = Int($0.rounded()) }
                            ), in: 1...10, step: 1)
                            .tint(AppColors.primary)
                            HStack {
                                Text("Low")
                                Spacer()
                                Text("Strong")
                            }
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.textSecondary)
                        }
                    }

                    AppCard(cornerRadius: 22, padding: 18) {
                        VStack(alignment: .leading, spacing: 14) {
                            Text("Notes")
                                .font(AppTypography.title)
                            AppInputField {
                                TextField("Anything worth remembering?", text: $notes, axis: .vertical)
                                    .lineLimit(4, reservesSpace: true)
                                    .font(AppTypography.body)
                            }
                        }
                    }

                    PrimaryButton(title: "Save Workout", isLoading: isLoading, systemImage: "checkmark") {
                        onSubmit(difficultyFeedback, energyAfter, notes.trimmingCharacters(in: .whitespacesAndNewlines).nilIfEmpty)
                    }
                }
                .padding(24)
            }
            .background(AppColors.background.ignoresSafeArea())
            .navigationTitle("Complete Workout")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Close") { dismiss() }
                }
            }
        }
    }

    private func chip(_ title: String, value: String, selection: Binding<String>) -> some View {
        Button {
            selection.wrappedValue = value
        } label: {
            Text(title)
                .font(AppTypography.caption.weight(.semibold))
                .foregroundStyle(selection.wrappedValue == value ? AppColors.textInverse : AppColors.textPrimary)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
                .background(selection.wrappedValue == value ? AppColors.primary : AppColors.surfaceElevated)
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        }
        .buttonStyle(.plain)
    }
}

private extension String {
    var nilIfEmpty: String? {
        isEmpty ? nil : self
    }
}

#if DEBUG
struct CompleteWorkoutView_Previews: PreviewProvider {
    static var previews: some View {
        CompleteWorkoutView(
            isLoading: false,
            statusMessage: nil,
            metricsNote: "Health metrics were not available."
        ) { _, _, _ in }
            .preferredColorScheme(.dark)
    }
}
#endif
