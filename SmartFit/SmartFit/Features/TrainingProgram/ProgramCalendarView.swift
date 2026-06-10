import SwiftUI

struct ProgramCalendarView: View {
    let programRepository: ProgramRepositoryProtocol
    let workoutRepository: WorkoutRepository
    let workoutMetricsReader: HealthKitWorkoutMetricsReader?
    let initialEquipment: [String]
    let generationMode: String

    @State private var calendarDays: [ProgramCalendarDay] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var selectedWorkout: WorkoutPlanResponse?

    var body: some View {
        Group {
            if isLoading && calendarDays.isEmpty {
                LoadingView(message: "Loading calendar...")
            } else if let errorMessage = errorMessage, calendarDays.isEmpty {
                ErrorStateView(message: errorMessage, retryTitle: "Retry") {
                    Task { await loadCalendar() }
                }
            } else {
                ScrollView {
                    VStack(alignment: .leading, spacing: 24) {
                        ForEach(groupedWeeks.keys.sorted(), id: \.self) { weekNum in
                            VStack(alignment: .leading, spacing: 12) {
                                Text("Week \(weekNum) · \(phaseForWeek(weekNum).programDisplayName)")
                                    .font(AppTypography.headline.weight(.semibold))
                                    .foregroundStyle(AppColors.textSecondary)
                                    .padding(.horizontal, 4)
                                
                                ForEach(groupedWeeks[weekNum] ?? []) { day in
                                    ProgramWorkoutRowView(workout: day) {
                                        if let planId = day.plannedWorkoutPlanId {
                                            Task { await fetchAndOpenWorkout(planId) }
                                        } else {
                                            self.errorMessage = "Workout not pre-generated yet."
                                        }
                                    }
                                }
                            }
                        }
                    }
                    .padding(24)
                }
                .refreshable {
                    await loadCalendar()
                }
            }
        }
        .background(AppColors.background.ignoresSafeArea())
        .navigationTitle("Program Calendar")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await loadCalendar()
        }
        .navigationDestination(item: $selectedWorkout) { workout in
            WorkoutPreviewView(
                workout: workout,
                workoutRepository: workoutRepository,
                workoutDate: ISO8601DateFormatter.smartFitDate.string(from: Date()),
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

    private var groupedWeeks: [Int: [ProgramCalendarDay]] {
        Dictionary(grouping: calendarDays, by: { $0.weekNumber })
    }

    private func phaseForWeek(_ weekNum: Int) -> String {
        calendarDays.first(where: { $0.weekNumber == weekNum })?.phase ?? "Training"
    }

    private func loadCalendar() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            calendarDays = try await programRepository.getProgramCalendar(fromDate: nil, toDate: nil)
        } catch {
            if error.isCancellation { return }
            errorMessage = "Unable to load program calendar."
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
            if error.isCancellation { return }
            errorMessage = "Unable to load planned workout details."
        }
    }
}
