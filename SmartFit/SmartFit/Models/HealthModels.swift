import Foundation

struct HealthSummaryDraft: Equatable {
    let date: Date
    let sleepHours: Double?
    let deepSleepHours: Double?
    let hrvMS: Double?
    let restingHeartRate: Double?
    let activeEnergyBurned: Double?
    let steps: Int?
    let workoutMinutesYesterday: Int?
}

struct HealthSummaryRequest: Codable {
    let date: String
    let sleepHours: Double?
    let sleepEfficiency: Double?
    let restingHeartRate: Double?
    let heartRateVariability: Double?
    let steps: Int?
    let activeEnergyKcal: Double?

    enum CodingKeys: String, CodingKey {
        case date
        case sleepHours = "sleep_hours"
        case sleepEfficiency = "sleep_efficiency"
        case restingHeartRate = "resting_heart_rate"
        case heartRateVariability = "heart_rate_variability"
        case steps
        case activeEnergyKcal = "active_energy_kcal"
    }
}

struct ManualCheckInSubmission {
    let date: String
    let sleepHours: Double?
    let energyLevel: Int
    let stressLevel: Int
    let sorenessLevel: Int
    let painNote: String?
}

struct ManualCheckInRequest: Codable {
    let date: String
    let energy: Int
    let soreness: Int
    let stress: Int
    let motivation: Int
    let sleepQuality: Int
    let notes: String?

    enum CodingKeys: String, CodingKey {
        case date
        case energy
        case soreness
        case stress
        case motivation
        case sleepQuality = "sleep_quality"
        case notes
    }
}
