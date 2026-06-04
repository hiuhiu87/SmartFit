import Foundation
import HealthKit

struct WorkoutHealthMetrics: Hashable {
    let activeEnergyBurned: Double?
    let avgHeartRate: Double?
    let maxHeartRate: Double?
    let minHeartRate: Double?

    var hasSendableMetrics: Bool {
        activeEnergyBurned != nil || avgHeartRate != nil
    }
}

final class HealthKitWorkoutMetricsReader {
    private let store: HKHealthStore

    init(store: HKHealthStore = HKHealthStore()) {
        self.store = store
    }

    func readMetrics(startDate: Date, endDate: Date) async throws -> WorkoutHealthMetrics {
        guard HKHealthStore.isHealthDataAvailable() else {
            throw HealthKitError.unavailable
        }
        guard endDate > startDate else {
            throw HealthKitError.noData
        }

        async let activeEnergy = fetchActiveEnergyBurned(
            startDate: startDate,
            endDate: endDate
        )
        async let heartRateSummary = fetchHeartRateSummary(
            startDate: startDate,
            endDate: endDate
        )

        let summary = try await heartRateSummary
        let metrics = WorkoutHealthMetrics(
            activeEnergyBurned: try await activeEnergy,
            avgHeartRate: summary.average,
            maxHeartRate: summary.maximum,
            minHeartRate: summary.minimum
        )

        if metrics.activeEnergyBurned == nil,
           metrics.avgHeartRate == nil,
           metrics.maxHeartRate == nil,
           metrics.minHeartRate == nil {
            throw HealthKitError.noData
        }

        return metrics
    }

    private func fetchActiveEnergyBurned(
        startDate: Date,
        endDate: Date
    ) async throws -> Double? {
        guard let quantityType = HKObjectType.quantityType(forIdentifier: .activeEnergyBurned) else {
            return nil
        }
        let predicate = HKQuery.predicateForSamples(
            withStart: startDate,
            end: endDate,
            options: .strictEndDate
        )

        return try await withCheckedThrowingContinuation { continuation in
            let query = HKStatisticsQuery(
                quantityType: quantityType,
                quantitySamplePredicate: predicate,
                options: .cumulativeSum
            ) { _, statistics, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                let value = statistics?.sumQuantity()?.doubleValue(for: .kilocalorie())
                continuation.resume(returning: value)
            }
            store.execute(query)
        }
    }

    private func fetchHeartRateSummary(
        startDate: Date,
        endDate: Date
    ) async throws -> HeartRateSummary {
        guard let quantityType = HKObjectType.quantityType(forIdentifier: .heartRate) else {
            return HeartRateSummary()
        }
        let predicate = HKQuery.predicateForSamples(
            withStart: startDate,
            end: endDate,
            options: .strictEndDate
        )
        let unit = HKUnit.count().unitDivided(by: .minute())

        return try await withCheckedThrowingContinuation { continuation in
            let query = HKStatisticsQuery(
                quantityType: quantityType,
                quantitySamplePredicate: predicate,
                options: [.discreteAverage, .discreteMax, .discreteMin]
            ) { _, statistics, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                continuation.resume(
                    returning: HeartRateSummary(
                        average: statistics?.averageQuantity()?.doubleValue(for: unit),
                        maximum: statistics?.maximumQuantity()?.doubleValue(for: unit),
                        minimum: statistics?.minimumQuantity()?.doubleValue(for: unit)
                    )
                )
            }
            store.execute(query)
        }
    }
}

private struct HeartRateSummary {
    let average: Double?
    let maximum: Double?
    let minimum: Double?

    init(average: Double? = nil, maximum: Double? = nil, minimum: Double? = nil) {
        self.average = average
        self.maximum = maximum
        self.minimum = minimum
    }
}
