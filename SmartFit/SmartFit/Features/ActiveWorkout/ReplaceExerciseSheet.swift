import SwiftUI

struct ReplaceExerciseSheet: View {
    let currentExercise: WorkoutExerciseResponse
    @Binding var selectedReason: String
    @Binding var selectedEquipment: Set<String>
    @Binding var userNote: String
    let equipmentOptions: [String]
    let replacementOptions: [ReplacementOptionResponse]
    let safetyNote: String?
    let errorMessage: String?
    let isFindingReplacement: Bool
    let isApplyingReplacement: Bool
    let onFindReplacement: () -> Void
    let onApplyReplacement: (ReplacementOptionResponse) -> Void

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Replace Exercise")
                            .font(AppTypography.hero)
                        Text(currentExercise.name)
                            .font(AppTypography.body.weight(.semibold))
                            .foregroundStyle(AppColors.textSecondary)
                    }

                    ReplacementReasonPicker(selection: $selectedReason)

                    ReplacementEquipmentSelector(
                        selection: $selectedEquipment,
                        options: equipmentOptions
                    )

                    VStack(alignment: .leading, spacing: 10) {
                        Text("Note")
                            .font(AppTypography.title)
                        AppInputField {
                            TextEditor(text: $userNote)
                                .font(AppTypography.body)
                                .foregroundStyle(AppColors.textPrimary)
                                .frame(minHeight: 80)
                                .scrollContentBackground(.hidden)
                                .background(AppColors.surfaceElevated)
                        }
                    }

                    PrimaryButton(
                        title: replacementOptions.isEmpty ? "Find Replacement" : "Find Again",
                        isLoading: isFindingReplacement,
                        action: onFindReplacement
                    )

                    if let errorMessage, !errorMessage.isEmpty {
                        Text(errorMessage)
                            .font(AppTypography.body)
                            .foregroundStyle(AppColors.error)
                            .padding(14)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(AppColors.error.opacity(0.12))
                            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                    }

                    if let safetyNote, !safetyNote.isEmpty {
                        Text(safetyNote)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.warning)
                            .padding(14)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(AppColors.warning.opacity(0.12))
                            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                    }

                    replacementOptionsSection
                }
                .padding(24)
            }
            .background(AppColors.background.ignoresSafeArea())
            .navigationTitle("Replacement")
            .navigationBarTitleDisplayMode(.inline)
        }
    }

    @ViewBuilder
    private var replacementOptionsSection: some View {
        if isFindingReplacement {
            AppCard(cornerRadius: 18, padding: 16) {
                HStack(spacing: 12) {
                    ProgressView()
                        .tint(AppColors.primary)
                    Text("Finding replacement options...")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.textSecondary)
                }
            }
        } else if !replacementOptions.isEmpty {
            VStack(alignment: .leading, spacing: 12) {
                Text("Options")
                    .font(AppTypography.title)

                ForEach(replacementOptions) { option in
                    ReplacementOptionCard(
                        option: option,
                        isApplying: isApplyingReplacement,
                        onUse: { onApplyReplacement(option) }
                    )
                }
            }
        }
    }
}

#if DEBUG
struct ReplaceExerciseSheet_Previews: PreviewProvider {
    struct InitialPreview: View {
        @State private var reason = "equipment_unavailable"
        @State private var equipment: Set<String> = ["bodyweight"]
        @State private var note = ""

        var body: some View {
            ReplaceExerciseSheet(
                currentExercise: WorkoutPlanResponse.mockAI.exercises[0],
                selectedReason: $reason,
                selectedEquipment: $equipment,
                userNote: $note,
                equipmentOptions: ["dumbbell", "barbell", "bench", "cable_machine", "machine", "smith_machine", "pull_up_bar", "resistance_band", "treadmill", "bodyweight"],
                replacementOptions: [],
                safetyNote: nil,
                errorMessage: nil,
                isFindingReplacement: false,
                isApplyingReplacement: false,
                onFindReplacement: {},
                onApplyReplacement: { _ in }
            )
        }
    }

    struct OptionsPreview: View {
        @State private var reason = "too_hard"
        @State private var equipment: Set<String> = ["bodyweight", "cable_machine"]
        @State private var note = "Shoulders feel tired."

        var body: some View {
            ReplaceExerciseSheet(
                currentExercise: WorkoutPlanResponse.mockAI.exercises[0],
                selectedReason: $reason,
                selectedEquipment: $equipment,
                userNote: $note,
                equipmentOptions: ["dumbbell", "barbell", "bench", "cable_machine", "machine", "smith_machine", "pull_up_bar", "resistance_band", "treadmill", "bodyweight"],
                replacementOptions: [.mockPushUp, .mockCablePress],
                safetyNote: "Choose a pain-free range of motion.",
                errorMessage: nil,
                isFindingReplacement: false,
                isApplyingReplacement: false,
                onFindReplacement: {},
                onApplyReplacement: { _ in }
            )
        }
    }

    static var previews: some View {
        InitialPreview()
            .preferredColorScheme(.dark)
        OptionsPreview()
            .preferredColorScheme(.dark)
    }
}
#endif
