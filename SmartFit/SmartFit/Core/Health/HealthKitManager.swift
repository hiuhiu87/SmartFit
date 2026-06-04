import Foundation
import HealthKit

enum HealthKitError: LocalizedError {
    case unavailable
    case authorizationDenied
    case noData

    var errorDescription: String? {
        switch self {
        case .unavailable:
            return "Apple Health is not available on this device."
        case .authorizationDenied:
            return "Apple Health permission was denied."
        case .noData:
            return "Not enough Apple Health data is available yet."
        }
    }
}

final class HealthKitManager {
    private let store = HKHealthStore()

    func isHealthDataAvailable() -> Bool {
        HKHealthStore.isHealthDataAvailable()
    }

    func currentPermissionState() -> HealthPermissionState {
        guard isHealthDataAvailable() else { return .unavailable }
        guard let sleepType = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) else {
            return .unavailable
        }
        switch store.authorizationStatus(for: sleepType) {
        case .notDetermined:
            return .notDetermined
        case .sharingDenied:
            return .denied
        case .sharingAuthorized:
            return .authorized
        @unknown default:
            return .notDetermined
        }
    }

    func requestAuthorization() async throws {
        guard isHealthDataAvailable() else {
            throw HealthKitError.unavailable
        }

        let sleep = HKObjectType.categoryType(forIdentifier: .sleepAnalysis)
        let hrv = HKObjectType.quantityType(forIdentifier: .heartRateVariabilitySDNN)
        let heartRate = HKObjectType.quantityType(forIdentifier: .heartRate)
        let restingHeartRate = HKObjectType.quantityType(forIdentifier: .restingHeartRate)
        let activeEnergy = HKObjectType.quantityType(forIdentifier: .activeEnergyBurned)
        let steps = HKObjectType.quantityType(forIdentifier: .stepCount)
        let workouts = HKObjectType.workoutType()

        let readTypes = Set([sleep, hrv, heartRate, restingHeartRate, activeEnergy, steps, workouts].compactMap { $0 })
        try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
            store.requestAuthorization(toShare: [], read: readTypes) { success, error in
                if let error {
                    continuation.resume(throwing: error)
                } else if success {
                    continuation.resume()
                } else {
                    continuation.resume(throwing: HealthKitError.authorizationDenied)
                }
            }
        }
    }

    func fetchDailyHealthSummary(for date: Date) async throws -> HealthSummaryDraft {
        guard isHealthDataAvailable() else {
            throw HealthKitError.unavailable
        }

        async let sleepHours = fetchSleepHours(for: date)
        async let deepSleepHours = fetchDeepSleepHours(for: date)
        async let hrv = fetchLatestQuantityAverage(
            identifier: .heartRateVariabilitySDNN,
            unit: HKUnit.secondUnit(with: .milli),
            startDate: Calendar.current.date(byAdding: .day, value: -2, to: date) ?? date,
            endDate: date
        )
        async let restingHeartRate = fetchLatestQuantityAverage(
            identifier: .restingHeartRate,
            unit: HKUnit.count().unitDivided(by: .minute()),
            startDate: Calendar.current.date(byAdding: .day, value: -2, to: date) ?? date,
            endDate: date
        )
        async let activeEnergy = fetchQuantitySum(
            identifier: .activeEnergyBurned,
            unit: .kilocalorie(),
            startDate: Calendar.current.startOfDay(for: date),
            endDate: Calendar.current.date(byAdding: .day, value: 1, to: Calendar.current.startOfDay(for: date)) ?? date
        )
        async let steps = fetchQuantitySum(
            identifier: .stepCount,
            unit: .count(),
            startDate: Calendar.current.startOfDay(for: date),
            endDate: Calendar.current.date(byAdding: .day, value: 1, to: Calendar.current.startOfDay(for: date)) ?? date
        )
        async let workoutMinutes = fetchWorkoutMinutesYesterday(for: date)

        let summary = HealthSummaryDraft(
            date: date,
            sleepHours: try await sleepHours,
            deepSleepHours: try await deepSleepHours,
            hrvMS: try await hrv,
            restingHeartRate: try await restingHeartRate,
            activeEnergyBurned: try await activeEnergy,
            steps: Int((try await steps) ?? 0),
            workoutMinutesYesterday: try await workoutMinutes
        )

        if summary.sleepHours == nil &&
            summary.hrvMS == nil &&
            summary.restingHeartRate == nil &&
            summary.activeEnergyBurned == nil &&
            summary.steps == nil {
            throw HealthKitError.noData
        }

        return summary
    }

    private func fetchSleepHours(for date: Date) async throws -> Double? {
        guard let sleepType = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) else { return nil }
        let calendar = Calendar.current
        let dayStart = calendar.startOfDay(for: date)
        let previousDay = calendar.date(byAdding: .day, value: -1, to: dayStart) ?? dayStart
        let morning = calendar.date(byAdding: .hour, value: 12, to: dayStart) ?? dayStart
        let predicate = HKQuery.predicateForSamples(withStart: previousDay, end: morning, options: .strictEndDate)

        return try await withCheckedThrowingContinuation { continuation in
            let query = HKSampleQuery(sampleType: sleepType, predicate: predicate, limit: HKObjectQueryNoLimit, sortDescriptors: nil) { _, samples, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                let sleepSamples = (samples as? [HKCategorySample]) ?? []
                let totalSeconds = sleepSamples
                    .filter {
                        if #available(iOS 16.0, *) {
                            return $0.value == HKCategoryValueSleepAnalysis.asleepUnspecified.rawValue ||
                                $0.value == HKCategoryValueSleepAnalysis.asleepCore.rawValue ||
                                $0.value == HKCategoryValueSleepAnalysis.asleepDeep.rawValue ||
                                $0.value == HKCategoryValueSleepAnalysis.asleepREM.rawValue
                        } else {
                            return $0.value == HKCategoryValueSleepAnalysis.asleepUnspecified.rawValue
                        }
                    }
                    .reduce(0.0) { partial, sample in
                        partial + sample.endDate.timeIntervalSince(sample.startDate)
                    }
                continuation.resume(returning: totalSeconds > 0 ? totalSeconds / 3600 : nil)
            }
            store.execute(query)
        }
    }

    private func fetchDeepSleepHours(for date: Date) async throws -> Double? {
        guard #available(iOS 16.0, *),
              let sleepType = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) else {
            return nil
        }
        let calendar = Calendar.current
        let dayStart = calendar.startOfDay(for: date)
        let previousDay = calendar.date(byAdding: .day, value: -1, to: dayStart) ?? dayStart
        let morning = calendar.date(byAdding: .hour, value: 12, to: dayStart) ?? dayStart
        let predicate = HKQuery.predicateForSamples(withStart: previousDay, end: morning, options: .strictEndDate)

        return try await withCheckedThrowingContinuation { continuation in
            let query = HKSampleQuery(sampleType: sleepType, predicate: predicate, limit: HKObjectQueryNoLimit, sortDescriptors: nil) { _, samples, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                let sleepSamples = (samples as? [HKCategorySample]) ?? []
                let totalSeconds = sleepSamples
                    .filter { $0.value == HKCategoryValueSleepAnalysis.asleepDeep.rawValue }
                    .reduce(0.0) { partial, sample in
                        partial + sample.endDate.timeIntervalSince(sample.startDate)
                    }
                continuation.resume(returning: totalSeconds > 0 ? totalSeconds / 3600 : nil)
            }
            store.execute(query)
        }
    }

    private func fetchLatestQuantityAverage(
        identifier: HKQuantityTypeIdentifier,
        unit: HKUnit,
        startDate: Date,
        endDate: Date
    ) async throws -> Double? {
        guard let quantityType = HKObjectType.quantityType(forIdentifier: identifier) else { return nil }
        let predicate = HKQuery.predicateForSamples(withStart: startDate, end: endDate, options: .strictEndDate)

        return try await withCheckedThrowingContinuation { continuation in
            let query = HKStatisticsQuery(quantityType: quantityType, quantitySamplePredicate: predicate, options: .discreteAverage) { _, statistics, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                let value = statistics?.averageQuantity()?.doubleValue(for: unit)
                continuation.resume(returning: value)
            }
            store.execute(query)
        }
    }

    private func fetchQuantitySum(
        identifier: HKQuantityTypeIdentifier,
        unit: HKUnit,
        startDate: Date,
        endDate: Date
    ) async throws -> Double? {
        guard let quantityType = HKObjectType.quantityType(forIdentifier: identifier) else { return nil }
        let predicate = HKQuery.predicateForSamples(withStart: startDate, end: endDate, options: .strictEndDate)

        return try await withCheckedThrowingContinuation { continuation in
            let query = HKStatisticsQuery(quantityType: quantityType, quantitySamplePredicate: predicate, options: .cumulativeSum) { _, statistics, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                let value = statistics?.sumQuantity()?.doubleValue(for: unit)
                continuation.resume(returning: value)
            }
            store.execute(query)
        }
    }

    private func fetchWorkoutMinutesYesterday(for date: Date) async throws -> Int? {
        let calendar = Calendar.current
        let todayStart = calendar.startOfDay(for: date)
        let yesterdayStart = calendar.date(byAdding: .day, value: -1, to: todayStart) ?? todayStart
        let predicate = HKQuery.predicateForSamples(withStart: yesterdayStart, end: todayStart, options: .strictEndDate)

        return try await withCheckedThrowingContinuation { continuation in
            let query = HKSampleQuery(sampleType: HKObjectType.workoutType(), predicate: predicate, limit: HKObjectQueryNoLimit, sortDescriptors: nil) { _, samples, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                let workouts = (samples as? [HKWorkout]) ?? []
                let totalMinutes = workouts.reduce(0.0) { partial, workout in
                    partial + workout.duration / 60
                }
                continuation.resume(returning: totalMinutes > 0 ? Int(totalMinutes.rounded()) : nil)
            }
            store.execute(query)
        }
    }
}
