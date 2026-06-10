import SwiftUI

struct TodayView: View {
    @EnvironmentObject private var appState: AppState
    @StateObject private var viewModel = TodayViewModel()
    
    @State private var showingReschedulePicker = false
    @State private var newScheduledDate = Date()

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.isLoading && viewModel.readiness == nil && viewModel.activeProgram == nil {
                    LoadingView(message: "Loading today...")
                } else {
                    ScrollView {
                        VStack(spacing: AppSpacing.xl) {
                            programSection

                            if let readiness = viewModel.readiness {
                                DailyReadinessCard(
                                    readiness: readiness,
                                    lastSyncDate: viewModel.lastSyncDate,
                                    onGenerateWorkout: { viewModel.navigateToWorkoutBuilder = true },
                                    onRefresh: { Task { await viewModel.syncHealthAndCalculateReadiness() } },
                                    showsGenerateWorkout: viewModel.activeProgram == nil
                                )
                                ReadinessFactorListView(readiness: readiness)
                            } else {
                                HealthKitPermissionView(
                                    permissionState: viewModel.healthPermissionState,
                                    isSyncing: viewModel.isSyncingHealth,
                                    includeSleepData: $viewModel.includeSleepHealthData,
                                    onConnect: { Task { await viewModel.connectHealthKit(includeSleep: viewModel.includeSleepHealthData) } },
                                    onManualCheckIn: { viewModel.showManualCheckIn = true }
                                )
                                if viewModel.showManualCheckIn {
                                    ManualCheckInView(
                                        isSubmitting: viewModel.isSyncingHealth,
                                        onSubmit: { submission in
                                            Task { await viewModel.submitManualCheckIn(submission) }
                                        }
                                    )
                                }
                            }
                        }
                        .padding(AppSpacing.xxl)
                    }
                    .refreshable { await viewModel.refresh() }
                }
            }
            .background(AppColors.background.ignoresSafeArea())
            .navigationTitle("Today")
            .navigationDestination(isPresented: $viewModel.navigateToWorkoutBuilder) {
                GenerateWorkoutView(
                    workoutDate: viewModel.workoutDate,
                    readiness: viewModel.readiness,
                    initialEquipment: appState.currentUser?.equipmentTypes ?? [],
                    workoutRepository: appState.environment.workoutRepository,
                    workoutMetricsReader: appState.environment.healthKitWorkoutMetricsReader
                )
            }
            .navigationDestination(isPresented: $viewModel.navigateToCreateProgram) {
                CreateProgramView(
                    repository: appState.environment.programRepository,
                    equipment: appState.currentUser?.equipmentTypes ?? [],
                    onCreated: viewModel.programCreated
                )
            }
            .navigationDestination(isPresented: $viewModel.navigateToProgramDetail) {
                if let program = viewModel.activeProgram {
                    ProgramDetailView(
                        program: program,
                        todayWorkout: viewModel.todayProgramWorkout,
                        readiness: viewModel.readiness,
                        equipment: appState.currentUser?.equipmentTypes ?? [],
                        programRepository: appState.environment.programRepository,
                        workoutRepository: appState.environment.workoutRepository,
                        workoutMetricsReader: appState.environment.healthKitWorkoutMetricsReader
                    )
                }
            }
            .navigationDestination(item: $viewModel.generatedProgramWorkout) { workout in
                WorkoutPreviewView(
                    workout: workout,
                    workoutRepository: appState.environment.workoutRepository,
                    workoutDate: viewModel.workoutDate,
                    readiness: viewModel.readiness,
                    initialEquipment: appState.currentUser?.equipmentTypes ?? [],
                    initialWorkoutSplit: viewModel.todayProgramWorkout?.scheduledWorkout?.focusType ?? "full_body",
                    initialFocusMuscle: viewModel.todayProgramWorkout?.scheduledWorkout?.focusType,
                    initialAvailableTimeMinutes: viewModel.activeProgram?.sessionDurationMinutes ?? 60,
                    initialGenerationMode: viewModel.activeProgram?.generationMode ?? "auto",
                    initialAvoidExercisesText: "",
                    initialUserNote: "",
                    allowsRegeneration: false,
                    workoutMetricsReader: appState.environment.healthKitWorkoutMetricsReader
                )
            }
            .task {
                viewModel.configure(appState: appState)
                await viewModel.onAppear()
            }
            .overlay(alignment: .bottom) {
                if let errorMessage = viewModel.errorMessage {
                    Text(errorMessage)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textPrimary)
                        .padding(.horizontal, AppSpacing.lg)
                        .padding(.vertical, AppSpacing.md)
                        .background(AppColors.error)
                        .clipShape(Capsule())
                        .padding(.bottom, AppSpacing.lg)
                }
            }
            .sheet(isPresented: $showingReschedulePicker) {
                VStack(spacing: AppSpacing.xl) {
                    Text("Reschedule Today's Workout")
                        .font(AppTypography.title)
                    DatePicker("Select Date", selection: $newScheduledDate, displayedComponents: .date)
                        .datePickerStyle(.graphical)
                        .background(AppColors.surfaceElevated)
                        .clipShape(RoundedRectangle(cornerRadius: AppRadius.input, style: .continuous))
                    
                    PrimaryButton(title: "Confirm Reschedule") {
                        Task {
                            await viewModel.rescheduleTodayWorkout(to: newScheduledDate)
                            showingReschedulePicker = false
                        }
                    }
                    SecondaryButton(title: "Cancel") {
                        showingReschedulePicker = false
                    }
                }
                .padding(AppSpacing.xxl)
                .background(AppColors.background.ignoresSafeArea())
                .presentationDetents([.medium, .large])
            }
        }
    }

    @ViewBuilder
    private var programSection: some View {
        if let program = viewModel.activeProgram, let todayWorkout = viewModel.todayProgramWorkout {
            TodayProgramWorkoutCard(
                program: program,
                todayWorkout: todayWorkout,
                onOpenWorkout: {
                    Task { await viewModel.openTodayWorkout() }
                },
                onAdjustWorkout: {
                    Task { await viewModel.adjustTodayWorkout() }
                },
                onSkip: {
                    Task { await viewModel.skipTodayWorkout() }
                },
                onReschedule: {
                    showingReschedulePicker = true
                }
            )
            .onTapGesture {
                // Navigate to details if tapped outside buttons
                viewModel.navigateToProgramDetail = true
            }
        } else {
            HeroCard {
                VStack(alignment: .leading, spacing: AppSpacing.md) {
                    Image(systemName: "calendar.badge.plus")
                        .font(.system(size: 28, weight: .semibold))
                        .foregroundStyle(AppColors.primary)
                    Text("Train with a real plan")
                        .font(AppTypography.title)
                    Text("Create a multi-week program with structured weekly workouts and readiness-based adjustments.")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.textSecondary)
                    PrimaryButton(
                        title: "Create Training Program",
                        systemImage: "plus"
                    ) {
                        viewModel.navigateToCreateProgram = true
                    }
                }
            }
        }
    }
}

struct TodayView_Previews: PreviewProvider {
    static var previews: some View {
        TodayView()
            .environmentObject(AppState(environment: AppEnvironment.bootstrap()))
            .preferredColorScheme(.dark)
            .previewDisplayName("Today Reference")
    }
}
