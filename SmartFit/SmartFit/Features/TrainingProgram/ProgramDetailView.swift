import SwiftUI

struct ProgramDetailView: View {
    let program: ActiveProgramResponse
    let todayWorkout: TodayProgramWorkoutResponse?
    let readiness: ReadinessResponse?
    let equipment: [String]
    let programRepository: ProgramRepositoryProtocol
    let workoutRepository: WorkoutRepository
    let workoutMetricsReader: HealthKitWorkoutMetricsReader?

    @State private var calendarDays: [ProgramCalendarDay] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    
    @State private var selectedDayForSheet: ProgramCalendarDay?
    @State private var selectedWorkoutForNavigation: WorkoutPlanResponse?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                summaryCard

                if !program.focusAreas.isEmpty {
                    AppCard {
                        VStack(alignment: .leading, spacing: 10) {
                            Text("Program Focus")
                                .font(AppTypography.title)
                            Text(program.focusAreas.map(\.programDisplayName).joined(separator: " · "))
                                .font(AppTypography.body)
                                .foregroundStyle(AppColors.textSecondary)
                        }
                    }
                }

                VStack(alignment: .leading, spacing: 12) {
                    Text("Calendar Schedule")
                        .font(AppTypography.title)
                        .padding(.horizontal, 4)

                    if isLoading && calendarDays.isEmpty {
                        HStack {
                            Spacer()
                            ProgressView("Loading calendar...")
                            Spacer()
                        }
                        .padding()
                    } else {
                        ForEach(groupedWeeks.keys.sorted(), id: \.self) { weekNum in
                            VStack(alignment: .leading, spacing: 12) {
                                Text("Week \(weekNum) · \(phaseForWeek(weekNum).programDisplayName)")
                                    .font(AppTypography.headline.weight(.semibold))
                                    .foregroundStyle(AppColors.textSecondary)
                                    .padding(.horizontal, 4)
                                
                                ForEach(groupedWeeks[weekNum] ?? []) { day in
                                    ProgramWorkoutRowView(workout: day) {
                                        selectedDayForSheet = day
                                    }
                                }
                            }
                            .padding(.bottom, 10)
                        }
                    }
                }
            }
            .padding(24)
        }
        .background(AppColors.background.ignoresSafeArea())
        .navigationTitle("Program Details")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await loadCalendar()
        }
        .sheet(item: $selectedDayForSheet) { day in
            WorkoutActionSheetView(
                day: day,
                onOpen: {
                    if let planId = day.plannedWorkoutPlanId {
                        Task { await fetchWorkoutDetails(planId) }
                    }
                },
                onSkip: {
                    if let instanceId = day.instanceId {
                        Task { await skipWorkout(instanceId) }
                    }
                },
                onReschedule: { newDate in
                    if let instanceId = day.instanceId {
                        Task { await rescheduleWorkout(instanceId, newDate: newDate) }
                    }
                }
            )
            .presentationDetents([.medium, .large])
        }
        .navigationDestination(item: $selectedWorkoutForNavigation) { workout in
            WorkoutPreviewView(
                workout: workout,
                workoutRepository: workoutRepository,
                workoutDate: ISO8601DateFormatter.smartFitDate.string(from: Date()),
                readiness: nil,
                initialEquipment: equipment,
                initialWorkoutSplit: workout.focusMuscle ?? "full_body",
                initialFocusMuscle: workout.focusMuscle,
                initialAvailableTimeMinutes: workout.estimatedDurationMinutes ?? 60,
                initialGenerationMode: program.generationMode,
                initialAvoidExercisesText: "",
                initialUserNote: "",
                allowsRegeneration: false,
                workoutMetricsReader: workoutMetricsReader
            )
        }
    }

    private var summaryCard: some View {
        AppCard(cornerRadius: 24, padding: 22) {
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    VStack(alignment: .leading, spacing: 5) {
                        Text(program.name)
                            .font(AppTypography.hero)
                        Text(
                            "\(program.goal.programDisplayName) · "
                                + "\(program.trainingLevel.programDisplayName)"
                        )
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                    }
                    Spacer()
                    StatusBadge(title: program.status.programDisplayName)
                }

                ProgressView(value: program.progress)
                    .tint(AppColors.primary)

                HStack {
                    metric("Week", "\(program.currentWeek)/\(program.durationWeeks)")
                    metric("Completed", "\(program.completedWorkoutsCount)/\(program.totalScheduledWorkouts)")
                    metric("Session", "\(program.sessionDurationMinutes)m")
                }
            }
        }
    }

    private func metric(_ title: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(AppTypography.caption)
                .foregroundStyle(AppColors.textSecondary)
            Text(value)
                .font(AppTypography.body.weight(.semibold))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
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

    private func fetchWorkoutDetails(_ planId: String) async {
        guard !isLoading else { return }
        isLoading = true
        defer { isLoading = false }

        do {
            let details = try await programRepository.getWorkoutDetail(workoutId: planId)
            selectedWorkoutForNavigation = details
        } catch {
            if error.isCancellation { return }
            errorMessage = "Unable to load workout details."
        }
    }

    private func skipWorkout(_ instanceId: String) async {
        guard !isLoading else { return }
        isLoading = true
        defer { isLoading = false }

        do {
            try await programRepository.skipProgramWorkout(instanceId: instanceId)
            await loadCalendar()
        } catch {
            if error.isCancellation { return }
            errorMessage = "Unable to skip workout."
        }
    }

    private func rescheduleWorkout(_ instanceId: String, newDate: Date) async {
        guard !isLoading else { return }
        isLoading = true
        let dateString = ISO8601DateFormatter.smartFitDate.string(from: newDate)
        defer { isLoading = false }

        do {
            try await programRepository.rescheduleProgramWorkout(instanceId: instanceId, newDate: dateString)
            await loadCalendar()
        } catch {
            if error.isCancellation { return }
            errorMessage = "Unable to reschedule workout."
        }
    }
}

struct WorkoutActionSheetView: View {
    let day: ProgramCalendarDay
    let onOpen: () -> Void
    let onSkip: () -> Void
    let onReschedule: (Date) -> Void
    @Environment(\.dismiss) private var dismiss
    
    @State private var selectedDate = Date()
    @State private var isRescheduling = false

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Week \(day.weekNumber) · Day \(day.dayIndex + 1)")
                        .font(AppTypography.caption.weight(.semibold))
                        .foregroundStyle(AppColors.primary)
                    Text(day.title)
                        .font(AppTypography.title)
                }
                Spacer()
                if let phase = day.phase {
                    ProgramPhaseBadge(phase: phase)
                }
            }
            
            Divider().overlay(AppColors.border)
            
            VStack(alignment: .leading, spacing: 8) {
                Text("STATUS")
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.textSecondary)
                StatusBadge(title: day.status.programDisplayName)
            }
            
            if !["completed", "skipped"].contains(day.status.lowercased()) {
                VStack(spacing: 12) {
                    if day.plannedWorkoutPlanId != nil {
                        PrimaryButton(title: "View Planned Workout", systemImage: "eye.fill") {
                            onOpen()
                            dismiss()
                        }
                    }
                    
                    Button(action: {
                        onSkip()
                        dismiss()
                    }) {
                        Label("Skip Workout", systemImage: "xmark.circle")
                            .font(AppTypography.body.weight(.semibold))
                            .foregroundStyle(AppColors.danger)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 14)
                            .background(AppColors.surfaceMuted)
                            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                    }
                    .buttonStyle(.plain)
                    
                    if isRescheduling {
                        VStack(spacing: 10) {
                            DatePicker(
                                "New Date",
                                selection: $selectedDate,
                                displayedComponents: .date
                            )
                            .datePickerStyle(.graphical)
                            .background(AppColors.surfaceElevated)
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                            
                            HStack(spacing: 12) {
                                SecondaryButton(title: "Cancel") {
                                    isRescheduling = false
                                }
                                PrimaryButton(title: "Confirm") {
                                    onReschedule(selectedDate)
                                    dismiss()
                                }
                            }
                        }
                        .transition(.slide)
                    } else {
                        Button(action: {
                            withAnimation {
                                isRescheduling = true
                            }
                        }) {
                            Label("Reschedule Workout", systemImage: "calendar")
                                .font(AppTypography.body.weight(.semibold))
                                .foregroundStyle(AppColors.textPrimary)
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 14)
                                .background(AppColors.surfaceMuted)
                                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(.top, 10)
            } else if day.plannedWorkoutPlanId != nil {
                PrimaryButton(title: "View Workout Details", systemImage: "eye.fill") {
                    onOpen()
                    dismiss()
                }
            }
        }
        .padding(24)
        .background(AppColors.background.ignoresSafeArea())
        .onAppear {
            let formatter = ISO8601DateFormatter.smartFitDate
            if let date = formatter.date(from: day.date) {
                selectedDate = date
            }
        }
    }
}
