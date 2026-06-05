import Foundation

struct AppEnvironment {
    let baseURLStore: BaseURLStore
    let tokenStore: TokenStore
    let apiClient: APIClient
    let authRepository: AuthRepository
    let onboardingRepository: OnboardingRepository
    let healthRepository: HealthRepository
    let readinessRepository: ReadinessRepository
    let workoutRepository: WorkoutRepository
    let programRepository: ProgramRepository
    let aiChatRepository: AIChatRepository
    let historyRepository: HistoryRepository
    let progressRepository: ProgressRepository
    let healthKitManager: HealthKitManager
    let healthKitWorkoutMetricsReader: HealthKitWorkoutMetricsReader
    let healthSummaryBuilder: HealthSummaryBuilder

    var baseURL: URL {
        baseURLStore.currentURL
    }

    static func bootstrap() -> AppEnvironment {
        let defaultBaseURL = resolvedBaseURL()
        let baseURLStore = BaseURLStore(defaultBaseURL: defaultBaseURL)
        let keychainService = KeychainService()
        let tokenStore = TokenStore(keychain: keychainService)
        let authInterceptor = AuthInterceptor(tokenStore: tokenStore)
        let apiClient = APIClient(
            baseURLStore: baseURLStore,
            authInterceptor: authInterceptor,
            tokenStore: tokenStore
        )
        let authRepository = AuthRepository(apiClient: apiClient, tokenStore: tokenStore)
        let onboardingRepository = OnboardingRepository(apiClient: apiClient)
        let healthRepository = HealthRepository(apiClient: apiClient)
        let readinessRepository = ReadinessRepository(apiClient: apiClient)
        let workoutRepository = WorkoutRepository(apiClient: apiClient)
        let programRepository = ProgramRepository(apiClient: apiClient)
        let aiChatRepository = AIChatRepository(apiClient: apiClient)
        let historyRepository = HistoryRepository(apiClient: apiClient)
        let progressRepository = ProgressRepository(apiClient: apiClient)
        let healthKitManager = HealthKitManager()
        let healthKitWorkoutMetricsReader = HealthKitWorkoutMetricsReader()
        let healthSummaryBuilder = HealthSummaryBuilder()
        return AppEnvironment(
            baseURLStore: baseURLStore,
            tokenStore: tokenStore,
            apiClient: apiClient,
            authRepository: authRepository,
            onboardingRepository: onboardingRepository,
            healthRepository: healthRepository,
            readinessRepository: readinessRepository,
            workoutRepository: workoutRepository,
            programRepository: programRepository,
            aiChatRepository: aiChatRepository,
            historyRepository: historyRepository,
            progressRepository: progressRepository,
            healthKitManager: healthKitManager,
            healthKitWorkoutMetricsReader: healthKitWorkoutMetricsReader,
            healthSummaryBuilder: healthSummaryBuilder
        )
    }

    private static func resolvedBaseURL() -> URL {
        let fallbackURL = URL(string: "http://127.0.0.1:8000")!
        let bundle = Bundle.main
        let processEnvironment = ProcessInfo.processInfo.environment

        let explicitBaseURL = processEnvironment["SMARTFIT_BASE_URL"]
        let simulatorBaseURL = bundle.object(forInfoDictionaryKey: "SMARTFIT_SIMULATOR_BASE_URL") as? String
        let deviceBaseURL = bundle.object(forInfoDictionaryKey: "SMARTFIT_DEVICE_BASE_URL") as? String

        let rawBaseURL: String?
        #if targetEnvironment(simulator)
        rawBaseURL = explicitBaseURL ?? simulatorBaseURL
        #else
        rawBaseURL = explicitBaseURL ?? deviceBaseURL
        #endif

        guard
            let rawBaseURL,
            !rawBaseURL.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
            let baseURL = URL(string: rawBaseURL)
        else {
            #if DEBUG
            print("Using fallback SmartFit base URL: \(fallbackURL.absoluteString)")
            #endif
            return fallbackURL
        }

        #if DEBUG
        print("Using SmartFit base URL: \(baseURL.absoluteString)")
        #endif
        return baseURL
    }
}
