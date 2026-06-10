import SwiftUI

struct ProgramWeekView: View {
    let programId: String
    let weekNumber: Int
    let phase: String?
    let workouts: [ProgramCalendarDay]
    
    let programRepository: ProgramRepositoryProtocol
    let workoutRepository: WorkoutRepository
    let workoutMetricsReader: HealthKitWorkoutMetricsReader?
    let initialEquipment: [String]
    let generationMode: String
    
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var selectedWorkout: WorkoutPlanResponse?
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                if let phase = phase {
                    AppCard {
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text("Week \(weekNumber)")
                                    .font(AppTypography.caption.weight(.semibold))
                                    .foregroundStyle(AppColors.textSecondary)
                                Spacer()
                                ProgramPhaseBadge(phase: phase)
                            }
                            
                            Text(phaseTitle(phase))
                                .font(AppTypography.title)
                            
                            Text(phaseExplanation(phase))
                                .font(AppTypography.body)
                                .foregroundStyle(AppColors.textSecondary)
                        }
                    }
                }
                
                VStack(alignment: .leading, spacing: 12) {
                    Text("Workouts")
                        .font(AppTypography.title)
                        .padding(.horizontal, 4)
                    
                    ForEach(workouts) { workout in
                        ProgramWorkoutRowView(workout: workout) {
                            if let planId = workout.plannedWorkoutPlanId {
                                Task { await fetchAndOpenWorkout(planId) }
                            } else {
                                errorMessage = "Workout not generated yet."
                            }
                        }
                    }
                }
                
                if isLoading {
                    HStack {
                        Spacer()
                        ProgressView("Loading planned workout...")
                        Spacer()
                    }
                    .padding()
                }
                
                if let errorMessage = errorMessage {
                    Text(errorMessage)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.danger)
                        .padding(.horizontal)
                }
            }
            .padding(24)
        }
        .background(AppColors.background.ignoresSafeArea())
        .navigationTitle("Week \(weekNumber)")
        .navigationBarTitleDisplayMode(.inline)
        .navigationDestination(item: $selectedWorkout) { workout in
            WorkoutPreviewView(
                workout: workout,
                workoutRepository: workoutRepository,
                workoutDate: workout.targetDate ?? ISO8601DateFormatter.smartFitDate.string(from: Date()),
                readiness: nil,
                initialEquipment: initialEquipment,
                initialWorkoutSplit: workout.focusMuscle ?? "full_body",
                initialFocusMuscle: workout.focusMuscle,
                initialAvailableTimeMinutes: workout.estimatedDurationMinutes ?? 60,
                initialGenerationMode: generationMode,
                initialAvoidExercisesText: "",
                initialUserNote: "",
                allowsRegeneration: false,
                workoutMetricsReader: workoutMetricsReader
            )
        }
    }
    
    private func fetchAndOpenWorkout(_ workoutId: String) async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        
        do {
            let plan = try await programRepository.getWorkoutDetail(workoutId: workoutId)
            selectedWorkout = plan
        } catch {
            errorMessage = "Unable to load planned workout details."
        }
    }
    
    private func phaseTitle(_ phase: String) -> String {
        switch phase.lowercased() {
        case "foundation": return "Foundation Phase"
        case "accumulation": return "Accumulation Phase"
        case "intensification": return "Intensification Phase"
        case "deload": return "Deload Week"
        case "consolidation": return "Consolidation Phase"
        default: return phase.capitalized
        }
    }
    
    private func phaseExplanation(_ phase: String) -> String {
        switch phase.lowercased() {
        case "foundation":
            return "Focus on building movement quality and consistent habits. Volume and intensity are moderate."
        case "accumulation":
            return "Gradually step up weekly work volume and intensity to accumulate training fatigue."
        case "intensification":
            return "Shift toward heavier lifting and higher relative RPEs to peak strength."
        case "deload":
            return "Reduce sets and load by 30-50% to dump accumulated fatigue and allow supercompensation."
        case "consolidation":
            return "Lock in your new performance baselines and test your maximum capabilities."
        default:
            return "Follow your structured training progression."
        }
    }
}

private extension WorkoutPlanResponse {
    var targetDate: String? {
        // Simple extraction since target_date isn't directly exposed or might be in a different field
        nil
    }
}
