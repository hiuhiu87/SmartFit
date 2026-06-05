import SwiftUI

struct TodayView: View {
    @EnvironmentObject private var appState: AppState
    @StateObject private var viewModel = TodayViewModel()

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.isLoading && viewModel.readiness == nil && viewModel.activeProgram == nil {
                    LoadingView(message: "Loading today...")
                } else {
                    ScrollView {
                        VStack(spacing: 20) {
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
                                    onConnect: { Task { await viewModel.connectHealthKit() } },
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
                        .padding(24)
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
                    initialWorkoutSplit: viewModel.todayProgramWorkout?.template?.workoutType ?? "full_body",
                    initialFocusMuscle: viewModel.todayProgramWorkout?.template?.focusType,
                    initialAvailableTimeMinutes: viewModel.todayProgramWorkout?.template?.estimatedDurationMinutes
                        ?? viewModel.activeProgram?.sessionDurationMinutes
                        ?? 60,
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
                        .padding(.horizontal, 16)
                        .padding(.vertical, 12)
                        .background(AppColors.error)
                        .clipShape(Capsule())
                        .padding(.bottom, 16)
                }
            }
        }
    }

    @ViewBuilder
    private var programSection: some View {
        if let program = viewModel.activeProgram {
            ActiveProgramCard(
                program: program,
                todayWorkout: viewModel.todayProgramWorkout,
                isGenerating: viewModel.isGeneratingProgramWorkout,
                onOpenProgram: { viewModel.navigateToProgramDetail = true },
                onGenerateWorkout: {
                    Task { await viewModel.openOrGenerateProgramWorkout() }
                }
            )
        } else {
            AppCard(cornerRadius: 24, padding: 22) {
                VStack(alignment: .leading, spacing: 14) {
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
